import logging
logger = logging.getLogger("panwid.datable")
import urwid
import urwid_utils.palette
from ..listbox import ScrollingListBox
from orderedattrdict import AttrDict
from collections.abc import MutableMapping
import itertools
import copy
import traceback
import math
from dataclasses import *
import typing

try:
    import pydantic
    HAVE_PYDANTIC=True
except ImportError:
    HAVE_PYDANTIC=False

try:
    import pony.orm
    from pony.orm import db_session
    HAVE_PONY=True
except ImportError:
    HAVE_PONY=False


from .dataframe import *
from .rows import *
from .columns import *
from .common import *


DEFAULT_TABLE_DIVIDER = DataTableDivider(" ")

def intersperse_divider(columns, divider):
    for i, col in enumerate(columns):
        yield col
        if (not i == len(columns)-1
            and not (col.hide or (i < len(columns)-1 and columns[i+1].hide))):
            yield copy.copy(divider)

class DataTable(urwid.WidgetWrap, urwid.listbox.ListWalker):


    signals = ["select", "refresh", "focus", "blur", "end", "requery",
               "drag_start", "drag_continue", "drag_stop"]

    ATTR = "table"

    columns = []

    data = None

    limit = None
    index = "index"

    with_header = True
    with_footer = False
    with_scrollbar = False
    empty_message = "(no data)"
    row_height = None
    cell_selection = False

    sort_by = (None, None)
    query_sort = False
    sort_icons = True
    sort_refocus = False
    no_load_on_init = None

    divider = DEFAULT_TABLE_DIVIDER
    padding = DEFAULT_CELL_PADDING
    row_style = None

    detail_fn = None
    detail_selectable = False
    detail_replace = None
    detail_auto_open = False
    detail_hanging_indent = None

    ui_sort = True
    ui_resize = True
    row_attr_fn = lambda self, position, data, row: ""

    with_sidecar = False

    attr_map = {}
    focus_map = {}
    column_focus_map = {}
    highlight_map = {}
    highlight_focus_map = {}
    highlight_focus_map2 = {}

    def __init__(self,
                 columns=None,
                 data=None,
                 limit=None,
                 index=None,
                 with_header=None, with_footer=None, with_scrollbar=None,
                 empty_message=None,
                 row_height=None,
                 cell_selection=None,
                 sort_by=None, query_sort=None, sort_icons=None,
                 sort_refocus=None,
                 no_load_on_init=None,
                 divider=None, padding=None,
                 row_style=None,
                 detail_fn=None, detail_selectable=None, detail_replace=None,
                 detail_auto_open=None, detail_hanging_indent=None,
                 ui_sort=None,
                 ui_resize=None,
                 row_attr_fn=None,
                 with_sidecar=None):

        self._focus = 0
        self.page = 0
        if columns is not None:
            self._columns = columns
        else:
            self._columns = [copy.copy(c) for c in self.columns]

        if not self._columns:
            raise Exception("must define columns for data table")

        if index: self.index = index

        if not self.index in self.column_names:
            self._columns.insert(
                0,
                DataTableColumn(self.index, hide=True)
            )

        if data is not None:
            self.data = data

        if query_sort: self.query_sort = query_sort

        if sort_by:
            if isinstance(sort_by, tuple):
                column = sort_by[0]
                reverse = sort_by[1]
            else:
                column = sort_by
                reverse = None
                self.sort_by = (column, reverse)

            self.sort_by = (column, reverse)

        self.initial_sort = self.sort_by

        if sort_icons is not None: self.sort_icons = sort_icons
        if no_load_on_init is not None: self.no_load_on_init = no_load_on_init

        if with_header is not None: self.with_header = with_header
        if with_footer is not None: self.with_footer = with_footer
        if with_scrollbar is not None: self.with_scrollbar = with_scrollbar
        if empty_message is not None: self.empty_message = empty_message

        if row_height is not None: self.row_height = row_height

        if cell_selection is not None: self.cell_selection = cell_selection
        if divider is not None: self.divider = divider
        if isinstance(self.divider, str):
            self.divider = DataTableDivider(self.divider)
        if padding is not None: self.padding = padding

        if isinstance(self.padding, tuple):
            self.padding_left, self.padding_right = self.padding
        else:
            self.padding_left = self.padding_right = self.padding

        if row_style is not None: self.row_style = row_style

        if ui_sort is not None: self.ui_sort = ui_sort
        if ui_resize is not None: self.ui_resize = ui_resize

        if row_attr_fn is not None: self.row_attr_fn = row_attr_fn

        if detail_fn is not None: self.detail_fn = detail_fn
        if detail_selectable is not None: self.detail_selectable = detail_selectable
        if detail_replace is not None: self.detail_replace = detail_replace
        if detail_auto_open is not None: self.detail_auto_open = detail_auto_open
        if detail_hanging_indent is not None: self.detail_hanging_indent = detail_hanging_indent
        if detail_hanging_indent is not None: self.detail_hanging_indent = detail_hanging_indent
        if detail_hanging_indent is not None: self.detail_hanging_indent = detail_hanging_indent
        if detail_hanging_indent is not None: self.detail_hanging_indent = detail_hanging_indent

        if with_sidecar is not None: self.with_sidecar = with_sidecar

        if limit:
            self.limit = limit

        self.sort_column = None
        self._width = None
        self._height = None
        self._initialized = False
        self._message_showing = False
        self.pagination_cursor = None
        self.filters = None
        self.filtered_rows = list()

        if self.divider:
            self._columns = list(intersperse_divider(self._columns, self.divider))
            # self._columns = intersperse(self.divider, self._columns)

        # FIXME: pass reference
        for c in self._columns:
            c.table = self

        kwargs = dict(
            columns = self.column_names,
            sort=False,
            index_name = self.index or None
            # sorted=True,
        )

        self.df = DataTableDataFrame(
            columns = self.column_names,
            sort=False,
            index_name = self.index or None
        )
        self.pile = urwid.Pile([])
        self.listbox = ScrollingListBox(
            self, infinite=self.limit,
            with_scrollbar = self.with_scrollbar,
            row_count_fn = self.row_count
        )
        urwid.connect_signal(
            self.listbox, "drag_start",
            lambda source, drag_from: urwid.signals.emit_signal(
                self, "drag_start", self, drag_from)
        )
        urwid.connect_signal(
            self.listbox, "drag_continue",
            lambda source, drag_from, drag_to: urwid.signals.emit_signal(
                self, "drag_continue", self, drag_from, drag_to)
        )
        urwid.connect_signal(
            self.listbox, "drag_stop",
            lambda source, drag_from ,drag_to: urwid.signals.emit_signal(
                self, "drag_stop", self, drag_from, drag_to)
        )

        if self.limit:
            urwid.connect_signal(self.listbox, "load_more", self.load_more)
            # self.offset = 0

        self.header = DataTableHeaderRow(
            self,
            padding = self.padding,
            style = self.row_style,
            row_height=1 # FIXME
        )

        if self.with_header:
            self.pile.contents.insert(
                0,
                (
                    urwid.Columns([
                        ("weight", 1, self.header),
                        (1, urwid.Text(("table_row_header", " ")))
                    ]),
                    self.pile.options('pack')
                )
             )

            if self.ui_sort:
                urwid.connect_signal(
                    self.header, "column_click",
                    lambda index: self.sort_by_column(index, toggle=True)
                )

            if self.ui_resize:
                urwid.connect_signal(self.header, "drag", self.on_header_drag)

        self.listbox_placeholder = urwid.WidgetPlaceholder(self.listbox)
        self.pile.contents.append(
            (self.listbox_placeholder, self.pile.options('weight', 1))
         )
        self.pile.focus_position = len(self.pile.contents)-1

        self.footer = DataTableFooterRow(
            self,
            padding = self.padding,
            style = self.row_style,
            row_height=1
        )

        if self.with_footer:
            self.pile.contents.append(
                (self.footer, self.pile.options('pack'))
             )


        # if not self.no_load_on_init:
        #     self.reset()

            # if self.sort_by:
            #     self.sort_by_column(self.sort_by)


        self.attr = urwid.AttrMap(
            self.pile,
            attr_map = self.attr_map,
        )
        super(DataTable, self).__init__(self.attr)


    def query(self, sort=None, offset=None):
        raise Exception("query method must be overriden")

    def query_result_count(self):
        raise Exception("query_result_count method must be defined")

    @classmethod
    def get_palette_entries(
            cls,
            user_entries={},
            min_contrast_entries = None,
            min_contrast = 2.0,
            default_background="black"
    ):


        foreground_map = {
            "table_divider": [ "light gray", "light gray" ],
            "table_row_body": [ "light gray", "light gray" ],
            "table_row_header": [ "light gray", "white" ],
            "table_row_footer": [ "light gray", "white" ],
        }

        background_map = {
            None: [ "black", "black" ],
            "focused": [ "dark gray", "g15" ],
            "column_focused": [ "black", "#660" ],
            "highlight": ["light gray", "g15"],
            "highlight focused": ["light gray", "g23"],
            "highlight column_focused": ["light gray", "#660"],
        }

        entries = dict()

        row_attr = "table_row_body"
        for suffix in [None, "focused", "column_focused",
                       "highlight", "highlight focused",
                       "highlight column_focused",
        ]:
            if suffix:
                attr = ' '.join([row_attr, suffix])
            else:
                attr = row_attr
            entries[attr] = urwid_utils.palette.PaletteEntry(
                mono = "white",
                foreground = foreground_map[row_attr][0],
                background = background_map[suffix][0],
                foreground_high = foreground_map[row_attr][1],
                background_high = background_map[suffix][1],
            )

        header_foreground_map = {
            None: ["white,bold", "white,bold"],
            "focused": ["dark gray", "white,bold"],
            "column_focused": ["black", "black"],
            "highlight": ["yellow,bold", "yellow,bold"],
            "highlight focused": ["yellow", "yellow"],
            "highlight column_focused": ["yellow", "yellow"],
        }

        header_background_map = {
            None: ["light gray", "g23"],
            "focused": ["light gray", "g50"],
            "column_focused": ["white", "g70"],#"g23"],
            "highlight": ["light gray", "g38"],
            "highlight focused": ["light gray", "g50"],
            "highlight column_focused": ["white", "g70"],
        }

        for prefix in ["table_row_header", "table_row_footer"]:
            for suffix in [
                    None, "focused", "column_focused",
                    "highlight", "highlight focused",
                    "highlight column_focused"
            ]:
                if suffix:
                    attr = ' '.join([prefix, suffix])
                else:
                    attr = prefix
                entries[attr] = urwid_utils.palette.PaletteEntry(
                    mono = "white",
                    foreground = header_foreground_map[suffix][0],
                    background = header_background_map[suffix][0],
                    foreground_high = header_foreground_map[suffix][1],
                    background_high = header_background_map[suffix][1],
                )

        for name, entry in list(user_entries.items()):
            DataTable.focus_map[name] = "%s focused" %(name)
            DataTable.highlight_map[name] = "%s highlight" %(name)
            DataTable.column_focus_map["%s focused" %(name)] = "%s column_focused" %(name)
            DataTable.highlight_focus_map["%s highlight" %(name)] = "%s highlight focused" %(name)
            for suffix in [None, "focused", "column_focused",
                           "highlight", "highlight focused",
                           "highlight column_focused",
            ]:

                # Check entry backgroun colors against default bg.  If they're
                # the same, replace the entry's background color with focus or
                # highglight color.  If not, preserve the entry background.

                default_bg_rgb = urwid.AttrSpec(default_background, default_background, 16)
                bg_rgb = urwid.AttrSpec(entry.background, entry.background, 16)
                background = background_map[suffix][0]
                if default_bg_rgb.get_rgb_values() != bg_rgb.get_rgb_values():
                    background = entry.background

                background_high = background_map[suffix][1]
                if entry.background_high:
                    bg_high_rgb = urwid.AttrSpec(
                        entry.background_high,
                        entry.background_high,
                        (1<<24
                         if urwid_utils.palette.URWID_HAS_TRUE_COLOR
                         else 256
                        )
                    )
                    if default_bg_rgb.get_rgb_values() != bg_high_rgb.get_rgb_values():
                        background_high = entry.background_high

                foreground = entry.foreground
                background = background
                foreground_high = entry.foreground_high if entry.foreground_high else entry.foreground
                if min_contrast_entries and name in min_contrast_entries:
                    # All of this code is available in the colourettu package
                    # (https://github.com/MinchinWeb/colourettu) but newer
                    # versions don't run Python 3, and older versions don't work
                    # right.
                    def normalized_rgb(r, g, b):

                        r1 = r / 255
                        g1 = g / 255
                        b1 = b / 255

                        if r1 <= 0.03928:
                            r2 = r1 / 12.92
                        else:
                            r2 = math.pow(((r1 + 0.055) / 1.055), 2.4)
                        if g1 <= 0.03928:
                            g2 = g1 / 12.92
                        else:
                            g2 = math.pow(((g1 + 0.055) / 1.055), 2.4)
                        if b1 <= 0.03928:
                            b2 = b1 / 12.92
                        else:
                            b2 = math.pow(((b1 + 0.055) / 1.055), 2.4)

                        return (r2, g2, b2)

                    def luminance(r, g, b):

                        return math.sqrt(
                            0.299*math.pow(r, 2) +
                            0.587*math.pow(g, 2) +
                            0.114*math.pow(b, 2)
                        )

                    def contrast(c1, c2):

                        n1 = normalized_rgb(*c1)
                        n2 = normalized_rgb(*c2)
                        lum1 = luminance(*n1)
                        lum2 = luminance(*n2)
                        minlum = min(lum1, lum2)
                        maxlum = max(lum1, lum2)
                        return (maxlum + 0.05) / (minlum + 0.05)

                    table_bg = background_map[suffix][1]
                    attrspec_bg = urwid.AttrSpec(table_bg, table_bg, 256)
                    color_bg = attrspec_bg.get_rgb_values()[3:6]
                    attrspec_fg = urwid.AttrSpec(
                        foreground_high,
                        foreground_high,
                        256
                    )
                    color_fg = attrspec_fg.get_rgb_values()[0:3]
                    cfg = contrast(color_bg, color_fg)
                    cblack = contrast((0,0,0), color_fg)
                    # cwhite = contrast((255, 255, 255), color_fg)
                    # logger.debug("%s, %s, %s" %(cfg, cblack, cwhite))
                    # raise Exception("%s, %s, %s, %s, %s, %s" %(table_bg, color_fg, color_bg, cfg, cblack, cwhite))
                    if cfg < min_contrast and cfg < cblack:
                        # logger.debug("adjusting contrast of %s" %(name))
                        foreground_high = "black"
                        # if cblack > cwhite:
                        # else:
                        #     foreground_high = "white"

                if suffix:
                    attr = ' '.join([name, suffix])
                else:
                    attr = name

                # print foreground, foreground_high, background, background_high
                entries[attr] = urwid_utils.palette.PaletteEntry(
                    mono = "white",
                    foreground = foreground,
                    background = background,
                    foreground_high = foreground_high,
                    background_high = background_high,
                )

            entries["table_message"] = urwid_utils.palette.PaletteEntry(
                mono = "white",
                foreground = "black",
                background = "white",
                foreground_high = "black",
                background_high = "white",
            )

        # raise Exception(entries)
        return entries


    @property
    def focus(self): return self._focus

    def next_position(self, position):
        index = position + 1
        if index > len(self.filtered_rows): raise IndexError
        return index

    def prev_position(self, position):
        index = position-1
        if index < 0: raise IndexError
        return index

    def set_focus(self, position):
        # if self._focus == position:
        #     return
        if self.selection and self.detail_auto_open:
            # logger.info(f"datatable close details: {self._focus}, {position}")
            self[self._focus].close_details()
        self._emit("blur", self._focus)
        self._focus = position
        if self.selection and self.detail_auto_open:
            # logger.info(f"datatable open details: {self._focus}, {position}")
            self.selection.open_details()
        self._emit("focus", position)
        self._modified()

    def _modified(self):
        # self.focus_position = 0
        urwid.listbox.ListWalker._modified(self)

    def positions(self, reverse=False):
        if reverse:
            return range(len(self) - 1, -1, -1)
        return range(len(self))

    def __getitem__(self, position):
        # logger.debug("walker get: %d" %(position))
        if isinstance(position, slice):
            return [self[i] for i in range(*position.indices(len(self)))]
        if position < 0 or position >= len(self.filtered_rows):
            raise IndexError
        try:
            r = self.get_row_by_position(position)
            return r
        except IndexError as e:
            logger.debug(traceback.format_exc())
            raise
        # logger.debug("row: %s, position: %s, len: %d" %(r, position, len(self)))

    def __delitem__(self, position):
        if isinstance(position, slice):
            indexes = [self.position_to_index(p)
                       for p in range(*position.indices(len(self)))]
            self.delete_rows(indexes)
            # for i in range(*position.indices(len(self))):
            #     print(f"{position}, {i}")
            #     del self[i]
        else:
            try:
                # raise Exception(position)
                i = self.position_to_index(self.filtered_rows[position])
                self.delete_rows(i)
            except IndexError:
                logger.error(traceback.format_exc())
                raise

    def __len__(self):
        return len(self.filtered_rows)

    def __getattr__(self, attr):
        if attr in [
                "head",
                "tail",
                "index_name",
                "log_dump",
        ]:
            return getattr(self.df, attr)
        elif attr in ["body"]:
            return getattr(self.listbox, attr)
        else:
            return object.__getattribute__(self, attr)

        # raise AttributeError(attr)
        # else:
        #     return object.__getattribute__(self, attr)
        # elif attr == "body":
        #     return self.walker
        # raise AttributeError(attr)

    def render(self, size, focus=False):
        # logger.info("table render")
        self._width = size[0]
        if len(size) > 1:
            self._height = size[1]

        # if not self._initialized and not self.no_load_on_init:
        #     self._initialized = True
        #     self._invalidate()
        #     self.reset(reset_sort=True)

        # if not self._initialized:
        #     self._initialized = True
        # if not self.no_load_on_init:
        #     self._invalidate()
        #     self.reset(reset_sort=True)

        if not self._initialized:
            self._initialized = True
            self._invalidate()
            if not self.no_load_on_init:
                self.reset(reset_sort=True)

        return super().render(size, focus)

    @property
    def width(self):
        return self._width

    @property
    def min_width(self):
        return sum([
            c.min_width for c in self.visible_columns
        ])

    @property
    def height(self):
        return self._height

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key == "enter" and self.selection and not self.selection.details_focused:
            self._emit("select", self.selection.data)
        # else:
        #     # key = super().keypress(size, key)
        return key
        # if key == "enter":
        #     self._emit("select", self, self.selection)
        # else:
        #     return key

    def decorate(self, row, column, value):
        if column.decoration_fn:
            value = column.decoration_fn(value)
        if not isinstance(value, urwid.Widget):
            if isinstance(value, tuple):
                value = (value[0], str(value[1]))
            else:
                value = str(value)

            # value = DataTableText(value, wrap=column.wrap)
            value = urwid.Text(value)
        return value

    @property
    def column_names(self):
        return [c.name for c in self.data_columns]

    @property
    def focus_position(self):
        return self._focus
        # return self.listbox.focus_position

    @focus_position.setter
    def focus_position(self, value):
        self.set_focus(value)
        # self.listbox.focus_position = value
        self.listbox._invalidate()

    def position_to_index(self, position):
        # if not self.query_sort and self.sort_by[1]:
        #     position = -(position + 1)
        try:
            return self.df.index[position]
        except IndexError as e:
            # logger.info(f"position_to_index: {position}, {self.df.index}")
            raise
            logger.error(traceback.format_exc())
    def index_to_position(self, index):
        # raise Exception(index, self.df.index)
        # return self.df.index.index(index)
        return self.filtered_rows.index(index)

    def get_dataframe_row(self, index):
        try:
            return self.df.get_columns(index, as_dict=True)
        except ValueError as e:
            raise Exception(e, index, self.df.head(10))

    def get_dataframe_row_object(self, index):

        d = self.get_dataframe_row(index)
        cls = d.get("_cls")
        if cls:
            if HAVE_PYDANTIC and issubclass(cls, pydantic.main.BaseModel):
                # import ipdb; ipdb.set_trace()
                return cls(
                    **{
                        k: v
                        for k, v in d.items()
                        if v
                    }
                )
            elif hasattr(cls, "__dataclass_fields__"):
                # Python dataclasses
                # klass = type(f"DataTableRow_{cls.__name__}", [cls],
                klass = make_dataclass(
                    f"DataTableRow_{cls.__name__}",
                    [
                        ("_cls", typing.Optional[typing.Any], field(default=None)),
                    ],
                    bases=(cls,)
                )
                k = klass(
                    **{k: d[k]
                       for k in set(
                               cls.__dataclass_fields__.keys())
                    })
                return k
            elif HAVE_PONY and issubclass(cls, pony.orm.core.Entity):
                keys = {
                    k.name: d.get(k.name, None)
                    for k in (cls._pk_ if isinstance(cls._pk_, tuple) else (cls._pk_,))
                }
                # raise Exception(keys)
                with db_session:
                    return cls.get(**keys)
            else:
                return AttrDict(**d)
        else:
            return AttrDict(**d)


    def get_row(self, index):
        row = self.df.get(index, "_rendered_row")
        details_open = False
        if self.df.get(index, "_dirty") or row is None:
            self.refresh_calculated_fields([index])
            # vals = self[index]

            pos = self.index_to_position(index)
            vals = self.get_dataframe_row_object(index)
            row = self.render_item(index)
            position = self.index_to_position(index)
            if self.row_attr_fn:
                attr = self.row_attr_fn(position, row.data_source, row)
                if attr:
                    row.set_attr(attr)
            focus = self.df.get(index, "_focus_position")
            if focus is not None:
                row.set_focus_column(focus)
            if details_open:
                row.open_details()
            self.df.set(index, "_rendered_row", row)
            self.df.set(index, "_dirty", False)

        return row

    def get_row_by_position(self, position):
        # index = self.position_to_index(self.filtered_rows[position])
        index = self.filtered_rows[position]
        return self.get_row(index)

    def get_value(self, row, column):
        return self.df[self.position_to_index(row), column]

    def set_value(self, row, column, value):
        self.df.set(self.position_to_index(row), column, value)

    @property
    def selection(self):
        if len(self.body) and self.focus_position is not None:
            # FIXME: make helpers to map positions to indexes
            try:
                return self[self.focus_position]
            except IndexError:
                return None

    @property
    def selection_data(self):
        return AttrDict(self.df.get_columns(self.position_to_index(self.focus_position), as_dict=True))

    def render_item(self, index):
        row = DataTableBodyRow(self, index,
                               row_height= self.row_height,
                               divider = self.divider,
                               padding = self.padding,
                               # index=data[self.index],
                               cell_selection = self.cell_selection,
                               style = self.row_style)
        return row

    def refresh_calculated_fields(self, indexes=None):
        if not indexes:
            indexes = self.df.index[:]
        if not hasattr(indexes, "__len__"):
            indexes = [indexes]
        for col in self.data_columns:
            if not col.value_fn: continue
            for index in indexes:
                if self.df[index, "_dirty"]:
                    self.df.set(index, col.name, col.value_fn(self, self.get_dataframe_row_object(index)))

    def visible_data_column_index(self, column_name):
        try:
            return next(i for i, c in enumerate(self.visible_data_columns)
                     if c.name == column_name)

        except Exception as e:
            logger.error(f"column not found in visible_data_column_index: {column_name}")
            logger.exception(e)
            raise IndexError

    def sort_by_column(self, col=None, reverse=None, toggle=False):

        column_name = None
        column_number = None

        if isinstance(col, tuple):
            col, reverse = col

        elif col is None:
            col = self.sort_column


        if isinstance(col, int):
            try:
                column_name = self.visible_data_columns[col].name
            except IndexError:
                raise Exception("bad column number: %d" %(col))
            column_number = col
            # column_number = next(i for i, c in enumerate(self._columns) if c.name == column_name)
        elif isinstance(col, str):
            column_name = col
            try:
                column_number = self.visible_data_column_index(column_name)
                column_name = col
            except:

                column_name = self.initial_sort[0] or self.visible_data_columns[0].name
                if column_name is None:
                    return
                column_number = self.visible_data_column_index(column_name)


        self.sort_column = column_number

        if not column_name:
            return
        try:
            column = next((c for c in self._columns if c.name == column_name))
            column = self.column_named(column_name)
        except:
            return # FIXME

        if toggle and column_name == self.sort_by[0]:
            reverse = not self.sort_by[1]

        elif reverse is None and column.sort_reverse is not None:
            reverse = column.sort_reverse

        sort_by = (column_name, reverse)
        # if not self.query_sort:

        self.sort_by = sort_by
        logger.debug("sort_by: %s (%s), %s" %(column_name, self.sort_column, reverse))
        if self.query_sort:
            self.reset()

        row_index = None
        if self.sort_refocus:
            row_index = self[self._focus].data.get(self.index, None)
            logger.debug("row_index: %s" %(row_index))
        self.sort(column_name, key=column.sort_key)

        if self.with_header:
            self.header.update_sort(self.sort_by)

        self.set_focus_column(self.sort_column)
        if row_index:
            self.focus_position = self.index_to_position(row_index)

    def sort(self, column, key=None):
        logger.debug(column)
        if not key:
            key = lambda x: (x is None, x)
        self.df.sort_columns(
            column,
            key = key,
            reverse = self.sort_by[1])
        self._modified()


    def set_focus_column(self, index):
        idx = [i for i, c in enumerate(self.visible_columns)
                   if not isinstance(c, DataTableDivider)
        ][index]

        if self.with_header:
            self.header.set_focus_column(idx)

        if self.with_footer:
            self.footer.set_focus_column(idx)

        # logger.debug("set_focus_column: %d" %(index))
        self.df["_focus_position"] = idx
        self.df["_dirty"] = True

    def cycle_sort_column(self, step):

        if not self.ui_sort:
            return
        if self.sort_column is None:
            index = 0
        else:
            index = (self.sort_column + step)
            if index < 0: index = len(self.visible_data_columns)-1
            if index > len(self.visible_data_columns)-1: index = 0
        logger.debug("index: %d" %(index))
        self.sort_by_column(index)

    def sort_index(self):
        self.df.sort_index()
        self._modified()

    def add_columns(self, columns, data=None):

        if not isinstance(columns, list):
            columns = [columns]
            if data:
                data = [data]

        self._columns += columns
        for i, column in enumerate(columns):
            # FIXME: pass reference
            column.table = self
            self.df[column.name] = data=data[i] if data else None

        self.invalidate()

    def remove_columns(self, columns):

        if not isinstance(columns, list):
            columns = [columns]

        # FIXME
        columns = [ column
                    for column in columns
                    if column != "divider"]

        self._columns = [ c for c in self._columns if c.name not in columns ]
        self.df.delete_columns(columns)
        self.invalidate()

    def set_columns(self, columns):
        # logger.info(self._columns)
        self.remove_columns([c.name for c in self._columns])
        self.add_columns(columns)
        # logger.info(self._columns)
        self.reset()

    def toggle_columns(self, columns, show=None):

        if not isinstance(columns, list):
            columns = [columns]

        for column in columns:
            if isinstance(column, int):
                try:
                    column = self._columns[column]
                except IndexError:
                    raise Exception("bad column number: %d" %(column))
            else:
                try:
                    column = next(( c for c in self._columns if c.name == column))
                except StopIteration:
                    raise ValueError("column %s not found" %(column))
                    # raise Exception("column %s not found" %(column))

            if show is None:
                column.hide = not column.hide
            else:
                column.hide = not show
        self.invalidate()

    def show_columns(self, columns):
        self.toggle_columns(columns, True)

    def hide_columns(self, columns):
        self.toggle_columns(columns, False)

    def resize_column(self, name, size):

        try:
            index, col = next( (i, c) for i, c in enumerate(self.data_columns) if c.name == name)
        except StopIteration:
            raise Exception(self.data_columns, name)
        if isinstance(size, tuple):
            col.sizing, col.width = size
        elif isinstance(size, int):
            col.sizing = "given"
            col.width = size
        else:
            raise NotImplementedError
        if self.with_header:
            self.header.update()
        for r in self:
            r.update()
        if self.with_footer:
            self.footer.update()
        #     r.resize_column(index, size)

    def on_header_drag(self, source, source_column, start, end):

        if not source:
            return

        def resize_columns(cols, mins, index, delta, direction):
            logger.debug(f"cols: {cols}, mins: {mins}, index: {index}, delta: {delta}, direction: {direction}")
            new_cols = [c for c in cols]

            if (index == 0) or (direction == 1 and index != len(cols)-1):
                indexes = range(index, len(cols))
            else:
                indexes = range(index, -1, -1)
            # if len(indexes) < 2:
            #     raise Exception(indexes, cols, mins, index, delta, direction)

            deltas = [a-b for a, b in zip(cols, mins)]
            # logger.debug(f"deltas: {deltas}")
            d = delta

            for n, i in enumerate(indexes):
                # logger.debug(f"i: {i}, d: {d}")

                if delta < 0:
                    # can only shrink down to minimum for this column
                    # logger.debug(f"{d}, {-deltas[i]}")
                    try:
                        d = max(delta, -deltas[i])
                    except:
                        raise Exception(cols, mins, deltas, list(indexes))
                    # logger.debug(f"shrinking: {d}")
                elif delta > 0:
                    # can only grow to maximum of remaining deltas?
                    d = min(delta, sum([ deltas[x] for x in indexes[1:]]))
                    # logger.debug(f"growing: {d}")
                else:
                    continue

                new_cols[i] += d

                if i == index:
                    delta = -d
                    d = delta
                    indexes = list(reversed(indexes))
                    # logger.debug(f"reversing: {d}")
                else:
                    delta -= d
                    if delta == 0:
                        break

            return new_cols


        old_widths = self.header.column_widths( (self.width,) )

        if isinstance(source, DataTableDividerCell):
            try:
                index, cell = list(enumerate([ c for c in itertools.takewhile(
                    lambda c: c != source,
                    [ x[0] for x in self.header.columns.contents ]
                ) if not isinstance(c, DataTableDividerCell)]))[-1]
            except IndexError:
                index, cell = list(enumerate([ c for c in itertools.takewhile(
                    lambda c: c != source,
                    [ x[0] for x in self.header.columns.contents ]
                ) if not isinstance(c, DataTableDividerCell)]))[-1]
        else:
            cell = source
            index = next(i for i, c in enumerate([
                x[0] for x in self.header.columns.contents
                if not isinstance(x[0], DataTableDividerCell)
            ]) if c == cell)

        colname = cell.column.name
        column = next( c for c in self.visible_data_columns if c.name == colname)
        # index = index//2


        # new_width = old_width = column.header.width
        new_width = old_width = old_widths[index]

        delta = end-start


        if isinstance(source, DataTableDividerCell):
            drag_direction= 1
        # elif index == 0 and source_column <= int(round(column.header.width / 3)):
        elif index == 0 and source_column <= int(old_width / 3):
            return
        elif index != 0 and source_column <= int(round(old_width / 3)):
            drag_direction=-1
            delta = -delta
        elif index != len(self.visible_data_columns)-1 and source_column >= int(round( (2*old_width) / 3)):
            drag_direction=1
        else:
           return

        widths = [ c.header.width for c in self.visible_data_columns ]
        mins = [ c.min_width for c in self.visible_data_columns ]
        new_widths = resize_columns(widths, mins, index, delta, drag_direction)

        for i, c in enumerate(self.visible_data_columns):
            if c.header.width != new_widths[i]:
                self.resize_column(c.name, new_widths[i])

        self.resize_body_rows()
        logger.debug(f"{widths}, {mins}, {new_widths}")
        if sum(widths) != sum(new_widths):
            logger.warning(f"{sum(widths)} != {sum(new_widths)}")

    def resize_body_rows(self):
        for r in self:
            r.on_resize()

    # def toggle_details(self):
    #     self.selection.toggle_details()

    def enable_cell_selection(self):
        logger.debug("enable_cell_selection")
        for r in self:
            r.enable_cell_selection()
        self.reset()
        self.cell_selection = True

    def disable_cell_selection(self):
        logger.debug("disable_cell_selection")
        for r in self:
            r.disable_cell_selection()
        self.reset()
        self.cell_selection = False

    def toggle_cell_selection(self):
        if self.cell_selection:
            self.disable_cell_selection()
        else:
            self.enable_cell_selection()

    def column_named(self, name):
        return next( (c for c in self._columns if c.name == name) )

    @property
    def data_columns(self):
        return [ c for c in self._columns if not isinstance(c, DataTableDivider) ]

    @property
    def visible_columns(self):
        return [ c for c in self._columns if not c.hide ]

    @property
    def visible_data_columns(self):
        return [ c for c in self.data_columns if not c.hide ]


    def add_row(self, data, sort=True):

        self.df.append_rows([data])
        if sort:
            self.sort_by_column()
        self.apply_filters()

    def delete_rows(self, indexes):

        self.df.delete_rows(indexes)
        self.apply_filters()
        if self.focus_position > 0 and self.focus_position >= len(self)-1:
            self.focus_position = len(self)-1


    def invalidate(self):
        self.df["_dirty"] = True
        if self.with_header:
            self.header.update()
        if self.with_footer:
            self.footer.update()

        # self._modified()

    def invalidate_rows(self, indexes):
        if not isinstance(indexes, list):
            indexes = [indexes]
        for index in indexes:
            self.refresh_calculated_fields(index)

        self.df[indexes, "_dirty"] = True
        self._modified()
        # FIXME: update header / footer if dynamic

    def invalidate_selection(self):
        self.invalidate_rows(self.focus_position)

    def swap_rows_by_field(self, p0, p1, field=None):

        if not field:
            field=self.index

        i0 = self.position_to_index(p0)
        i1 = self.position_to_index(p1)

        r0 = { k: v[0] for k, v in list(self.df[i0, None].to_dict().items()) }
        r1 = { k: v[0] for k, v in list(self.df[i1, None].to_dict().items()) }

        for k, v in list(r0.items()):
            if k != field:
                self.df.set(i1, k, v)

        for k, v in list(r1.items()):
            if k != field:
                self.df.set(i0, k, v)
        self.df.set(i0, "_dirty", True)

        self.invalidate_rows([i0, i1])

    def swap_rows(self, p0, p1, field=None):
        self.swap_rows_by_field(p0, p1, field=field)

    def row_count(self):

        # if not self.limit:
        #     return None

        if self.limit:
            return self.query_result_count()
        else:
            return len(self)

    def apply_filters(self, filters=None):

        if not filters:
            filters = self.filters
        elif not isinstance(filters, list):
            filters = [filters]

        self.filtered_rows = list(
            row[self.df.index_name]
            for i, row in enumerate(self.df.iterrows())
            if not filters or all(
                    f(row)
                    for f in filters
            )
        )
        # if self.focus_position > len(self):
        #     self.focus_position = len(self)-1

        # logger.debug("filtered: %s" %(self.filtered_rows))


        self.filters = filters
        # self.invalidate()

    def clear_filters(self):
        self.filtered_rows = list(range(len(self.df)))
        self.filters = None
        # self.invalidate()


    def load_all(self):
        if len(self) >= self.query_result_count():
            return
        logger.debug("load_all: %s" %(self.page))
        self.requery(self.page*self.limit, load_all=True)
        self.page = (self.query_result_count() // self.limit)
        self.listbox._invalidate()


    def load_more(self, position):

        # logger.debug("load_more")
        if position is not None and position > len(self):
            return False
        self.page += 1
        # self.page = len(self) // self.limit
        offset = (self.page)*self.limit
        # logger.debug(f"offset: {offset}, row count: {self.row_count()}")
        # if (self.row_count() is not None
        #     and len(self) >= self.row_count()):
        #     self._emit("end", self.row_count())
        #     return False

        updated = self.requery(offset=offset)
        # try:
        #     updated = self.requery(offset=offset)
        # except Exception as e:
        #     raise Exception(f"{position}, {len(self)}, {self.row_count()}, {offset}, {self.limit}, {str(e)}")

        return updated

    def requery(self, offset=None, limit=None, load_all=False, **kwargs):
        logger.debug(f"requery: {offset}, {limit}")
        if (offset is not None) and self.limit:
            self.page = offset // self.limit
            offset = self.page*self.limit
            limit = self.limit
        elif self.limit:
            self.page = (limit // self.limit)
            limit = (self.page) * self.limit
            offset = 0

        kwargs = {"load_all": load_all}
        if self.query_sort:
            kwargs["sort"] = self.sort_by
        else:
            kwargs["sort"] = (None, False)
        limit = limit or self.limit
        if limit:
            kwargs["offset"] = offset
            kwargs["limit"] = limit

        if offset:
            kwargs["cursor"] = self.pagination_cursor

        rows = list(self.query(**kwargs)) if self.data is None else self.data

        if len(rows) and self.sort_by[0]:
            self.pagination_cursor = getattr(rows[-1], self.sort_by[0])

        updated = self.df.update_rows(rows, replace=self.limit is None, with_sidecar = self.with_sidecar)

        self.df["_focus_position"] = self.sort_column

        self.refresh_calculated_fields()
        self.apply_filters()
        if not self.query_sort:
            self.sort_by_column(self.initial_sort)


        if len(updated):
            for i in updated:
                if not i in self.filtered_rows:
                    continue
                pos = self.index_to_position(i)
                self[pos].update()
            # self.sort_by_column(*self.sort_by)

        self._modified()
        self._emit("requery", self.row_count())

        if not len(self) and self.empty_message:
            self.show_message(self.empty_message)
        else:
            self.hide_message()
        return len(updated)
        # self.invalidate()


    def refresh(self, reset=False):
        logger.debug(f"refresh: {reset}")
        offset = None
        idx = None
        pos = 0
        # limit = len(self)-1
        self.df.delete_all_rows()
        if reset:
            self.page = 0
            offset = 0
            limit = self.limit
        else:
            try:
                idx = getattr(self.selection.data, self.index)
                pos = self.focus_position
            except (AttributeError, IndexError, ValueError):
                pos = None
            limit = len(self)
        # del self[:]
        self.requery(offset=offset, limit=limit)

            # self.sort_by_column(self.sort_by[0], key=column.sort_key)
        if self._initialized:
            self.pack_columns()

        if idx:
            try:
                pos = self.index_to_position(idx)
            except:
                return
        if pos is not None:
            self.focus_position = pos

        # self.focus_position = 0

    def reset_columns(self):
        for c in self.visible_columns:
            if c.sizing == c.initial_sizing and c.width == c.initial_width:
                continue
            # print(c.initial_sizing, c.initial_width)
            self.resize_column(c.name, (c.initial_sizing, c.initial_width) )
            # c.sizing = c.initial_sizing
            # c.width = c.initial_width


    def reset(self, reset_sort=False):

        self.pagination_cursor = None
        self.refresh(reset=True)

        if reset_sort and self.initial_sort is not None:
            self.sort_by_column(self.initial_sort)
        # if self._initialized:
        #     for r in self:
        #         if r.details_open:
        #             r.open_details()
        self._modified()
        if len(self):
            self.set_focus(0)
        # self._invalidate()

    def pack_columns(self):

        # logger.info("pack_columns")
        widths = self.header.column_widths( (self.width,) )
        logger.debug(f"{self}, {widths}")

        other_columns, pack_columns = [
            list(x) for x in partition(
                lambda c: c[0].pack == True,
                zip(self.visible_columns, widths)
            )
        ]

        other_widths = sum([c[1] for c in other_columns])

        num_pack = len(pack_columns)
        available = self.width - (1 if self.with_scrollbar else 0) - other_widths
        if self.row_style in ["boxed", "grid"]:
            available -= 2

        for i, (c, cw) in enumerate(pack_columns):
            w = min(c.contents_width, available//(num_pack-i))
            logger.debug(f"resize: {c.name}, available: {available}, contents: min({c.contents_width}, {available//(num_pack-i)}), {w})")
            self.resize_column(c.name, w)
            available -= w

        self.resize_body_rows()


    def show_message(self, message):

        if self._message_showing:
            self.hide_message()

        overlay = urwid.Overlay(
            urwid.Filler(
                urwid.Pile([
                    ( "pack", urwid.Padding(
                        urwid.Text( ("table_message", message) ),
                        width="pack",
                        align="center"
                    )),
                    (1, urwid.Filler(urwid.Text("")))
                ]),
                valign="top"
            ),
            self.listbox,
            "center", ("relative", 100), "top", ("relative", 100)
        )
        overlay.selectable = lambda: True
        self.listbox_placeholder.original_widget = overlay
        self._message_showing = True

    def hide_message(self):
        if not self._message_showing:
            return
        self.listbox_placeholder.original_widget = self.listbox

    def load(self, path):

        with open(path, "r") as f:
            json = "\n".join(f.readlines())
            self.df = DataTableDataFrame.from_json(json)
        self.reset()

    def save(self, path):
        # print(path)
        with open(path, "w") as f:
            f.write(self.df.to_json())

__all__ = ["DataTable", "DataTableColumn"]
