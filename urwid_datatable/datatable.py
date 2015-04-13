import logging
logger = logging.getLogger(__name__)

import urwid
from collections import namedtuple
from collections import MutableSequence
import threading

intersperse = lambda e,l: sum([[x, e] for x in l],[])[:-1]

class SimpleButton(urwid.WidgetWrap):
    """A clickable, selectable text widget."""

    signals = ['click']

    def __init__(self, label, attr=None, align="left",
                 callback=None, data=None,
                 attr_map = None,
                 focus_map = None):
        self.l = label
        self.t = urwid.Text( (attr, self.l), align)
        am = urwid.AttrMap(self.t, attr_map=attr_map, focus_map=focus_map)
        super(SimpleButton, self).__init__(am)
        if callback is not None:
            urwid.connect_signal(self, 'click', callback, data)

    def set_text_attr(self, attr):
        self.t.set_text((attr, self.l))

    @property
    def label(self):
        return self.l

    def keypress(self, size, key):
        if urwid.command_map[key] != 'activate':
            return key
        urwid.emit_signal(self, 'click')

    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            urwid.emit_signal(self, 'click')

    def selectable(self):
        return True


class DataTableColumnDef(object):

    def __init__(self, label, field=None, attr=None, details=None,
                 width=1, padding=1,
                 sizing="given", align='left', wrap = "space",
                 sort_key=None, sort_fn=None, format_fn=None,
                 attr_map = None, focus_map = None):

        self.label = label
        if field:
            self.field = field
        else:
            self.field = label

        self.attr = attr
        self.details = details

        self.width = width
        self.padding = padding
        self.sizing = sizing
        self.align = align
        self.wrap = wrap
        self.sort_key = sort_key
        self.sort_fn = sort_fn
        if format_fn:
            self.format_fn = format_fn
        else:
            self.format_fn = self.default_format
        self.attr_map = attr_map
        self.focus_map = focus_map

    def default_format(self, v):
        if v is None:
            v = ""
        elif isinstance(v, int):
            v = "%d" %(v)
        if isinstance(v, float):
            v = "%.03f" %(v)
        return urwid.Text(v, align=self.align, wrap=self.wrap)



class ScrollingListBox(urwid.ListBox):

    signals = ["select",
               "drag_start", "drag_continue", "drag_stop",
               "load_more"]

    def __init__(self, body):
        super(ScrollingListBox, self).__init__(body)
        self.mouse_state = 0
        self.drag_from = None
        self.drag_last = None
        self.drag_to = None
        self.requery = False


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
                for _ in range(3):
                    self.keypress(size, 'up')
                return True
            elif button == 5:
                for _ in range(3):
                    self.keypress(size, 'down')
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
                self.keypress(size, 'down')
            elif key == 'k':
                self.keypress(size, 'up')
            elif key == 'g':
                self.set_focus(0)
            elif key == 'G':
                self.set_focus(len(self.body) - 1)
                self.set_focus_valign('bottom')
            elif key == 'home':
                self.focus_position = 0
            elif key == 'end':
                self.focus_position = len(self.body)-1
            elif key in ['page down', "down"] and self.focus_position == len(self.body)-1:
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

        return super(ScrollingListBox, self).render( (maxcol, maxrow), focus)


    def disable(self):
        self.selectable = lambda: False

    def enable(self):
        self.selectable = lambda: True


class DataTableCell(urwid.WidgetWrap):

    def __init__(self, column, value, details=None,
                 expand_details = False,
                 attr_map=None, focus_map=None):

        def value_format(v):
            if isinstance(v, int):
                v = "%d" %(v)
            elif v is None:
                v = ""
            return v

        self.column = column
        self._value = value
        self.expand_details = expand_details
        self.details = details
        self.details_contents = None

        if value is not None:

            try:
                self.contents = column.format_fn(value)
            except Exception, e:
                logger.warn("format function raised exception: %s" %e)
                self.contents = ""
                # raise Exception("can't format value in column %s: %s" %(
                #     self.column.label,
                #     e))
        else:
            self.contents = urwid.Text("")


        if not isinstance(self.contents, urwid.Widget):
            if not isinstance(self.contents, basestring):
                self.contents = str(self.contents)
            self.contents = urwid.Text(self.contents,
                                  align=self.column.align,
                                  wrap=self.column.wrap)


        self.padding = urwid.Padding(self.contents,
                                left=column.padding, right=column.padding
        )

        if self.details:
            self.details_contents = urwid.Text(self.details)
            self.details_padding = urwid.Padding(
                self.details_contents,
                left=column.padding, right=column.padding
            )




        # cell_attr_map = {}
        # if attr_map:
        #     cell_attr_map = attr_map
        # elif self.column.attr_map:
        #     cell_attr_map = self.column.attr_map

        # cell_focus_map = {}
        # if focus_map:
        #     cell_focus_map = focus_map
        # elif self.column.focus_map:
        #     cell_focus_map = self.column.focus_map

        # print "focus_map: %s" %(focus_map)
        self.pile = urwid.Pile([self.padding])
        self.attr = urwid.AttrMap(
            self.pile,
            attr_map = attr_map,
            focus_map = focus_map)
        super(DataTableCell, self).__init__(self.attr)
        if self.expand_details:
            self.open_details()


    def open_details(self):

        if not self.details or len(self.pile.contents) > 1:
            return
        # self.pile.contents.insert(
        #     0,
        #     (urwid.Divider(u"\u2500"), self.pile.options("pack"))
        # )


        self.pile.contents += [
            (urwid.Divider(u"\u2500"), self.pile.options("pack")),
            (self.details_padding, self.pile.options("pack")),
            (urwid.Divider(u"\u2500"), self.pile.options("pack")),
        ]

    def close_details(self):

        if not self.details or len(self.pile.contents) == 1:
            return
        # del self.pile.contents[0]
        del self.pile.contents[1:]


    @property
    def value(self):
        return self._value


class DataTableRow(urwid.WidgetWrap):

    signals = ["focus", "unfocus"]

    def __init__(self, data, expand_details = False,
                 columns = [], **kwargs):

        self.expand_details = expand_details
        self.columns = columns
        self.border_char = kwargs.get('border_char', " ")
        attr_map = kwargs.get('attr_map', {})
        focus_map = {None: 'focused'}
        border_map = kwargs.get('border_map', {})
        self._values = dict()
        focus_map.update(kwargs.get('focus_map', {}))
        self.highlighted = False
        self.focused = False
        self.details_open = False
        details = None

        cols = list()

        if isinstance(data, dict):
            for k, v in data.items():
                self._values[k] = v

        for i, c in enumerate(self.columns):
            l = list()
            if c.sizing == None or c.sizing == "given":
                l.append(c.width)
            else:
                l += ['weight', c.width]

            if isinstance(data, (list, tuple)):
                val = data[i]
            elif isinstance(data, dict):
                val = data.get(c.field, None)
                details = data.get(c.details, None)
            else:
                raise Exception(data)

            cell_attr_map = attr_map.copy()
            if c.attr_map:
                cell_attr_map.update(c.attr_map)

            if c.attr:
                a = data.get(c.attr, {})
                if isinstance(a, basestring):
                    a = {None: a}
                # elif isinstance(a, dict):
                #     pass
                # else:
                #     raise Exception(a)
                cell_attr_map.update(a)

            cell_focus_map = focus_map.copy()
            if c.focus_map:
                cell_attr_map.update(c.focus_map)

            cell = DataTableCell(c, val, details=details,
                                 expand_details = self.expand_details,
                                 attr_map = cell_attr_map,
                                 focus_map = cell_focus_map)
            l.append(cell)
            cols.append(tuple(l))

        self._columns = urwid.Columns(cols)

        self._columns.contents = intersperse(
            (urwid.AttrMap(urwid.Divider(self.border_char),
                          attr_map=border_map,
                          focus_map=focus_map), ('given', 1, False)),
            self._columns.contents)
        super(DataTableRow, self).__init__(
            urwid.AttrMap(self._columns, attr_map, focus_map)
        )

    @property
    def values(self):
        return self._values

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

    def disable(self):
        self.selectable = lambda: False

    def enable(self):
        self.selectable = lambda: True

    def set_attr_map(self, attr_map):
        self._w.set_attr_map(attr_map)

    def set_focus_map(self, focus_map):
        self._w.set_focus_map(focus_map)

    def cell_by_column_label(self, label):

        for i, col in enumerate(self.columns):
            if col.label == label:
                return self[i]
        return None

    def __len__(self): return len(self._columns.contents)

    def __getitem__(self, i): return self._columns[i*2]

    def __delitem__(self, i): del self._columns[i*2]

    def __setitem__(self, i, v): self._columns[i*2] = v

    def render(self, size, focus=False):

        canvas = super(DataTableRow, self).render(size, focus)

        if not self.focused and focus:
            urwid.emit_signal(self, 'focus', self)
        elif self.focused and not focus:
            urwid.emit_signal(self, 'unfocus', self)
        self.focused = focus
        return canvas

    def open_details(self):

        for cell in self:
            cell.open_details()

        self.details_open = True

    def close_details(self):

        for cell in self:

            cell.close_details()

        self.details_open = False

    def toggle_details(self):

        if self.details_open:
            self.close_details()
        else:
            self.open_details()



class DataTableColumnHeader(urwid.WidgetWrap):

    def __init__(self, label,
                 align="left", padding=1, on_click=None, data=None,
                 attr_map={}, focus_map={}):
        self._label = label
        self.button = SimpleButton(label, attr="header",
                                   align=align, callback=on_click, data=data)
        p = urwid.Padding(
            self.button,
            left=padding, right=padding)
        am = urwid.AttrMap(p,
                           attr_map = attr_map,
                           focus_map = focus_map)
        super (DataTableColumnHeader, self).__init__(am)

    @property
    def label(self):
        return self._label

    def highlight(self):
        self.button.set_text_attr("highlight")

    def unhighlight(self):
        self.button.set_text_attr("header")

class DataTableHeaderRow(urwid.WidgetWrap):

    signals = ['click']

    def __init__(self, cols, border_char=" ",
                 attr_map={}, focus_map={}, border_map=None):

        self.border_char = border_char
        self.attr_map = attr_map
        self.focus_map = focus_map
        if border_map:
            self.border_map = border_map
        else:
            self.border_map = attr_map


        self.column_defs = cols
        self.button_group = list()
        button_attr_map = dict()
        button_focus_map = dict()
        widgets = list()
        self.columns = urwid.Columns([])
        am = urwid.AttrMap(self.columns, "header")

        self.padding = urwid.Padding(am)
        super(DataTableHeaderRow, self).__init__(self.padding)
        for i, item in enumerate(cols):
            width = item.width
            sizing = item.sizing
            header = DataTableColumnHeader(
                item.label,
                align = item.align,
                padding = item.padding,
                on_click = self.header_clicked,
                attr_map = self.attr_map,
                focus_map = self.focus_map)
            self.columns.contents.append(( header, (item.sizing, item.width, False)))

        self.columns.contents = intersperse(
            (urwid.AttrMap(urwid.Divider(self.border_char),
                          attr_map=border_map,
                          focus_map=focus_map), ('given', 1, False)),
            self.columns.contents)

    def header_clicked(self):
        index = [x[0] for x in self.contents].index(self.focus) / 2
        self._emit('click', index)


    def header_for_column(self, index):
        return self.columns.contents[index*2][0]

    def label_for_column(self, index):
        return self.header_for_column(index).label

    @property
    def contents(self):
        return self.columns.contents

    # @property
    # def focus(self):
    #     return self.columns.focus


class DataTable(urwid.WidgetWrap):

    signals = ["select", "refresh",
               "focus", "unfocus", "row_focus", "row_unfocus",
               "drag_start", "drag_continue", "drag_stop"]

    query_presorted = False

    def __init__(self, columns=None, data=[],
                 sort_field=None, sort_disabled=False, search_key=None,
                 wrap=False, limit = None, expand_details = False,
                 padding=0, border_char=" ",
                 attr_map={}, focus_map={}, border_map = {},
                 *args, **kwargs):
        self.lock = threading.Lock()

        if columns:
            self.columns = columns

        if not self.columns:
            raise Exception("must define columns in class or constructor")

        self.sort_field = sort_field
        self.sort_disabled = sort_disabled
        self.search_key = search_key
        self.wrap = wrap
        self.limit = limit
        self.expand_details = expand_details
        self.border_char = border_char
        self.attr_map = attr_map
        self.focus_map = focus_map
        if border_map:
            self.border_map = border_map
        else:
            self.border_map = attr_map
        self.selected_index = 0
        self.sort_reverse = False
        self.focused = False
        self.data = list()

        header_attr_map = attr_map.copy()
        header_focus_map = focus_map.copy()
        header_attr_map.update({None: "header"})
        header_focus_map.update({None: "focused"})

        self.header = DataTableHeaderRow(
            self.columns,
            border_char = self.border_char,
            attr_map=header_attr_map,
            focus_map=header_focus_map,
            border_map=self.border_map,
            **kwargs)
        urwid.connect_signal(self.header, 'click', self.column_clicked, None)
        self.walker = urwid.SimpleFocusListWalker([])

        self.listbox = ScrollingListBox(self.walker)


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
            self.paginate = True
            self.limit = limit
            self.offset = 0
        else:
            self.paginate = False
            self.limit = None
            self.offset = None


        self._pile = urwid.Pile([('pack', self.header),
                                 ('weight', 1, self.listbox)
                             ])
        self._pile.focus_position = 1
        super(DataTable,self).__init__(self._pile)
        for r in data:
            self.add_row(r)

        if self.sort_field and not self.query_presorted:
            self.sort_by(self.sort_field)

        if not len(self.columns):
            self._w.selectable = lambda: False
        args = list()
        if self.limit:
            args.append(self.offset)
        self.refresh(*args)


    def query(self, **kwargs):
        raise Exception("Must override datatable query method")

    def load_more(self, offset):

        self.refresh(offset)

    def refresh(self, offset = 0, **kwargs):
        orig_offset = offset
        with self.lock:
            if not offset: self.clear()
            if self.limit:
                kwargs['offset'] = offset
            for r in self.query(**kwargs):
                self.data.append(r)
                self.add_row(r, expand_details = self.expand_details)
            if self.sort_field and not self.query_presorted:
                self.sort_by(self.sort_field)

            if offset:
                self.listbox.set_focus(orig_offset)
            # if self.body and len(self.body):
            #     self.listbox.set_focus(0)
        urwid.emit_signal(self, "refresh", self)


    def column_clicked(self, header, index, *args):

        if self.sort_disabled:
            return

        label = self.header.label_for_column(index)
        if index != self.selected_index:
            self.sort_reverse = False
        else:
            self.sort_reverse = not self.sort_reverse

        if self.sort_field:
            self.sort_by(label, reverse=self.sort_reverse)

    def highlight_column(self, index):
        for i, col in enumerate(self.columns):
            if i == index:
                self.header.header_for_column(i).highlight()
            else:
                self.header.header_for_column(i).unhighlight()

    def cycle_index(self, direction):
        index = self.selected_index + direction
        if index == len(self.columns):
            if self.wrap:
                index = 0
            else:
                return
        elif index == -1:
            if self.wrap:
                index = len(self.columns) - 1
            else:
                return
        self.column_clicked(None, index)

    @property
    def body(self):
        return self.listbox.body

    def sort_by(self, field, **kwargs):
        self.sort_field = field
        index = 0
        for i,c in enumerate(self.columns):
            if c.label == field:
                index = i
                break

        sort_key = self.columns[index].sort_key

        if sort_key:
            kwargs['key'] = lambda x: sort_key(x[index].value)
        else:
            kwargs['key'] = lambda x: x[index].value

        if self.columns[index].sort_fn:
            kwargs['cmp'] = self.columns[index].sort_fn
        # print kwargs
        self.listbox.body.sort(**kwargs)
        self.selected_index = index
        self.highlight_column(self.selected_index)


    def add_row(self, data, expand_details = False):

        row = DataTableRow(
            data,
            expand_details = expand_details,
            columns = self.columns,
            border_char = self.border_char,
            attr_map = self.attr_map,
            focus_map = self.focus_map,
            border_map = self.border_map)

        urwid.connect_signal(
            row, "focus",
            lambda source: urwid.signals.emit_signal(self, "row_focus", self, row)
        )

        urwid.connect_signal(
            row, "unfocus",
            lambda source: urwid.signals.emit_signal(self, "row_unfocus", self, row)
        )

        self.listbox.body.append(row)



    def apply_filter(self, filter_fn):

        with self.lock:
            matches = filter(filter_fn, self.data)

            del self.listbox.body[:]
            for m in matches:
                self.add_row(m)



    @property
    def focus_position(self):

        return self.listbox.focus_position


    @property
    def selection(self):

        return self.listbox.selection

    def clear(self):
        del self.data[:]
        del self.listbox.body[:]
