import logging
logger = logging.getLogger("panwid.datable")
import urwid
import urwid_utils.palette
from ..listbox import ScrollingListBox
from orderedattrdict import OrderedDict
import itertools
import traceback
from datetime import datetime, date as datetype
import math
from blist import blist

from .dataframe import *
from .rows import *

class NoSuchColumnException(Exception):
    pass

def make_value_function(template):

    def inner(table, row):
        return template.format(
            row=table.index_to_position(
                row.get(table.index)
            )+1,
            rows_loaded = len(table),
            rows_total = table.query_result_count()
        )

    return inner


class DataTableColumn(object):

    def __init__(self, name,
                 label=None,
                 value=None,
                 width=('weight', 1),
                 align="left", wrap="space",
                 padding = DEFAULT_CELL_PADDING, #margin=1,
                 hide=False,
                 format_fn=None,
                 format_record = None, # format_fn is passed full row data
                 attr = None,
                 sort_key = None, sort_reverse=False,
                 sort_icon = None,
                 footer_fn = None, footer_arg = "values"):

        self.name = name
        self.label = label if label is not None else name
        if value:
            if isinstance(value, str):
                self.value_fn = make_value_function(value)
            elif callable(value):
                self.value_fn = value
        else:
            self.value_fn = None
        self.width = width
        self.align = align
        self.wrap = wrap
        self.padding = padding
        self.hide = hide
        self.format_fn = format_fn
        self.format_record = format_record
        self.attr = attr
        self.sort_key = sort_key
        self.sort_reverse = sort_reverse
        self.sort_icon = sort_icon
        self.footer_fn = footer_fn
        self.footer_arg = footer_arg

        if isinstance(self.width, tuple):
            if self.width[0] != "weight":
                raise Exception(
                    "Column width %s not supported" %(col.width[0])
                )
            self.sizing, self.width = self.width
        elif isinstance(width, int):
            self.sizing = "given"
        else:
            self.sizing = width


    def width_with_padding(self, table_padding=None):
        padding = 0
        if self.padding is None and table_padding is not None:
            padding = table_padding
        return self.width + 2*padding


    def _format(self, v):

        # First, call the format function for the column, if there is one
        if self.format_fn:
            try:
                v = self.format_fn(v)
            except Exception as e:
                logger.error("%s format exception: %s" %(self.name, v))
                logger.exception(e)
                raise e
        return self.format(v)


    def format(self, v):

        # Do our best to make the value into something presentable
        if v is None:
            v = ""
        elif isinstance(v, int):
            v = "%d" %(v)
        elif isinstance(v, float):
            v = "%.03f" %(v)
        elif isinstance(v, datetime):
            v = v.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(v, datetype):
            v = v.strftime("%Y-%m-%d")

        if not isinstance(v, urwid.Widget):
            v = str(v)
            v = urwid.Text(v, align=self.align, wrap=self.wrap)
        return v


class DataTable(urwid.WidgetWrap, urwid.listbox.ListWalker):


    signals = ["select", "refresh",
               # "focus", "unfocus", "row_focus", "row_unfocus",
               "drag_start", "drag_continue", "drag_stop"]

    ATTR = "table"

    columns = []

    limit = None
    index = "index"

    with_header = True
    with_footer = False
    with_scrollbar = False
    cell_selection = False

    sort_by = (None, None)
    query_sort = False
    sort_icons = True
    sort_refocus = False

    border = DEFAULT_TABLE_BORDER
    padding = DEFAULT_CELL_PADDING

    data = None
    ui_sort = True

    attr_map = {}
    focus_map = {}
    column_focus_map = {}
    highlight_map = {}
    highlight_focus_map = {}
    highlight_focus_map2 = {}

    detail_fn = None
    detail_column = None
    auto_expand_details = False

    def __init__(self,
                 columns = None,
                 data = None,
                 limit = None,
                 index = None,
                 with_header = None, with_footer = None, with_scrollbar = None,
                 cell_selection = None,
                 sort_by = None, query_sort = None, sort_icons = None,
                 sort_refocus = None,
                 border = None, padding = None,
                 detail_fn = None, detail_column = None,
                 auto_expand_details = False,
                 ui_sort = None):

        self._focus = 0
        if columns is not None: self.columns = columns
        if not self.columns:
            raise Exception("must define columns for data table")
        if index: self.index = index

        if not self.index in self.column_names:
            self.columns.insert(
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
        if sort_refocus is not None: self.sort_refocus = sort_refocus

        if with_header is not None: self.with_header = with_header
        if with_footer is not None: self.with_footer = with_footer
        if with_scrollbar is not None: self.with_scrollbar = with_scrollbar
        if cell_selection is not None: self.cell_selection = cell_selection
        if border is not None: self.border = border
        if padding is not None: self.padding = padding

        if ui_sort is not None: self.ui_sort = ui_sort

        if detail_fn is not None: self.detail_fn = detail_fn
        if detail_column is not None: self.detail_column = detail_column
        if auto_expand_details: self.auto_expand_details = auto_expand_details

        # self.offset = 0
        if limit:
            self.limit = limit

        self.sort_column = None

        self.filters = None
        self.filtered_rows = blist()

        kwargs = dict(
            columns = self.column_names,
            use_blist=True,
            sort=False,
            # sorted=True,
        )
        if self.index:
            kwargs["index_name"] = self.index

        self.df = DataTableDataFrame(**kwargs)

        self.pile = urwid.Pile([])
        self.listbox = ScrollingListBox(
            self, infinite=self.limit,
            with_scrollbar = self.with_scrollbar,
            row_count_fn = self.row_count
        )

        urwid.connect_signal(
            self.listbox, "select",
            lambda source, selection: urwid.signals.emit_signal(
                self, "select", self, self.get_dataframe_row(selection.index))
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

        if self.with_header:
            self.header = DataTableHeaderRow(
                self,
                border = self.border,
                padding = self.padding,
            )

            self.pile.contents.insert(0,
                (self.header, self.pile.options('pack'))
             )

            if self.ui_sort:
                urwid.connect_signal(
                    self.header, "column_click",
                    lambda index: self.sort_by_column(index, toggle=True)
                )

        self.pile.contents.append(
            (self.listbox, self.pile.options('weight', 1))
         )
        self.pile.focus_position = len(self.pile.contents)-1

        if self.with_footer:
            self.footer = DataTableFooterRow(
                self,
                border = self.border,
                padding = self.padding
            )
            self.pile.contents.append(
                (self.footer, self.pile.options('pack'))
             )


        self.reset()

        if self.sort_by:
            self.sort_by_column(self.sort_by)


        self.attr = urwid.AttrMap(
            self.pile,
            attr_map = self.attr_map,
            # focus_map = self.focus_map
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
                entries[attr] = PaletteEntry(
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
                    # logger.info("%s, %s, %s" %(cfg, cblack, cwhite))
                    # raise Exception("%s, %s, %s, %s, %s, %s" %(table_bg, color_fg, color_bg, cfg, cblack, cwhite))
                    if cfg < min_contrast and cfg < cblack:
                        # logger.info("adjusting contrast of %s" %(name))
                        foreground_high = "black"
                        # if cblack > cwhite:
                        # else:
                        #     foreground_high = "white"

                if suffix:
                    attr = ' '.join([name, suffix])
                else:
                    attr = name

                # print foreground, foreground_high, background, background_high
                entries[attr] = PaletteEntry(
                    mono = "white",
                    foreground = foreground,
                    background = background,
                    foreground_high = foreground_high,
                    background_high = background_high,
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
        # logger.debug("walker set_focus: %d" %(position))
        self._focus = position
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
        if position < 0 or position >= len(self.filtered_rows): raise IndexError
        try:
            r = self.get_row_by_position(position)
            return r
        except IndexError:
            logger.error(traceback.format_exc())
            raise
        # logger.debug("row: %s, position: %s, len: %d" %(r, position, len(self)))

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
        # elif attr == "body":
        #     return self.walker
        # raise AttributeError(attr)

    @property
    def column_names(self):
        return [c.name for c in self.columns]

    @property
    def focus_position(self):
        return self._focus
        # return self.listbox.focus_position

    @focus_position.setter
    def focus_position(self, value):
        self._focus = value
        # self.listbox.focus_position = value
        self.listbox._invalidate()

    def position_to_index(self, position):
        # if not self.query_sort and self.sort_by[1]:
        #     position = -(position + 1)
        return self.df.index[position]

    def index_to_position(self, index):
        # raise Exception(index, self.df.index)
        return self.df.index.index(index)

    def get_dataframe_row(self, index):
        logger.debug("__getitem__: %s" %(index))
        try:
            v = self.df[index:index]
        except IndexError:
            logger.debug(traceback.format_exc())

        return self.df.get_columns(index, as_dict=True)

    def get_row(self, index):
        try:
            row = self.df.get(index, "_rendered_row")
        except:
            raise

        if self.df.get(index, "_dirty") or not row:
            self.refresh_calculated_fields([index])
            # vals = self[index]
            vals = self.get_dataframe_row(index)
            row = self.render_item(vals)
            focus = self.df.get(index, "_focus_position")
            if focus is not None:
                row.set_focus_column(focus)
            self.df.set(index, "_rendered_row", row)
            self.df.set(index, "_dirty", False)
        return row

    def get_row_by_position(self, position):
        index = self.position_to_index(self.filtered_rows[position])
        return self.get_row(index)

    @property
    def selection(self):
        if len(self.body) and self.focus_position is not None:
            # FIXME: make helpers to map positions to indexes
            return self[self.focus_position]


    def render_item(self, item):
        # raise Exception(item)
        row = DataTableBodyRow(self, item,
                               border = self.border,
                               padding = self.padding,
                               index=item[self.index],
                               cell_selection = self.cell_selection)
        return row

    def refresh_calculated_fields(self, indexes=None):
        if not indexes:
            indexes = self.df.index[:]
        if not hasattr(indexes, "__len__"):
            indexes = [indexes]
        for col in self.columns:
            if not col.value_fn: continue
            for index in indexes:
                if self.df[index, "_dirty"]:
                    self.df.set(index, col.name, col.value_fn(self, self.get_dataframe_row(index)))

    def visible_column_index(self, column_name):
        try:
            return next(i for i, c in enumerate(self.visible_columns)
                     if c.name == column_name)

        except StopIteration:
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
                column_name = self.visible_columns[col].name
            except IndexError:
                raise Exception("bad column number: %d" %(col))
            column_number = col
        elif isinstance(col, str):
            column_name = col
            try:
                column_number = self.visible_column_index(column_name)
            except:
                column_number = None

        self.sort_column = column_number

        if not column_name:
            return
        try:
            column = next((c for c in self.columns if c.name == column_name))
        except:
            return # FIXME

        if reverse is None and column.sort_reverse is not None:
            reverse = column.sort_reverse

        if toggle and column_name == self.sort_by[0]:
            reverse = not self.sort_by[1]
        sort_by = (column_name, reverse)
        # if not self.query_sort:

        self.sort_by = sort_by
        logger.info("sort_by: %s (%s), %s" %(column_name, self.sort_column, reverse))
        if self.query_sort:
            self.reset()

        row_index = None
        if self.sort_refocus:
            row_index = self[self._focus].data.get(self.index, None)
            logger.info("row_index: %s" %(row_index))
        self.sort(column_name, key=column.sort_key)

        if self.with_header:
            self.header.update_sort(self.sort_by)

        self.set_focus_column(self.sort_column)
        if row_index:
            self.focus_position = self.index_to_position(row_index)

    def sort(self, column, key=None):
        import functools
        logger.debug(column)
        if not key:
            key = lambda x: (x is None, x)
        self.df.sort_columns(
            column,
            key = key,
            reverse = self.sort_by[1])
        self._modified()


    def set_focus_column(self, index):
        if self.with_header:
            self.header.set_focus_column(self.sort_column)

        if self.with_footer:
            self.footer.set_focus_column(self.sort_column)

        # logger.debug("set_focus_column: %d" %(index))
        self.df["_focus_position"] = index
        self.df["_dirty"] = True

    def cycle_sort_column(self, step):

        if not self.ui_sort:
            return
        if self.sort_column is None:
            index = 0
        else:
            index = (self.sort_column + step)
            if index < 0: index = len(self.visible_columns)-1
            if index > len(self.visible_columns)-1: index = 0
        logger.debug("index: %d" %(index))
        self.sort_by_column(index)

    def sort_index(self):
        self.df.sort_index()
        self._modified()

    def requery(self, offset=0, load_all=False, **kwargs):

        # logger.info("requery")
        kwargs = {"load_all": load_all}
        if self.query_sort:
            kwargs["sort"] = self.sort_by
        else:
            kwargs["sort"] = (None, False)
        if self.limit:
            kwargs["offset"] = offset
            kwargs["limit"] = self.limit

        if self.data:
            rows = self.data
        else:
            rows = list(self.query(**kwargs))
        self.append_rows(rows)
        self.refresh_calculated_fields()
        self.apply_filters()



    def append_rows(self, rows):
        # logger.info("append_rows: %s" %([row[self.index] for row in rows]))
        self.df.append_rows(rows)
        self.df["_focus_position"] = self.sort_column
        self.invalidate()
        self._modified()

    def add_columns(self, columns, data=None):

        if not isinstance(columns, list):
            columns = [columns]
            if data:
                data = [data]

        self.columns += columns
        for i, column in enumerate(columns):
            self.df[column.name] = data=data[i] if data else None

        self.invalidate()

    def remove_columns(self, columns):

        if not isinstance(columns, list):
            columns = [columns]

        columns = [ self.columns[column].name
                    if isinstance(column, int)
                    else column for column in columns ]

        self.columns = [ c for c in self.columns if c.name not in columns ]
        self.df.delete_columns(columns)
        self.invalidate()

    def set_columns(self, columns):
        self.remove_columns([c.name for c in self.columns])
        self.add_columns(columns)
        self.reset()

    def toggle_columns(self, columns, show=None):

        if not isinstance(columns, list):
            columns = [columns]

        for column in columns:
            if isinstance(column, int):
                try:
                    column = self.columns[column]
                except IndexError:
                    raise Exception("bad column number: %d" %(column))
            else:
                try:
                    column = next(( c for c in self.columns if c.name == column))
                except IndexError:
                    raise Exception("column %s not found" %(column))

            if show is None:
                column.hide = not column.hide
            else:
                column.hide = show
        self.invalidate()

    def show_columns(self, columns):
        self.toggle_columns(columns, True)

    def hide_columns(self, columns):
        self.show_column(columns, False)

    def toggle_details(self):
        self.selection.toggle_details()

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

    @property
    def visible_columns(self):
        return [ c for c in self.columns if not c.hide ]

    def add_row(self, data, sort=True):

        self.append_rows([data])
        if sort:
            self.sort_by_column()
        self.apply_filters()
        # else:
        #     self.invalidate()

    def delete_rows(self, indexes):
        self.df.delete_rows(indexes)
        self.apply_filters()
        if self.focus_position >= len(self)-1:
            self.focus_position = len(self)-1


    def invalidate(self):
        self.df["_dirty"] = True
        if self.with_header:
            self.header.update()
        if self.with_footer:
            self.footer.update()
        self._modified()

    def invalidate_rows(self, indexes):
        if not isinstance(indexes, list):
            indexes = [indexes]
        for index in indexes:
            self.refresh_calculated_fields(index)

        self.df[indexes, "_dirty"] = True
        self._modified()
        # FIXME: update header / footer if dynamic

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
        # r0 = self[self.position_to_index(p0)]
        # r1 = self[self.position_to_index(p1)]
        self.swap_rows_by_field(p0, p1, field=field)

    def row_count(self):

        if not self.with_scrollbar:
            return None

        if self.limit:
            if self.page*self.limit >= self.query_result_count():
                return len(self.filtered_rows)
            else:
                return self.query_result_count()
        else:
            return len(self)

    def load_more(self):
        offset = self.page*self.limit
        if offset >= self.row_count():# or offset >= len(self):
            return
        logger.info("load_more: page: %s, offset: %s, len: %s" %(self.page, offset, self.row_count()))
        self.requery(offset)
        self.page += 1

    def load_all(self):
        if len(self) >= self.query_result_count():
            return
        logger.info("load_all: %s" %(self.page))
        self.requery(self.page*self.limit, load_all=True)
        self.page = (self.query_result_count() // self.limit)
        self.listbox._invalidate()

    def apply_filters(self, filters=None):

        if not filters:
            filters = self.filters
        elif not isinstance(filters, list):
            filters = [filters]

        self.filtered_rows = blist(
            i
            for i, row in enumerate(self.df.iterrows())
            if not filters or all(
                    f(row)
                    for f in filters
            )
        )
        if self.focus_position > len(self):
            self.focus_position = len(self)-1

        # logger.info("filtered: %s" %(self.filtered_rows))


        self.filters = filters
        self.invalidate()

    def clear_filters(self):
        self.filtered_rows = blist(range(len(self.df)))
        self.filters = None
        self.invalidate()

    def reset(self, reset_sort=False):
        logger.debug("reset")
        # self.offset = 0
        # if self.query_sort:
            # self.df.clear()
        # if requery or self.query_sort:
        self.df.clear()
        self.requery()
        self.page = 1
        self.clear_filters()
        self.apply_filters()
        if reset_sort:
            self.sort_by_column(self.initial_sort)
        self.focus_position = 0
        # self.invalidate()

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
