#!/usr/bin/env python
from __future__ import division
import logging
logger = logging.getLogger(__name__)

# formatter = logging.Formatter("%(asctime)s [%(levelname)8s] %(message)s",
#                                     datefmt='%Y-%m-%d %H:%M:%S')
# logger.setLevel(logging.DEBUG)
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)
# console_handler.setLevel(logging.ERROR)
# logger.addHandler(console_handler)


# fh = logging.FileHandler("datatable.log")
# fh.setLevel(logging.DEBUG)
# fh.setFormatter(formatter)
# logger.addHandler(fh)

import urwid
import urwid.raw_display
import random
import string
from datetime import datetime, timedelta, date
from operator import itemgetter
import sortedcontainers
from functools import cmp_to_key
from urwid.compat import PYTHON3


DEFAULT_BORDER_WIDTH = 1
DEFAULT_BORDER_CHAR = " "
DEFAULT_BORDER_ATTR = "table_border"
DEFAULT_CELL_PADDING = 1

intersperse = lambda e,l: sum([[x, e] for x in l],[])[:-1]

class DataTableHeaderLabel(str):
    pass


class ListBoxScrollBar(urwid.WidgetWrap):


    def __init__(self, parent):
        self.parent = parent
        self.pile = urwid.Pile([])
        super(ListBoxScrollBar, self).__init__(self.pile)

    def update(self, size):

        width, height = size
        del self.pile.contents[:]
        if (len(self.parent.body)
            and self.parent.focus is not None
            and self.parent.row_count > height):
            scroll_position = int(
                self.parent.focus_position / self.parent.row_count * height
            )
        else:
            scroll_position = -1

        pos_marker = urwid.AttrMap(urwid.Text(u"\N{FULL BLOCK}"),
                                   {None: "scroll_pos"}
        )

        down_marker = urwid.AttrMap(urwid.Text(u"\N{DOWNWARDS ARROW}"),
                                   {None: "scroll_marker"}
        )

        end_marker = urwid.AttrMap(urwid.Text(u"\N{CIRCLED DOT OPERATOR}"),
                                   {None: "scroll_marker"}
        )

        bg_marker = urwid.AttrMap(urwid.Text(" "),
                                   {None: "scroll_bg"}
        )

        for i in range(height):
            if i == scroll_position:
                if self.parent.row_count == self.parent.focus_position + 1:
                    marker = end_marker
                else:
                    marker = pos_marker
            elif (i == scroll_position + 1
            and self.parent.focus is not None
            and len(self.parent.body) == self.parent.focus_position + 1
            and len(self.parent.body) != self.parent.row_count):
                marker = down_marker
            else:
                marker = bg_marker
            self.pile.contents.append(
                (marker, self.pile.options("pack"))
            )
        self._invalidate()


class DataTableRowsListWalker(urwid.listbox.ListWalker):

    def __init__(self, table, key=None):
        self.table = table
        if not key:
            key = lambda x: 0
        self.rows = sortedcontainers.SortedListWithKey(key=key)
        self.focus = 0
        super(DataTableRowsListWalker, self).__init__()

    def __getitem__(self, position):
        # raise Exception
        # logger.debug("position: %d" %(position))
        # logger.debug("data: %s" %(self.rows))
        if position < 0 or position >= len(self.rows):
            # logger.debug("IndexError: %d, %d" %(position, len(self.rows)))
            raise IndexError

        try:
            #row = DataTableBodyRow(self.table, self.rows[position])
            return self.rows[position]
        except Exception, e:
            logger.exception(e)
        # logger.debug("getitem: %s" %(row))
        return row

    def next_position(self, position):
        index = position + 1
        if position >= len(self.rows):
            raise IndexError
        focus = index
        return index

    def prev_position(self, position):
        index = position-1
        if position < 0:
            raise IndexError
        focus = index
        return index

    def set_focus(self, position):
        # logger.debug("set_focus: %s" %(position))
        self.focus = position
        self._modified()

    def set_sort_column(self, column, **kwargs):
        # logger.debug("data: %s" %(self.rows))
        field = column.name
        sort_key = column.sort_key
        index = self.table.columns.index(column)
        logger.debug("sort_by: %s, %d, %s" %(column.name, index, kwargs))
        if sort_key:
            kwargs['key'] = lambda x: sort_key(x[index].value)
        else:
            kwargs['key'] = lambda x: x[index].value

        # if column.sort_fn:
        #     kwargs['cmp'] = column.sort_fn
        # print kwargs
        if not kwargs.get("reverse", None):
            key = cmp_to_key(lambda a, b: cmp(a[index].value, b[index].value))
        else:
            key = cmp_to_key(lambda a, b: cmp(b[index].value, a[index].value))

        self.rows = sortedcontainers.SortedListWithKey(key=key)
        self._modified()

    def __len__(self):
        return len(self.rows)

    # def get_focus(self):

    #     if self.focus:
    #         return (self.rows[focus], self.focus)
    #     return (None, None)

    # def add(self, item):
    #     if self.key:
    #         self.rows.add(item)
    #     else:
    #         self.rows.append(item)
    #     self._modified()

    def clear(self):
        self.focus = 0
        self._modified()
        return self.rows.clear()

    def __getattr__(self, attr):
        # logger.debug("getattr: %s" %(attr))
        # logger.debug("len: %s" %(len(self.rows)))
        if attr in [ "append", "add", "as_list", "index", "insert", "update"]:
            rv = getattr(self.rows, attr)
            self._modified()
            return rv
        raise AttributeError(attr)




class MyListBox(urwid.ListBox):

    def keypress(self, size, key):
        if len(self.body):
            if key == 'home':
                self.focus_position = 0
                self._invalidate()
            elif key == 'end':
                self.focus_position = len(self.body)-1
                self._invalidate()
            elif key == 'r':
                self.requery()
            elif key == 'a':
                self.append()
            else:
                return super(MyListBox, self).keypress(size, key)
        else:
            return super(MyListBox, self).keypress(size, key)

    def requery(self):
        self.body.clear()
        for i in range(100):
            row = Row(random.randint(1, 1000))
            self.body.add(row)
        # self.focus_position = 0
        self._invalidate()
        loop.draw_screen()

    def append(self):
        for i in range(100):
            row = Row(random.randint(1, 1000))
            self.body.add(row)
        self.focus_position = 0
        self._invalidate()
        loop.draw_screen()


class ScrollingListBox(urwid.WidgetWrap):

    signals = ["select",
               "drag_start", "drag_continue", "drag_stop",
               "load_more"]

    def __init__(self, body,
                 infinite = False,
                 with_scrollbar=False,
                 row_count_fn = None):

        self.infinite = infinite
        self.with_scrollbar = with_scrollbar
        self.row_count_fn = row_count_fn

        self.mouse_state = 0
        self.drag_from = None
        self.drag_last = None
        self.drag_to = None
        self.requery = False

        self.listbox = urwid.ListBox(body)
        if self.with_scrollbar:
            self.scroll_bar = ListBoxScrollBar(self)
            self.columns = urwid.Columns([
                ('weight', 3, self.listbox),
                (1, self.scroll_bar),
            ])
            self.pile = urwid.Pile([
                ('weight', 1, self.columns)
             ])
            super(ScrollingListBox, self).__init__(self.pile)

        else:
            super(ScrollingListBox, self).__init__(self.listbox)

    # @property
    # def contents(self):
    #     return super(ScrollingListBox, self).contents()

    def mouse_event(self, size, event, button, col, row, focus):
        """Overrides ListBox.mouse_event method.

        Implements mouse scrolling.
        """
        if row < 0 or row >= len(self.body):
            return
        if event == 'mouse press':
            if button == 1:
                self.mouse_state = 1
                self.drag_from = self.drag_last = (col, row)
            elif button == 4:
                # for _ in range(3):
                #     self.keypress(size, 'up')
                pct = self.focus_position / len(self.body)
                self.set_focus_valign(('relative', pct - 10))
                self._invalidate()
                return True
            elif button == 5:
                # for _ in range(3):
                #     self.keypress(size, 'down')
                pct = self.focus_position / len(self.body)
                self.set_focus_valign(('relative', pct + 5))
                self._invalidate()
                return True
        elif event == 'mouse drag':
            if self.drag_from is None:
                return
            if button == 1:
                self.drag_to = (col, row)
                if self.mouse_state == 1:
                    self.mouse_state = 2
                    urwid.signals.emit_signal(
                        self, "drag_start",self, self.drag_from
                    )
                    # self.on_drag_start(self.drag_from)
                else:
                    urwid.signals.emit_signal(
                        self, "drag_continue",self,
                        self.drag_last, self.drag_to
                    )

            self.drag_last = (col, row)

        elif event == 'mouse release':
            if self.mouse_state == 2:
                self.drag_to = (col, row)
                urwid.signals.emit_signal(
                    self, "drag_stop",self, self.drag_from, self.drag_to
                )
            self.mouse_state = 0
        return self.__super.mouse_event(size, event, button, col, row, focus)


    def keypress(self, size, key):
        """Overrides ListBox.keypress method.

        Implements vim-like scrolling.
        """
        if len(self.body):
            if key == 'j':
                self._invalidate()
                self.keypress(size, 'down')
            elif key == 'k':
                self._invalidate()
                self.keypress(size, 'up')
            elif key == 'g':
                self._invalidate()
                self.focus_position = 0
            elif key == 'G':
                self.focus_position = len(self.body) - 1
                self.listbox._invalidate()
                self.set_focus_valign('bottom')
            elif key == 'home':
                self.focus_position = 0
                self.listbox._invalidate()
                return key
            elif key == 'end':
                self.focus_position = len(self.body)-1
                self._invalidate()
                return key
            elif (self.infinite
            and key in ['page down', "down"]
            and len(self.body)
            and self.focus_position == len(self.body)-1):
                self.requery = True
                self._invalidate()
            elif key == "enter":
                urwid.signals.emit_signal(self, "select", self, self.selection)
            else:
                return super(ScrollingListBox, self).keypress(size, key)
        else:
            return super(ScrollingListBox, self).keypress(size, key)

    @property
    def selection(self):

        if len(self.body):
            return self.body[self.focus_position]


    def render(self, size, focus=False):
        maxcol, maxrow = size
        if self.requery and "bottom" in self.ends_visible(
                (maxcol, maxrow) ):
            self.requery = False
            urwid.signals.emit_signal(
                self, "load_more", len(self.body))
        # (offset, inset) = self.listbox.get_focus_offset_inset(size)
        # (middle, top, bottom) = self.listbox.calculate_visible(size, focus)
        if self.with_scrollbar:
            self.scroll_bar.update(size)
        return super(ScrollingListBox, self).render( (maxcol, maxrow), focus)


    def disable(self):
        self.selectable = lambda: False

    def enable(self):
        self.selectable = lambda: True

    # @property
    # def focus_position(self):
    #     return self.listbox.focus_position
    #     if not len(self.listbox.body):
    #         raise Eception
    #     if len(self.listbox.body):
    #         return self.listbox.focus_position
    #     return None

    # @focus_position.setter
    # def focus_position(self, value):
    #     self.listbox.focus_position = value
    #     self.listbox._invalidate()

    def __getattr__(self, attr):
        if attr in ["ends_visible", "set_focus", "body"]:
            return getattr(self.listbox, attr)
        # elif attr == "body":
        #     return self.walker
        raise AttributeError(attr)

    def __setattr__(self, attr, value):
        if attr in ["focus_position"]:
            rv = setattr(self.listbox, attr, value)
            self.listbox._invalidate()
            return
        return super(ScrollingListBox, self).__setattr__(attr, value)
        raise AttributeError(attr)

    def __getattribute__(self, attr):
        if attr == "focus_position":
            # print "focus_position"
            # print len(self.listbox.body)
            return urwid.ListBox.__getattribute__(self.listbox, "focus_position")
        else:
            return super(ScrollingListBox, self).__getattribute__(attr)

    @property
    def row_count(self):
        if self.row_count_fn:
            return self.row_count_fn()
        return len(self.body)

    # @focus_position.setter
    # def focus_position(self, value):
    #     self.listbox.focus_position = value

    # @focus_position.setter
    # def set_focus(self, value):
    #     self.listbox.focus_position = value



class DataTableColumn(object):

    def __init__(self, name, label=None, width=('weight', 1),
                 align="left", wrap="space", padding = None,
                 format_fn=None, attr = None,
                 sort_key = None, sort_fn = None, sort_reverse=False,
                 footer_fn = None,
                 attr_map = None, focus_map = None):

        self.name = name
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
        self.attr_map = attr_map if attr_map else {}
        self.focus_map = focus_map if focus_map else {}
        if isinstance(self.width, tuple):
            if self.width[0] != "weight":
                raise Exception(
                    "Column width %s not supported" %(col.width[0])
                )
            self.sizing, self.width = self.width
        else:
            self.sizing = "given"


    def _format(self, v):

        if isinstance(v, DataTableHeaderLabel):
            return urwid.Text(v, align=self.align, wrap=self.wrap)
        else:
            # First, call the format function for the column, if there is one
            if self.format_fn:
                try:
                    v = self.format_fn(v)
                except TypeError, e:
                    logger.info("format function raised exception: %s" %e)
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
        elif isinstance(v, date):
            v = v.strftime("%Y-%m-%d")

        if not isinstance(v, urwid.Widget):
            v = urwid.Text(v, align=self.align, wrap=self.wrap)
        return v

class DataTableCell(urwid.WidgetWrap):

    # attr_map = { None: "table_content" }
    # focus_map = { "table_content": "table_content focused" }

    signals = ["click", "select"]

    def __init__(self, table, column, row, value,
                 attr_map = None, focus_map = None,
                 *args, **kwargs):

        self.table = table
        self.column = column
        self.row = row
        self.value = value
        self.contents = self.column._format(self.value)

        self.attr_map = {}
        self.focus_map = {}

        if table.attr_map:
            self.attr_map.update(table.attr_map)
        if column.attr_map:
            self.attr_map.update(column.attr_map)
        if row.attr_map:
            self.attr_map.update(row.attr_map)
        if column.attr and isinstance(row.data, dict):
            a = row.data.get(column.attr, {})
            if isinstance(a, basestring):
                a = {None: a}
            self.attr_map.update(a)

        if attr_map:
            self.attr_map.update(attr_map)

        # if table.focus_map:
        #     self.attr_map.update(table.focus_map)
        if column.focus_map:
            self.focus_map.update(column.focus_map)
        if row.focus_map:
            self.focus_map.update(row.focus_map)
        if focus_map:
            self.focus_map.update(focus_map)

        # print "[%s] [%s]" %(self.attr_map, self.focus_map)

        # print self.focus_map
        padding = (self.column.padding
                   if self.column.padding
                   else self.table.padding)

        self.padding = urwid.Padding(self.contents,
                                     left=padding, right=padding)

        self.attr = urwid.AttrMap(self.padding,
                                  attr_map = self.attr_map,#)
                                  focus_map = self.focus_map)

        self.orig_attr_map = self.attr.get_attr_map()
        self.orig_focus_map = self.attr.get_focus_map()

        self.highlight_attr_map = self.attr.get_attr_map()
        for k in self.highlight_attr_map.keys():
            self.highlight_attr_map[k] = self.highlight_attr_map[k] + " column_focused"

        self.highlight_focus_map = self.attr.get_attr_map()
        for k in self.highlight_focus_map.keys():
            self.highlight_focus_map[k] = self.highlight_focus_map[k] + " column_focused focused"

        super(DataTableCell, self).__init__(self.attr)


    def selectable(self):
        if isinstance(self.value, DataTableHeaderLabel):
            return True
        return False

    def keypress(self, size, key):
        return super(DataTableCell, self).keypress(size, key)

    def highlight(self):
        self.attr.set_attr_map(self.highlight_attr_map)
        self.attr.set_focus_map(self.highlight_focus_map)

        # print self.attr_map

    def unhighlight(self):
        self.attr.set_attr_map(self.orig_attr_map)
        self.attr.set_focus_map(self.orig_focus_map)

    def keypress(self, size, key):
        if key != "enter":
            return key
        urwid.emit_signal(self, "select")

    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            urwid.emit_signal(self, "click")



class HeaderColumns(urwid.Columns):

    def __init__(self, contents, header = None):

        self.selected_column = None
        super(HeaderColumns, self).__init__(contents)


class BodyColumns(urwid.Columns):

    def __init__(self, contents, header = None):

        self.header = header
        super(BodyColumns, self).__init__(contents)


    @property
    def selected_column(self):

        # print "get focus_position"
        return self.header.selected_column

    @selected_column.setter
    def selected_column(self, value):
        return


class DataTableRow(urwid.WidgetWrap):

    column_class = urwid.Columns

    # attr_map = {}
    # focus_map = {}

    # border_attr_map = { None: "table_border" }
    # border_focus_map = { None: "table_border focused" }

    decorate = True

    def __init__(self, table, data,
                 header = None,
                 cell_click = None, cell_select = None,
                 border_attr_map = None, border_focus_map = None,
                 **kwargs):

        self.table = table
        self.data = data
        self.header = header
        self.cell_click = cell_click
        self.cell_select = cell_select
        # self.selected_column = None
        self.contents = []
        self._values = dict()

        if self.decorate:
            if table.attr_map:
                self.attr_map.update(table.attr_map)
            if table.focus_map:
                self.focus_map.update(table.focus_map)


        if border_attr_map:
            self.border_attr_map = border_attr_map
        else:
            self.border_attr_map = self.attr_map

        if border_focus_map:
            self.border_focus_map = border_focus_map
        else:
            self.border_focus_map = self.focus_map

        for i, col in enumerate(self.table.columns):
            l = list()
            if col.sizing == "weight":
                l += [col.sizing, col.width]
            else:
                l.append(col.width)

            if isinstance(self.data, (list, tuple)):
                val = self.data[i]
            elif isinstance(data, dict):
                val = data.get(col.name, None)
                # details = data.get(c.details, None)
            else:
                raise Exception(data)

            cell = DataTableCell(self.table, col, self, val)
            if self.cell_click:
                urwid.connect_signal(cell, 'click', self.cell_click, i*2)
            if self.cell_select:
                urwid.connect_signal(cell, 'select', self.cell_select, i*2)

            l.append(cell)
            self.contents.append(tuple(l))

        border_width = DEFAULT_BORDER_WIDTH
        border_char = DEFAULT_BORDER_CHAR
        border_attr = DEFAULT_BORDER_ATTR

        if isinstance(table.border, tuple):

            try:
                border_width, border_char, border_attr = table.border
            except IndexError:
                try:
                    border_width, border_char = table.border
                except Indexerror:
                    border_width = table.border

        elif isinstance(table.border, int):
            border_width = table.border

        else:
            raise Exception("Invalid border specification: %s" %(table.border))

        if self.header:
            self.row = self.column_class(self.contents, header = self.header)
        else:
            self.row = self.column_class(self.contents)

        self.row.contents = intersperse(
            (urwid.AttrMap(urwid.Divider(border_char),
                          attr_map = self.border_attr_map,
                          focus_map = self.border_focus_map),
             ('given', border_width, False)),
            self.row.contents)


        self.attr = urwid.AttrMap(self.row,
                                  attr_map = self.attr_map,
                                  focus_map = self.focus_map)

        super(DataTableRow, self).__init__(self.attr)


    # @property
    # def attr_map(self):
    #     return self.attr.attr_map

    # @attr_map.setter
    # def set_attr_map(self, attr_map):
    #     self.attr.set_attr_map(attr_map)

    # @property
    # def focus_map(self):
    #     return self.attr.focus_map

    # @focus_map.setter
    # def set_focus_map(self, focus_map):
    #     self.attr.set_focus_map(focus_map)
    def set_attr_map(self, attr_map):
        self.attr.set_attr_map(attr_map)

    def set_focus_map(self, focus_map):
        self.attr.set_focus_map(focus_map)

    def __len__(self): return len(self.contents)

    def __getitem__(self, i): return self.row.contents[i*2][0]

    def __delitem__(self, i): del self.row.contents[i*2]

    def __setitem__(self, i, v):

        self.row.contents[i*2] = (
            v, self.row.options(self.table.columns[i].sizing,
                                self.table.columns[i].width)
        )

    def selectable(self):
        return True

    def keypress(self, size, key):
        return super(DataTableRow, self).keypress(size, key)

    # def focus_position(self):
    #     return self.table.header.focus_position


    @property
    def focus_position(self):
        return self.row.focus_position

    @focus_position.setter
    def focus_position(self, value):
        self.row.focus_position = value

    @property
    def selected_column(self):
        return self.row.selected_column

    @selected_column.setter
    def selected_column(self, value):
        self.row.selected_column = value


    # def cycle_focus(self, step):

    #     if not self.selected_column:
    #         self.selected_column = -1
    #     index = (self.selected_column + 2*step)
    #     if index < 0:
    #         index = len(self.row.contents)-1
    #     if index > len(self.row.contents)-1:
    #         index = 0

    #     self.focus_position = index


    def highlight_column(self, index):
        self.selected_column = index
        for i in range(0, len(self.row.contents), 2):
            if i == index:
                self.row[i].highlight()
            else:
                self.row[i].unhighlight()

    def cycle_columns(self, step):

        if self.selected_column is None:
            index = 0
        else:
            index = (self.row.selected_column + 2*step)
            if index < 0:
                index = len(self.row.contents)-1
            if index > len(self.row.contents)-1:
                index = 0

        # print "index: %s" %(index)
        self.highlight_column(index)


class DataTableBodyRow(DataTableRow):


    column_class = BodyColumns

    attr_map = { None: "table_row" }
    focus_map = {
        None: "table_row focused",
        "table_row": "table_row focused",
        # "table_row column_focused": "table_row column_focused focused"
    }
    # focus_map = {}


class DataTableHeaderRow(DataTableRow):

    signals = ['column_click']

    column_class = HeaderColumns

    border_attr_map = { None: "table_border" }
    border_focus_map = { None: "table_border focused" }


    def __init__(self, table, *args, **kwargs):

        self.attr_map = {}
        self.focus_map = {}

        self.attr_map = { None: "table_header" }
        self.focus_map = { None: "table_header focused" }

        self.decorate = False

        self.table = table
        self.contents = [ DataTableHeaderLabel(x.label) for x in self.table.columns ]
        if not self.table.ui_sort:
            self.selectable = lambda: False

        super(DataTableHeaderRow, self).__init__(
            self.table,
            self.contents,
            border_attr_map = self.border_attr_map,
            border_focus_map = self.border_focus_map,
            cell_click = self.header_clicked,
            cell_select = self.header_clicked,
            *args, **kwargs)

    def header_clicked(self, index):
        # print "click: %d" %(index)
        # index = [x[0] for x in self.contents].index(self.focus) / 2
        urwid.emit_signal(self, "column_click", index)


class DataTableFooterRow(DataTableRow):

    # column_class = HeaderColumns

    border_attr_map = { None: "table_border" }
    border_focus_map = { None: "table_border focused" }

    def __init__(self, table, *args, **kwargs):

        self.attr_map = {}
        self.focus_map = {}

        self.attr_map = { None: "table_footer" }
        self.focus_map = { None: "table_footer focused" }

        self.table = table
        self.contents = [ DataTableHeaderLabel("")
                          for i in range(len(self.table.columns)) ]


        super(DataTableFooterRow, self).__init__(
            self.table,
            self.contents,
            border_attr_map = self.border_attr_map,
            border_focus_map = self.border_focus_map,
            *args, **kwargs)

    def selectable(self):
        return False

    def update(self):

        columns = self.table.columns

        for i, col in enumerate(columns):
            if not col.footer_fn:
                continue
            try:
                # col_data = [ r.data.get(col.name, None)
                #              for r in self.table.body ]
                data = [ r.data for r in self.table.body ]
                footer_content = col.footer_fn(data, col.name)
                if not isinstance(footer_content, urwid.Widget):
                    footer_content = col._format(footer_content)
                self[i] = footer_content
            except Exception, e:
                logger.exception(e)


class DataTable(urwid.WidgetWrap):

    signals = ["select", "refresh",
               "focus", "unfocus", "row_focus", "row_unfocus",
               "drag_start", "drag_continue", "drag_stop"]

    columns = []
    attr_map = {}
    focus_map = {}
    # attr_map = { None: "table" }
    # focus_map = { None: "table focused" }
    border = (DEFAULT_BORDER_WIDTH, DEFAULT_BORDER_CHAR, DEFAULT_BORDER_ATTR)
    padding = DEFAULT_CELL_PADDING
    with_header = True
    with_footer = False
    with_scrollbar = False
    sort_field = None
    initial_sort = None
    query_sort = False
    ui_sort = False
    limit = None

    def __init__(self, border=None, padding=None,
                 with_header=True, with_footer=False, with_scrollbar=False,
                 initial_sort = None, query_sort = None, ui_sort = False,
                 limit = None):

        if border: self.border = border
        if padding: self.padding = padding
        if with_header: self.with_header = with_header
        if with_footer: self.with_footer = with_footer
        if with_scrollbar: self.with_scrollbar = with_scrollbar
        if initial_sort:
            self.initial_sort = initial_sort

        if initial_sort: self.initial_sort = initial_sort
        #     self.sort_field = initial_sort
        # else:
        #     self.sort_field = self.initial_sort

        # self.sort_field = self.column_label_to_field(self.sort_field)

        if query_sort: self.query_sort = query_sort
        if ui_sort: self.ui_sort = ui_sort
        if limit: self.limit = limit

        # if not self.query_sort:
        #     self.data = SortedListWithKey()
        # else:
        #     self.data = list()

        self.data = sortedcontainers.SortedListWithKey()

        self.walker = DataTableRowsListWalker(self)
        self.listbox = ScrollingListBox(
            self.walker, infinite=self.limit,
            with_scrollbar = self.with_scrollbar,
            row_count_fn = (self.query_result_count
                            if self.with_scrollbar
                            else None)
            )

        self.selected_column = None
        self.sort_reverse = False

        urwid.connect_signal(
            self.listbox, "select",
            lambda source, selection: urwid.signals.emit_signal(
                self, "select", self, selection)
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


        self.pile = urwid.Pile([])

        self.header = DataTableHeaderRow(self)
        if self.with_header:
            self.pile.contents.append(
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

        # self.pile = urwid.Pile([
        #     ('pack', self.header),
        #     ('weight', 1, self.listbox)
        # ])

        if self.with_footer:
            self.footer = DataTableFooterRow(self)
            self.pile.contents.append(
                (self.footer, self.pile.options('pack'))
             )


        self.attr = urwid.AttrMap(
            self.pile,
            attr_map = self.attr_map
        )
        super(DataTable, self).__init__(self.attr)

        if self.initial_sort:
            logger.debug("initial sort: %s" %(self.initial_sort))
            self.sort_by_column(self.initial_sort, toggle=False)
        self.requery()



    # @property
    # def selected_column(self):
    #     return self.header.focus_position

    # @property
    # def data(self):

    #     return self._data

    def __getattr__(self, attr):
        if attr == ["body"]:
            return self.walker
        raise AttributeError(attr)


    @property
    def focus_position(self):
        return self.listbox.focus_position

    @focus_position.setter
    def focus_position(self, value):
        self.listbox.focus_position = value

    @property
    def body(self):
        return self.listbox.body

    @property
    def selection(self):
        return self.body[self.focus_position]

    def highlight_column(self, index):
        self.header.highlight_column(index)
        for row in self.listbox.body:
            row.highlight_column(index)

    def column_label_to_field(self, label):
        for i, col in enumerate(self.columns):
            if col.label == label:
                return col.name


    def sort_by_column(self, index=None, reverse=None, toggle = False):

        if index is None:
            index = self.sort_field

        if index is None:
            return


        if isinstance(index, basestring):
            sort_field = index
            for i, col in enumerate(self.columns):
                if col.name == sort_field:
                    index = i*2
                    break
        else:
            sort_field = self.columns[index//2].name

        column = self.columns[index//2]

        if not isinstance(index, int):
            raise Exception("invalid column index: %s" %(index))

        # logger.warning("sort: %s, %s" %(self.sort_field, self.sort_reverse))
        # raise Exception("%s, %s" %(index//2, self.selected_column))
        # print "%s, %s" %(index//2, self.selected_column)
        # print "%s, %s" %(sort_field, self.sort_field)

        if reverse is not None:
            self.sort_reverse = reverse ^ self.columns[index//2].sort_reverse
        elif not toggle or sort_field != self.sort_field:
            self.sort_reverse = self.columns[index//2].sort_reverse
        else:
            self.sort_reverse = not self.sort_reverse
        # print "sort: %s, %s" %(self.sort_field, self.sort_reverse)
        self.sort_field = sort_field
        # print self.sort_reverse
        self.selected_column = index
        # if self.query_sort:
        #     self.requery()
        # else:
        # if not self.query_sort:
        #self.sort_by(index//2, reverse = self.sort_reverse)
        # self.sort_by(index//2, reverse = self.sort_reverse)
        self.walker.set_sort_column(column, reverse = self.sort_reverse)
        self.requery()
        # if len(self.listbox.body):
        #     self.listbox.focus_position = 0

    # def cycle_columns(self, step):

    #     index = (self.header.focus_position + 2*step)
    #     if index < 0:
    #         index = len(self.row.contents)-1
    #     if index > len(self.row.contents)-1:
    #         index = 0
    #     self.highlight_column(index)
    #     raise Exception(self.selected_column)


    def sort_by(self, index, **kwargs):
        self.walker.set_sort_column(index)
        self.requery()

    def sort_by2(self, index, **kwargs):

        sort_key = self.columns[index].sort_key

        if sort_key:
            kwargs['key'] = lambda x: sort_key(x[index].value)
        else:
            kwargs['key'] = lambda x: x[index].value

        if self.columns[index].sort_fn:
            kwargs['cmp'] = self.columns[index].sort_fn
        # print kwargs
        if not kwargs.get("reverse", None):
            key = cmp_to_key(lambda a, b: cmp(a[index].value, b[index].value))
        else:
            key = cmp_to_key(lambda a, b: cmp(b[index].value, a[index].value))

        # self.body.clear()
        # body = SimpleMonitoredSortedFocusListWalker([], key=key)
        self.walker.set_key(key)
        # l = self.body.as_list()
        # self.clear()
        # self.body._key=key
        # self.body.update(l)
        # self.refresh()
        # self.listbox.body.sort(**kwargs)

    def selectable(self):
        return True


    def cycle_index(self, step=1):
        self.header.cycle_columns(step)
        self.sort_by_column(self.header.row.selected_column)

    # def keypress(self, size, key):

    #     if self.ui_sort and key in [ "<", ">" ]:

    #         self.header.cycle_columns( -1 if key == "<" else 1 )
    #         self.sort_by_column(self.header.row.selected_column)
    #     else:
    #         return super(DataTable, self).keypress(size, key)
    #         # return key

    def add_row(self, data, position=None):
    # def add_row(self, data):
        # index = self.data.bisect(data)

        # self.data.insert(index, data)
        # print data
        row = DataTableBodyRow(self, data, header = self.header.row)
        # if position is None:
        # self.body.add(row)
        if not position:
            self.listbox.body.add(row)
        else:
            self.listbox.body.insert(position, row)

        #     position = len(self.listbox.body)-1
        # else:
        #     self.listbox.body.insert(position, row)

        # item = self.listbox.body[position]
        # if keep_sorted:
        #     self.sort_by_column()
        return row


    def query(self, sort=None, offset=None):
        pass

    def query_result_count(self):
        raise Exception("query_result_count method must be defined")


    # def refresh(self, offset=0):

    #     if not offset:
    #         self.clear()

    #     for r in self.data[offset:]:
    #         if isinstance(r, (tuple, list)):
    #             r = dict(zip( [c.name for c in self.columns], r))
    #         self.add_row(r)

    #     if self.with_footer:
    #         self.footer.update()

    #     # if self.sort_field:
    #     #     self.sort_by_column(self.initial_sort, toggle = False)
    #     urwid.emit_signal(self, "refresh", self)

    # def keypress(self, size, key):

    #     if key == "enter":
    #         logger.debug("%d, %d" %(len(self.listbox.body), self.listbox.focus_position))
    #     else:
    #         return super(DataTable, self).keypress(size, key)


    def requery(self, offset=0, **kwargs):

        orig_offset = offset

        kwargs = {"sort": (self.sort_field, self.sort_reverse)}
        if self.limit:
            kwargs["offset"] = offset

        # if len(self.body):
        #     logger.debug("setting focus_position = 0")
        #     self.listbox.focus_position = 0
        if not offset:
            logger.debug("clearing")
            self.clear()
        logger.debug(kwargs)
        for r in self.query(**kwargs):
            if isinstance(r, (tuple, list)):
                r = dict(zip( [c.name for c in self.columns], r))
            # print "adding: %s" %(r)
            self.add_row(r)
        logger.debug("body length: %d" %(len(self.body)))
        # self.listbox.focus_position = 0
        # logger.debug(self.listbox.focus_position)

        # self.refresh(offset)
        # if offset and orig_offset < len(self.body):
        #     # self.listbox.set_focus(orig_offset)
        #     self.listbox.focus_position = orig_offset
        # self._invalidate()
        # self.listbox._invalidate()
        # if hasattr(self.listbox, "pile"):
        #     self.listbox.pile._invalidate()
        # self.listbox.listbox._invalidate()
        if self.selected_column is not None:
            self.highlight_column(self.selected_column)
        urwid.emit_signal(self, "refresh", self)


    def load_more(self, offset):

        self.requery(offset)
        self._invalidate()
        self.listbox._invalidate()
        # print self.selected_column


    def clear(self):
        # del self.data[:]
        # del self.listbox.body[:]
        self.listbox.body.clear()
        # while len(self.body):
        #     self.body.pop()
        # self.body.update([])
        # pass



def main():

    import os

    from urwid_utils.palette import PaletteEntry, Palette

    loop = None

    screen = urwid.raw_display.Screen()
    screen.set_terminal_properties(256)

    foreground_map = {
        "table_row": [ "light gray", "light gray" ],
        "red": [ "light red", "#a00" ],
        "green": [ "light green", "#0a0" ],
        "blue": [ "light blue", "#00a" ],
        "yellow": [ "yellow", "#aa0" ],
    }

    background_map = {
        None: [ "black", "black" ],
        "focused": [ "dark gray", "g7" ],
        "column_focused": [ "dark gray", "g7" ],
        "column_focused focused": [ "dark gray", "g11" ],
    }

    entries = dict()
    FOCUS_MAP = dict()

    for prefix in ["table_row", "red", "yellow", "green", "blue"]:
        for suffix in [None, "focused", "column_focused", "column_focused focused"]:
            if suffix:
                attr = ' '.join([prefix, suffix])
            else:
                attr = prefix
            entries[attr] = PaletteEntry(
                mono = "white",
                foreground = foreground_map[prefix][0],
                background = background_map[suffix][0],
                foreground_high = foreground_map[prefix][1],
                background_high = background_map[suffix][1],
            )

        FOCUS_MAP[prefix] = "%s focused" %(prefix)
        # FOCUS_MAP["%s column_focused" %(prefix)] = "%s column_focused focused" %(prefix)


    # raise Exception(FOCUS_MAP)
    header_foreground_map = {
        None: ["black,bold", "g7,bold"],
        "focused": ["white,bold", "white,bold"],
        "column_focused": ["yellow,bold", "yellow,bold"],
        "column_focused focused": ["yellow,bold", "yellow,bold"],

    }

    header_background_map = {
        None: ["light gray", "g40"],
        "focused": ["light gray", "g40"],
        "column_focused": ["white", "g40"],
        "column_focused focused": ["light gray", "g40"],
    }

    for prefix in ["table_header", "table_footer"]:
        for suffix in [None, "focused", "column_focused", "column_focused focused"]:
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
            mono = "white",
            foreground = "black",
            background = "white",
            foreground_high = "black",
            background_high = "white"
        ),
        "scroll_bg": PaletteEntry(
            mono = "white,bold",
            foreground = "black",
            background = "dark gray",
            foreground_high = "black",
            background_high = "dark gray"
        ),

    })


    palette = Palette("default", **entries)



    def avg(data, attr):
        values = [ d[attr] for d in data ]
        return sum(values)/len(values)

    class ExampleDataTable(DataTable):

        focus_map = FOCUS_MAP
        query_sort = True
        with_footer = True
        ui_sort = True
        num_rows = None

        columns = [
            DataTableColumn(
                "foo", width=5,
            ),
            DataTableColumn("bar", width=12, align="right",
                            footer_fn = avg, sort_reverse=True),
            DataTableColumn("baz", width=('weight', 1), attr="baz_attr"),
        ]


        def __init__(self, num_rows = 1000, *args, **kwargs):
            self.num_rows = num_rows
            self.query_data = [
                self.random_row() for i in range(self.num_rows)
            ]


            super(ExampleDataTable, self).__init__(*args, **kwargs)

        def random_row(self):
            return dict(foo=random.randint(1, 100),
                        bar =random.uniform(0, 1000),
                        baz =''.join(random.choice(
                            string.ascii_uppercase
                            + string.lowercase
                            + string.digits + ' ' * 20
                        ) for _ in range(32))
            )

        def keypress(self, size, key):
            if self.ui_sort and key in [ "shift left", "shift right" ]:
                self.cycle_index( -1 if key == "shift left" else 1 )

            elif self.ui_sort and key == "shift up":
                self.sort_by_column(reverse=True)
            elif self.ui_sort and key == "shift down":
                self.sort_by_column(reverse=False)
            elif self.ui_sort and key == "ctrl s":
                self.sort_by_column(toggle=True)
            elif key == "a":
                self.add_row(self.random_row())
            # elif key == "A":
            #     self.add_row(self.random_row(), keep_sorted=False)
            elif key == "r":
                self.requery()
            else:
                return super(ExampleDataTable, self).keypress(size, key)

        def query(self, sort=(None, None), offset=None):

            sort_field, sort_reverse = sort
            if sort_field:
                kwargs = {}
                kwargs["reverse"] = sort_reverse
                kwargs["key"] = itemgetter(sort_field)
                logger.debug("query: %s" %(kwargs))
                self.query_data.sort(**kwargs)
                logger.debug("s" %(self.query_data))
            # print l[0]
            if offset is not None:
                start = offset
                end = offset + self.limit
                r = self.query_data[start:end]
                # print "%s, %s, %d, %d" %(sort_field, sort_reverse, start, end)
            else:
                r = self.query_data

            for d in r:
                yield d

        def query_result_count(self):
            return self.num_rows


    class MainView(urwid.WidgetWrap):

        def __init__(self):

            self.tables = list()

            self.tables.append(
                ExampleDataTable(initial_sort="foo", limit=10, num_rows=100,
                                 with_scrollbar=True)
            )

            self.tables.append(
                ExampleDataTable(initial_sort="bar", limit=20, num_rows=100,
                                 with_scrollbar=True)
            )

            self.tables.append(
                ExampleDataTable(initial_sort="baz", ui_sort=False,
                                 num_rows=1000)
            )

            self.tables.append(
                ExampleDataTable(initial_sort=None, query_sort=False,
                                 limit = 20,
                                 num_rows=1000)
            )

            for t in self.tables:
                urwid.connect_signal(
                    t, "refresh", lambda source: loop.draw_screen()
                )

            self.grid_flow = urwid.GridFlow(
                [urwid.BoxAdapter(t, 40) for t in self.tables], 55, 1, 1, "left"
            )
            #     [ ('weight', 1, urwid.LineBox(t)) for t in self.tables ]
            # )


            self.pile = urwid.Pile([
                ('weight', 1, urwid.Filler(self.grid_flow))

            ])
            # w = urwid.WidgetPlaceholder(self.pile)
            super(MainView,self).__init__(self.pile)


    def parse_list(option, opt, value, parser):
        setattr(parser.values, option.dest, value.split(','))

    main_view = MainView()

    def global_input(key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        else:
            return False


    loop = urwid.MainLoop(main_view,
                          palette,
                          screen=screen,
                          pop_ups=True,
                          unhandled_input=global_input,
                          event_loop=urwid.TwistedEventLoop())

    old_signal_keys = screen.tty_signal_keys()
    l = list(old_signal_keys)
    l[0] = 'undefined'
    l[1] = 'undefined'
    l[2] = 'undefined'
    l[3] = 'undefined'
    l[4] = 'undefined'
    screen.tty_signal_keys(*l)
    print screen.tty_signal_keys()
    try:
        loop.run()
    finally:
        screen.tty_signal_keys(*old_signal_keys)


if __name__ == "__main__":
    main()

