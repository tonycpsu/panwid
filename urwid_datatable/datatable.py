#!/usr/bin/python
from __future__ import division
import urwid
from urwid_utils.palette import *
import raccoon as rc
from listbox import ScrollingListBox
import logging
logger = logging.getLogger(__name__)

import traceback

from datetime import datetime, date as datetype

class DataTableHeaderLabel(str):
    pass


class DataTableCell(urwid.WidgetWrap):

    ATTR = "table_cell"
    attr_map = { None: ATTR }
    # focus_map = {ATTR: "%s focused" %(ATTR)}
    attr_map = {}
    focus_map = {}

    def __init__(self, column, value):

        self.column = column
        # self._attr_map =  self.attr_map.copy()
        # self._focus_map =  self.focus_map.copy()

        # self._attr_map.update(row.attr_map)
        # self._focus_map.update(row.focus_map)
        # raise Exception(self._focus_map)

        self.widget = self.format(value)
        # self.text = urwid.Text(value)
        self.padding = urwid.Padding(
            self.widget,
            left=self.column.padding or 0,
            right=self.column.padding or 0
        )
        self.attr = urwid.AttrMap(
            self.padding,
            attr_map = self.attr_map
        )
        # raise Exception(self.widget)
        super(DataTableCell, self).__init__(self.attr)


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
            v = urwid.Text(v,
                           align=self.column.align,
                           wrap=self.column.wrap)
        return v


    def selectable(self):
        return True

    def keypress(self, size, key):
        return key
        # return super(DataTableCell, self).keypress(size, key)


class DataTableColumn(object):

    def __init__(self, name, dtype=None,
                 label=None, width=('weight', 1),
                 align="left", wrap="space", padding = None,
                 format_fn=None, attr = None,
                 sort_key = None, sort_fn = None, sort_reverse=False,
                 footer_fn = None):

        self.name = name
        self.dtype = dtype
        self.label = label if label else name
        self.width = width
        self.align = align
        self.wrap = wrap
        self.padding = padding
        self.format_fn = format_fn
        self.attr = attr
        self.sort_key = sort_key
        self.sort_fn = sort_fn
        self.sort_reverse = sort_reverse
        self.footer_fn = footer_fn
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



    def _format(self, v):

        if isinstance(v, DataTableHeaderLabel):
            return urwid.Text(v, align=self.align, wrap=self.wrap)
        else:
            if isinstance(v, float) and np.isnan(v):
                v = None
            # First, call the format function for the column, if there is one
            if self.format_fn:
                try:
                    v = self.format_fn(v)
                except TypeError, e:
                    # logger.debug("format function raised exception: %s" %e)
                    return urwid.Text("", align=self.align, wrap=self.wrap)
                except:
                    raise
            return self.format(v)


    def format(self, v):

        # Do our best to make the value into something presentable
        if v is None:
            v = ""
        if isinstance(v, float) and np.isnan(v):
            v = ""
        elif isinstance(v, int):
            v = "%d" %(v)
        elif isinstance(v, float):
            v = "%.03f" %(v)
        elif isinstance(v, datetime):
            v = v.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(v, date):
            v = v.strftime("%Y-%m-%d")

        if not isinstance(v, urwid.Widget):
            v = urwid.Text(v, align=self.align, wrap=self.wrap)
        return v


    def cell(self, value):
        return DataTableCell(self, value)


class DataTableRow(urwid.WidgetWrap):

    ATTR = "table_row"

    def __init__(self, columns, cells):

        self.attr_map =  { None: self.ATTR }
        self.focus_map = {None: "%s focused" %(self.ATTR)}

        self.columns = urwid.Columns([])

        # for i, col in enumerate(table.columns):

        #     self.columns.contents.append(
        #         (col.cell(data[i]), self.columns.options(col.sizing, col.width))
        #     )


        for i, cell in enumerate(cells):
            col = columns[i]
            self.columns.contents.append(
                (cell, self.columns.options(col.sizing, col.width))
            )


        self.attr = urwid.AttrMap(
            self.columns,
            attr_map = self.attr_map,
            focus_map = self.focus_map
        )
        super(DataTableRow, self).__init__(self.attr)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return super(DataTableRow, self).keypress(size, key)


class DataTableBodyRow(DataTableRow):

    def __init__(self, columns, data):

        cells = [col.cell(data[i]) for i, col in enumerate(columns)]
        super(DataTableBodyRow, self).__init__(columns, cells)


class DataTableHeaderRow(DataTableRow):

    signals = ['column_click']

    ATTR = "table_header"

    def __init__(self, columns):

        cells = [col.cell(col.label) for i, col in enumerate(columns)]
        super(DataTableHeaderRow, self).__init__(columns, cells)

    def selectable(self):
        return False


class DataTableFooterRow(DataTableRow):

    ATTR = "table_footer"


    def __init__(self, columns):

        cells = [col.cell(col.label) for i, col in enumerate(columns)]
        super(DataTableFooterRow, self).__init__(columns, cells)

    def selectable(self):
        return False


class DataTable(urwid.WidgetWrap):


    ATTR = "table"

    # attr_map = { None: ATTR }
    focus_map = {None: "%s focused" %(ATTR)}

    columns = []

    limit = None
    index = None
    query_sort = False
    sort_by = None

    with_header = False
    with_footer = False
    with_scrollbar = None

    ui_sort = False

    def __init__(self,
                 index=None,
                 limit=None,
                 query_sort=None, sort_by=None,
                 with_header=None, with_footer=None, with_scrollbar=False,
                 ui_sort=None):

        class DataTableListWalker(urwid.listbox.ListWalker):

            table = self

            def __init__(self):
                self._focus = 0
                super(DataTableListWalker, self).__init__()

            def __getitem__(self, position):
                # logger.debug("walker get: %d" %(position))
                if position < 0 or position >= len(self): raise IndexError
                try:
                    r = self.table.get_row(position)
                    return r
                except IndexError:
                    logger.error(traceback.format_exc(5))
                    raise
                # logger.debug("row: %s, position: %s, len: %d" %(r, position, len(self)))

            @property
            def focus(self): return self._focus

            def next_position(self, position):
                index = position + 1
                # index = self.table.df.index[position+1]
                logger.debug("walker next: %d, len: %d" %(position, len(self)))
                if index > len(self): raise IndexError
                return index

            def prev_position(self, position):
                index = position-1
                # index = self.table.df.index[position-1]
                logger.debug("walker prev: %d, len: %d" %(position, len(self)))
                if index < 0: raise IndexError
                return index

            def set_focus(self, position):
                logger.debug("walker set_focus: %d" %(position))
                self._focus = position
                self._modified()

            def __len__(self): return len(self.table)

            def _modified(self):
                self.focus_position = 0
                super(DataTableListWalker, self)._modified()


        if index: self.index = index
        if query_sort: self.query_sort = query_sort
        if sort_by: self.sort_by = sort_by

        if with_header: self.with_header = with_header
        if with_footer: self.with_footer = with_footer
        if with_scrollbar: self.with_scrollbar = with_scrollbar

        if ui_sort: self.ui_sort = ui_sort
        if limit:
            self.offset = 0
            self.limit = limit

        self.colnames = [c.name for c in self.columns]
        self.pd_columns = self.colnames + ["_rendered_row"]

        self.df = rc.DataFrame(
            columns = self.colnames,
            use_blist=True,
            sorted=False,
            # sorted=True,
            index_name = self.index,
        )
        self.df["_rendered_row"] = None

        self.walker = DataTableListWalker()


        self.pile = urwid.Pile([])
        self.listbox = ScrollingListBox(
            self.walker, infinite=self.limit,
            with_scrollbar = self.with_scrollbar,
            row_count_fn = (self.query_result_count
                            if self.with_scrollbar
                            else None)
            )

        if self.limit:
            urwid.connect_signal(self.listbox, "load_more", self.load_more)
            self.offset = 0

        if self.with_header:
            self.header = DataTableHeaderRow(self.columns)
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
            self.footer = DataTableFooterRow(self.columns)
            self.pile.contents.append(
                (self.footer, self.pile.options('pack'))
             )


        self.requery()

        self.attr = urwid.AttrMap(
            self.pile,
            attr_map = {},
            focus_map = {}
        )
        super(DataTable, self).__init__(self.attr)


    def query(self, sort=None, offset=None):
        raise Exception("query method must be overriden")

    def query_result_count(self):
        raise Exception("query_result_count method must be defined")

    @classmethod
    def get_palette_entries(cls):

        foreground_map = {
            "table_row": [ "light gray", "light gray" ],
            "header_row": [ "light gray", "light gray" ],
        }

        background_map = {
            None: [ "black", "black" ],
            "focused": [ "dark gray", "g11" ],
            "column_focused": [ "dark gray", "g11" ],
            "column_focused focused": [ "dark gray", "g19" ],
        }

        entries = dict()

        row_attr = "table_row"
        for suffix in [None, "focused",
                       "column_focused", "column_focused focused"]:
            if suffix:
                attr = ' '.join([row_attr, suffix])
            else:
                attr = row_attr
            entries[attr] = PaletteEntry(
                mono = "white",
                foreground = foreground_map[row_attr][0],
                background = background_map[suffix][0],
                foreground_high = foreground_map[row_attr][1],
                background_high = background_map[suffix][1],
            )


        header_foreground_map = {
            None: ["white,bold", "white,bold"],
            # "focused": ["white,bold", "white,bold"],
            "column_focused": ["yellow,bold", "yellow,bold"],
            "column_focused focused": ["yellow,bold", "yellow,bold"],
        }

        header_background_map = {
            None: ["light gray", "g40"],
            # "focused": ["light gray", "g40"],
            "column_focused": ["light gray", "g40"],
            "column_focused focused": ["light gray", "g40"],
        }

        for prefix in ["table_header", "table_footer"]:
            for suffix in [None, "column_focused"]:
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

        entries.update({

            "scroll_pos": PaletteEntry(
                mono = "white",
                foreground = "white",
                background = "white",
                foreground_high = "white",
                background_high = "white"
            ),
            "scroll_marker": PaletteEntry(
                mono = "white,bold",
                foreground = "black",
                background = "white",
                foreground_high = "black",
                background_high = "white"
            ),
            "scroll_view": PaletteEntry(
                mono = "black",
                foreground = "black",
                background = "light gray",
                foreground_high = "black",
                background_high = "light gray"
            ),
            "scroll_bg": PaletteEntry(
                mono = "black",
                foreground = "black",
                background = "dark gray",
                foreground_high = "black",
                background_high = "dark gray"
            ),

        })
        # raise Exception(entries)
        return entries


    def __getitem__(self, index):
        try:
            v = self.df[index:index]
        except IndexError:
            logger.error(traceback.format_exc(5))
            logger.error("%d, %s" %(index, self.df.index))
            raise

        return [
            v[0]
            for k, v in self.df[index:index].to_dict(ordered=True).items()
            if k in self.colnames
        ]


    def get_row(self, position):

        # index = position
        index = self.df.index[position]
        logger.debug("get_row: %d, %d" %(position, index))
        vals = self[index]
        return self.render_item(vals)

        try:
            item = self.df.get(index, "_rendered_row")
        except ValueError:
            item = None

        if not item:
            # vals = [ v[0] for k, v in self.df[index:index].to_dict(ordered=True).items() if k in self.colnames ]
            vals = self[index]
            item = self.render_item(vals)
            self.df.set(index, "_rendered_row", item)
        return item


    def __len__(self):
        return len(self.df)

    # @property
    # def focus(self):
    #     return self.walker.focus

    def render_item(self, item):
        # logger.debug("render: %s" %(item))
        row = DataTableBodyRow(self.columns, item)
        return row

    def sort_by_column(self, column):
        self.sort_by = column
        self.sort(column)

    def sort(self, column):
        # self.sort_by = column
        if isinstance(column, tuple):
            column = column[0] # FIXME: descending
        logger.debug(column)
        logger.debug("before:\n%s" %(self.df.head(5)))
        self.df.sort_columns(column)
        logger.debug("after:\n%s" %(self.df.head(5)))
        # focus = self.df.index[0]
        # logger.debug("focus: %d" %(focus))
        # self.listbox.focus_position = focus
        self.walker._modified()
        # self.listbox.focus_position = 0

    def sort_index(self):
        logger.debug("before:\n%s" %(self.df.head(10)))
        self.df.sort_index()
        logger.debug("after:\n%s" %(self.df.head(10)))
        self.walker._modified()

    def requery(self, offset=0, **kwargs):

        kwargs = {"sort": self.sort_by}
        if self.limit:
            kwargs["offset"] = offset

        colnames = self.colnames + [self.index]
        recs = list(self.query(**kwargs))
        if not recs:
            return
        data = dict(
            zip((r for r in recs[0] if r in colnames),
                [ list(z) for z in zip(*[[ v for k, v in d.items() if k in colnames] for d in recs])]
            )
        )
        # raise Exception(data["uniqueid"])
        # raise Exception(self.index)
        newdata = rc.DataFrame(
            columns = colnames,
            data = data,
            use_blist=True,
            sorted=False,
            # sorted=True,
            index = data["uniqueid"],
            index_name = (self.index)
        )
        newdata["_rendered_row"] = None

        # logger.debug("orig:\n%s" %(self.df.head(5)))
        # logger.debug("new:\n%s" %(newdata.head(5)))
        logger.debug("orig:\n%s, %s" %(self.df.index_name, sorted(self.df.index)))
        logger.debug("new:\n%s, %s" %(newdata.index_name, sorted(newdata.index)))
        self.df.append(newdata)
        if self.sort_by:
            self.sort(self.sort_by)
        # self.df.sort_index()
        # logger.debug("after sort index:\n%s, %s" %(self.df.index_name, sorted(newdata.index)))

        self.walker._modified()
        # focus = self.df.index[0]
        # logger.debug("focus: %d" %(focus))
        # self.listbox.focus_position = focus
        # if self.sort_by and not self.query_sort:
        #     self.sort(self.sort_by)


    def load_more(self, offset):
        self.requery(offset)
        # self._invalidate()
        # self.listbox._invalidate()
