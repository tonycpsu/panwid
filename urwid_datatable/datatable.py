#!/usr/bin/python
from __future__ import division
import urwid
from urwid_utils.palette import *
import raccoon as rc
from listbox import ScrollingListBox
import logging
from collections import OrderedDict
import itertools
logger = logging.getLogger("urwid_datatable")

import traceback

from datetime import datetime, date as datetype



class DataTableColumn(object):

    def __init__(self, name,
                 label=None, width=('weight', 1),
                 align="left", wrap="space",
                 padding = 1, #margin=1,
                 hide=False,
                 format_fn=None,
                 format_record = None, # format_fn is passed full row data
                 attr = None,
                 sort_key = None, sort_fn = None, sort_reverse=False,
                 footer_fn = None):

        self.name = name
        self.label = label if label else name
        self.width = width
        self.align = align
        self.wrap = wrap
        self.padding = padding
        # self.margin = margin
        self.hide = hide
        self.format_fn = format_fn
        self.format_record = format_record
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

    @property
    def width_with_padding(self):
        return self.width + 2*self.padding



    def _format(self, v):

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
        elif isinstance(v, int):
            v = "%d" %(v)
        elif isinstance(v, float):
            v = "%.03f" %(v)
        elif isinstance(v, datetime):
            v = v.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(v, datetype):
            v = v.strftime("%Y-%m-%d")

        if not isinstance(v, urwid.Widget):
            v = urwid.Text(v, align=self.align, wrap=self.wrap)
        return v

    # def cell(self, value):
    #     return DataTableCell(self, value)



class DataTableCell(urwid.WidgetWrap):

    ATTR = "table_cell"
    PADDING_ATTR = "table_row_padding"

    def __init__(self, column, value):

        self.attr = self.ATTR
        self.attr_focused = "%s focused" %(self.attr)
        self.attr_highlight = "%s highlight" %(self.attr)
        self.attr_highlight_focused = "%s focused" %(self.attr_highlight)

        self.column = column
        self.attr_map =  {}

        self.normal_attr_map = {
            None: self.attr,
        }


        self.highlight_attr_map = {
            None: self.attr_highlight,
        }

        self.normal_focus_map = {
            None: self.attr_focused,
        }

        self.highlight_focus_map = {
            None: self.attr_highlight,
            self.attr_highlight: self.attr_highlight_focused,
        }

        self.contents = self._format(value)

        self.padding = urwid.Padding(
            self.contents,
            left=self.column.padding or 0,
            right=self.column.padding or 0
        )

        # self.columns = urwid.Columns(
        #     [self.padding], dividechars=self.column.margin or 0
        # )
        # logger.info(self.columns.dividechars)

        self.attr = urwid.AttrMap(
            self.padding,
            attr_map = self.normal_attr_map,
            focus_map = self.normal_focus_map
        )
        super(DataTableCell, self).__init__(self.attr)

    def highlight(self):
        self.attr.set_attr_map(self.highlight_attr_map)
        self.attr.set_focus_map(self.highlight_focus_map)


    def unhighlight(self):
        self.attr.set_attr_map(self.normal_attr_map)
        self.attr.set_focus_map(self.normal_focus_map)

    def selectable(self):
        return False

    def keypress(self, size, key):
        return key
        # return super(DataTableCell, self).keypress(size, key)

    def _format(self, v):
        return urwid.Text(v)

class DataTableBodyCell(DataTableCell):
    ATTR = "table_row_body"
    PADDING_ATTR = "table_row_body_padding"

    def _format(self, v):
        return self.column._format(v)


class DataTableHeaderCell(DataTableCell):
    ATTR = "table_row_header"
    PADDING_ATTR = "table_row_header_padding"


class DataTableFooterCell(DataTableCell):
    ATTR = "table_row_footer"
    PADDING_ATTR = "table_row_footer_padding"


class DataTableRow(urwid.WidgetWrap):

    def __init__(self, columns, data, index=None, *args, **kwargs):

        self.data = data
        self._index = index
        self.attr = self.ATTR
        self.attr_focused = "%s focused" %(self.attr)
        self.attr_highlight = "%s highlight" %(self.attr)
        self.attr_highlight_focused = "%s focused" %(self.attr_highlight)

        self.attr_map =  {
            None: self.attr,
        }

        self.focus_map = {
            self.attr: self.attr_focused,
            self.attr_highlight: self.attr_highlight_focused
        }

        if isinstance(self.data, list):
            self.data = dict(zip([c.name for c in columns], self.data))

        cells = [self.CELL_CLASS(col, self.data[col.name])
                 for i, col in enumerate(columns)]


        self.columns = urwid.Columns([])

        for i, cell in enumerate(cells):
            col = columns[i]
            self.columns.contents.append(
                (cell, self.columns.options(col.sizing, col.width_with_padding))
            )

        self.attr = urwid.AttrMap(
            self.columns,
            attr_map = self.attr_map,
            focus_map = self.focus_map,
        )
        super(DataTableRow, self).__init__(self.attr)

    def selectable(self):
        return True

    # def keypress(self, size, key):
    #     return super(DataTableRow, self).keypress(size, key)

    def set_focus_column(self, index):
        self.columns.focus_position = index
        for i, (cell, options) in enumerate(self.columns.contents):
            if i == index:
                cell.highlight()
            else:
                cell.unhighlight()



class DataTableBodyRow(DataTableRow):

    ATTR = "table_row_body"

    CELL_CLASS = DataTableBodyCell


class DataTableHeaderRow(DataTableRow):

    signals = ['column_click']

    ATTR = "table_row_header"
    CELL_CLASS = DataTableHeaderCell

    def __init__(self, columns, *args, **kwargs):
        super(DataTableHeaderRow, self).__init__(columns, [c.name for c in columns])

    def selectable(self):
        return False


class DataTableFooterRow(DataTableRow):

    ATTR = "table_row_footer"
    CELL_CLASS = DataTableFooterCell

    def __init__(self, columns, *args, **kwargs):
        super(DataTableFooterRow, self).__init__(columns, ["footer" for n in range(len(columns))])

    def selectable(self):
        return False


class DataTableDataFrame(rc.DataFrame):

    DATA_TABLE_COLUMNS = ["_dirty", "_focus_position", "_rendered_row"]

    def __init__(self, data=None, columns=None, index=None, index_name='index', use_blist=False, sorted=None):
        if not index_name in columns:
            columns = [index_name] + columns
        super(DataTableDataFrame, self).__init__(data, columns, index, index_name, use_blist, sorted)
        for c in self.DATA_TABLE_COLUMNS:
            self[c] = None

    def append_rows(self, rows):

        # columns = [self.index_name] + self.DATA_TABLE_COLUMNS + list(self.columns)
        # raise Exception(self.columns)
        colnames = list(self.columns) #+ self.DATA_TABLE_COLUMNS
        # data = dict(
        #     zip((r for r in rows[0] if r in colnames),
        #         [ list(z) for z in zip(*[[ v for k, v in d.items() if k in colnames] for d in rows])]
        #     )
        # )

        data = dict(
            zip((colnames),
                [ list(z) for z in zip(*[[ d.get(k, None) for k in colnames] for d in rows])]
            )
        )

        # logger.info(sorted(data.keys()))
        # logger.info(sorted(colnames))
        # columns = [c for c in self.columns if not c.startswith("_")]
        # print "newdata: %s" %(columns)
        newdata = DataTableDataFrame(
            columns = list(self.columns),
            data = data,
            use_blist=True,
            sorted=False,
            # sorted=True,
            index = data[self.index_name],
            index_name = self.index_name
        )
        self.append(newdata)

    def clear(self):
        self.delete_rows(self.index)



class DataTable(urwid.WidgetWrap):


    signals = ["select", "refresh",
               # "focus", "unfocus", "row_focus", "row_unfocus",
               "drag_start", "drag_continue", "drag_stop"]

    ATTR = "table"

    columns = []

    limit = None
    index = None
    sort_by = (None, False)
    query_sort = False

    with_header = False
    with_footer = False
    with_scrollbar = None

    ui_sort = False

    def __init__(self,
                 limit=None,
                 index=None,
                 sort_by=None, query_sort=None,
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
                # logger.debug("walker next: %d, len: %d" %(position, len(self)))
                if index > len(self): raise IndexError
                return index

            def prev_position(self, position):
                index = position-1
                # index = self.table.df.index[position-1]
                # logger.debug("walker prev: %d, len: %d" %(position, len(self)))
                if index < 0: raise IndexError
                return index

            def set_focus(self, position):
                # logger.debug("walker set_focus: %d" %(position))
                self._focus = position
                self._modified()

            def __len__(self): return len(self.table)

            def _modified(self):
                self.focus_position = 0
                super(DataTableListWalker, self)._modified()


        if index: self.index = index
        if query_sort: self.query_sort = query_sort
        if sort_by:
            if isinstance(sort_by, tuple):
                column = sort_by[0]
                reverse = sort_by[1]
            else:
                column = sort_by
                reverse = False

            self.initial_sort = self.sort_by = (column, reverse)


        # raise Exception(self.initial_sort)

        if with_header: self.with_header = with_header
        if with_footer: self.with_footer = with_footer
        if with_scrollbar: self.with_scrollbar = with_scrollbar


        self.attr_map = {}
        self.focus_map = {}


        if ui_sort: self.ui_sort = ui_sort
        if limit:
            self.offset = 0
            self.limit = limit

        self.sort_column = None
        self.sort_reverse = False

        self.colnames = [c.name for c in self.columns]
        logger.info("columns: %s" %(self.colnames))
        # self.pd_columns = self.colnames + ["_rendered_row"]

        self.df = DataTableDataFrame(
            columns = self.colnames,
            use_blist=True,
            sorted=False,
            # sorted=True,
            index_name = self.index,
        )
        # self.df["_rendered_row"] = None

        self.walker = DataTableListWalker()


        self.pile = urwid.Pile([])
        self.listbox = ScrollingListBox(
            self.walker, infinite=self.limit,
            with_scrollbar = self.with_scrollbar,
            row_count_fn = (self.query_result_count
                            if self.with_scrollbar
                            else None)
            )

        urwid.connect_signal(
            self.listbox, "select",
            lambda source, selection: urwid.signals.emit_signal(
                self, "select", self, self[selection._index])
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

        self.reset()

        if self.sort_by:
            self.sort_by_column(self.sort_by)


        self.attr = urwid.AttrMap(
            self.pile,
            attr_map = self.attr_map,
            focus_map = self.focus_map
        )
        super(DataTable, self).__init__(self.attr)


    def query(self, sort=None, offset=None):
        raise Exception("query method must be overriden")

    def query_result_count(self):
        raise Exception("query_result_count method must be defined")

    @classmethod
    def get_palette_entries(cls):

        foreground_map = {
            "table_row_body": [ "light gray", "light gray" ],
            "table_row_header": [ "light gray", "white" ],
            "table_row_footer": [ "light gray", "white" ],
        }

        background_map = {
            None: [ "black", "black" ],
            "focused": [ "dark gray", "g15" ],
            "highlight": ["light gray", "g15"],
            "highlight focused": ["light gray", "g23"],
        }

        entries = dict()

        for row_attr in [
                "table_row_body", "table_row_header", "table_row_footer",
        ]:
            for suffix in [None, "focused",
                           "highlight", "highlight focused"]:
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
            "focused": ["white,bold", "yellow,bold"],
            "highlight": ["yellow,bold", "yellow,bold"],
            "highlight focused": ["yellow,bold", "yellow,bold"],
        }

        header_background_map = {
            None: ["light gray", "g40"],
            "focused": ["light gray", "g40"],
            "highlight": ["light gray", "g40"],
            "highlight focused": ["light gray", "g40"],
        }

        for prefix in ["table_row_header", "table_row_footer"]:
            for suffix in [None, "focused", "highlight", "highlight focused"]:
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
                foreground = "black",
                background = "white",
                foreground_high = "black",
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
                background_high = "g50"
            ),
            "scroll_bg": PaletteEntry(
                mono = "black",
                foreground = "light gray",
                background = "dark gray",
                foreground_high = "light gray",
                background_high = "g23"
            ),

        })
        # raise Exception(entries)
        return entries


    def __getitem__(self, index):
        logger.debug("__getitem__: %d" %(index))
        try:
            v = self.df[index:index]
        except IndexError:
            logger.error(traceback.format_exc(5))
            logger.error("%d, %s" %(index, self.df.index))
            raise

        return  OrderedDict(
            (k, v[0])
            for k, v in self.df[index:index].to_dict(ordered=True, index=True).items()
            # if k in self.colnames
        )

    def __len__(self):
        return len(self.df)


    def __getattr__(self, attr):
        if attr in ["head", "tail", "index_name"]:
            return getattr(self.df, attr)
        # elif attr == "body":
        #     return self.walker
        raise AttributeError(attr)

    def log_dump(self, n=5):
        logger.info("index: %s\n%s" %(self.index_name, self.head(n)))

    def get_row(self, position):

        # raise Exception(self.sort_by)
        if self.sort_by[1]:
            position = -position
        index = self.df.index[position]
        try:
            row = self.df.get(index, "_rendered_row")
        except:
            raise

        if self.df.get(index, "_dirty") or not row:
            # logger.debug("render %d" %(position))
            vals = self[index]
            row = self.render_item(vals)
            focus = self.df.get(index, "_focus_position")
            if focus is not None:
                row.set_focus_column(focus)
            logger.debug("render: %d, %d, %s" %(position, index, row))
            self.df.set(index, "_rendered_row", row)
            self.df.set(index, "_dirty", False)
        return row


    def render_item(self, item):
        # raise Exception(item)
        row = DataTableBodyRow(self.columns, item, index=item[self.index])
        return row


    def sort_by_column(self, col):

        logger.debug("sort_by_column: " + repr(col))
        if isinstance(col, tuple):
            col, reverse = col
        else:
            reverse = False

        if col is None:
            return

        if isinstance(col, int):
            try:
                colname = self.columns[col].name
            except IndexError:
                raise Exception("bad column number: %d" %(column))
            self.sort_column = col
        elif isinstance(col, str):
            colname = col
            try:
                self.sort_column = self.colnames.index(colname)
            except:
                raise IndexError("bad column name: %s" %(colname))
        else:
            raise Exception(col)

        self.sort_by = (colname, reverse)
        logger.debug("sort_by: %s, %s" %(colname, reverse))
        if not self.query_sort:
            self.sort(colname)

        if self.query_sort:
            self.reset()

        self.set_focus_column(self.sort_column)
        logger.info(self.sort_reverse)

    def sort(self, column):
        logger.debug(column)
        self.df.sort_columns(column)
        self.walker._modified()


    def set_focus_column(self, index):
        if self.with_header:
            self.header.set_focus_column(self.sort_column)

        if self.with_footer:
            self.footer.set_focus_column(self.sort_column)

        # logger.debug("set_focus_column: %d" %(index))
        self.df["_focus_position"] = index
        self.df["_dirty"] = True


    def cycle_sort_column(self, step):

        if self.sort_column is None:
            index = 0
        else:
            index = (self.sort_column + step)
            if index < 0: index = len(self.columns)-1
            if index > len(self.columns)-1: index = 0
        logger.debug("index: %d" %(index))
        self.sort_by_column(index)


    def sort_index(self):
        # logger.debug("before:\n%s" %(self.df.head(10)))
        self.df.sort_index()
        # logger.debug("after:\n%s" %(self.df.head(10)))
        self.walker._modified()


    def requery(self, offset=0, load_all=False, **kwargs):

        logger.debug("requery")
        kwargs = {"load_all": load_all}
        if self.query_sort:
            kwargs["sort"] = self.sort_by
        if self.limit:
            kwargs["offset"] = offset

        rows = list(self.query(**kwargs))
        logger.debug("requery: %d, %s (%d rows)" %(offset, load_all, len(rows)))
        self.append_rows(rows)


    def append_rows(self, rows):
        self.df.append_rows(rows)
        self.df["_focus_position"] = self.sort_column
        self.df["_dirty"] = True
        if not self.query_sort:
            self.sort_by_column(self.sort_by)
        # self.walker._modified()


    def add_row(self, data, sorted=True):
        # raise Exception(data)
        self.append_rows([data])

    def load_more(self, offset):
        if offset >= self.query_result_count():
            return
        self.requery(offset)

    def load_all(self):
        if len(self) >= self.query_result_count():
            return
        self.requery(len(self), load_all=True)
        self.listbox._invalidate()

    def reset(self, reset_sort=False):
        logger.debug("reset")
        self.offset = 0
        self.df.clear()
        self.requery()
        self.walker.set_focus(0)
        if reset_sort:
            self.sort_by = self.initial_sort
        # raise Exception(self.sort_by)
        # if not self.query_sort:
        #     self.sort_by_column(self.sort_by)

    # def keypress(self, size, key):
    #     if key != "enter":
    #         return key
    #     urwid.emit_signal(self, "select")

    # def mouse_event(self, size, event, button, col, row, focus):
    #     if event == 'mouse press':
    #         urwid.emit_signal(self, "click")
