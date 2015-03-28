import urwid
from collections import namedtuple
from collections import MutableSequence

intersperse = lambda e,l: sum([[x, e] for x in l],[])[:-1]

class SimpleButton(urwid.WidgetWrap):
    """A clickable, selectable text widget."""

    signals = ['click']

    def __init__(self, label, attr="normal", align="left",
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

    def __init__(self, label, width=1, padding=1, sizing="given", align='left',
                 sort_key=None, sort_fn=None, format_fn=None,
                 attr_map = None, focus_map = None):

        self.label = label
        self.width = width
        self.padding = padding
        self.sizing = sizing
        self.align = align
        self.sort_key = sort_key
        self.sort_fn = sort_fn
        if format_fn:
            self.format_fn = format_fn
        else:
            self.format_fn = self.default_format
        self.attr_map = attr_map
        self.focus_map = focus_map

    def default_format(self, v):
        if isinstance(v, int):
            v = "%d" %(v)
        if isinstance(v, float):
            v = "%.03f" %(v)
        elif v is None:
            v = ""
        return urwid.Text(v, align=self.align)
        

# class DataTableColumnDef(
#         namedtuple('DataTableColumnDef',
#                    ['label', 'width', 'padding', 'sizing', 'align',
#                     'sort_key', 'sort_fn', 'format_fn',
#                     'attr_map', 'focus_map', ])):

#     def __new__(cls, label, width=1, padding=1, sizing="given", align='left',
#                 sort_key=None, sort_fn=None, format_fn=None,
#                 attr_map = None, focus_map = None):
        
#         if not format_fn:
#             format_fn = cls.format
            
#         return super(DataTableColumnDef, cls).__new__(
#             cls, label, width, padding, sizing, align,
#             sort_key, sort_fn, format_fn,
#             attr_map, focus_map)

#     def format(self, v):
#         if isinstance(v, int):
#             v = "%d" %(v)
#         elif v is None:
#             v = ""
#         return v    
    

#     def default_format(self, t):
#         textattr = "normal"
#         # if isinstance(t, tuple):
#         #     textattr, t = t
#         if self.format_fn:
#             s = self.format_fn(t)
#         elif isinstance(t, int):
#             s = "%d" %(t)
#         elif t == None:
#             s = ""
#         else:
#             s = unicode(t)
            
#         text = urwid.Text( (textattr, s), align=self.align)
#         text.val = t
#         cell = urwid.Padding(text, left=self.padding, right=self.padding)
#         text.sort_key = self.sort_key
#         text.sort_fn = self.sort_fn
#         l = list()
#         cell = urwid.AttrMap(cell, self.attr_map, self.focus_map)
#         if self.sizing == None or self.sizing == "given":
#             l.append(self.width)
#         else:
#             l += ['weight', self.width]
#         l.append(cell)
#         return tuple(l)


class ScrollingListBox(urwid.ListBox):

    def __init__(self, body, paginate=False):
        super(ScrollingListBox, self).__init__(body)
        self.mouse_state = 0
        self.drag_from = None
        self.drag_last = None
        self.drag_to = None
        self.requery = False
        self.paginate = paginate

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
            if not self.drag_from:
                return
            if button == 1:
                self.drag_to = (col, row)
                if self.mouse_state == 1:
                    self.mouse_state = 2
                    self.on_drag_start(self.drag_from)
                else:
                    self.on_drag(self.drag_last, self.drag_to)

            self.drag_last = (col, row)

        elif event == 'mouse release':
            if self.mouse_state == 2:
                self.drag_to = (col, row)
                self.on_drop(self.drag_from, self.drag_to)
            self.mouse_state = 0
        return self.__super.mouse_event(size, event, button, col, row, focus)

    def on_drag_start(self, drag_from):
        pass

    def on_drag(self, drag_from, drag_to):
        pass

    def on_drop(self, drag_from, drop_to):
        pass

    def keypress(self, size, key):
        """Overrides ListBox.keypress method.

        Implements vim-like scrolling.
        """
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
        elif key == 'page down' and self.focus_position == len(self.body)-1:
            self.requery = True
        return super(ScrollingListBox, self).keypress(size, key)

    def update(self):
        pass

    def render(self, size, focus=False):
        maxcol, maxrow = size
        if self.paginate:
            if self.requery and "bottom" in self.ends_visible(
                (maxcol, maxrow) ):
                self.requery = False
                self.update()
        return super(ScrollingListBox, self).render( (maxcol, maxrow), focus)


    def disable(self):
        self.selectable = lambda: False

    def enable(self):
        self.selectable = lambda: True


class DataTableCell(urwid.WidgetWrap):

    def __init__(self, column, value,
                 attr_map={}, focus_map={}):

        def value_format(v):
            if isinstance(v, int):
                v = "%d" %(v)
            elif v is None:
                v = ""
            return v    
        
        self.column = column
        self._value = value
        value = column.format_fn(value)
        padding = urwid.Padding(value,
                                left=column.padding, right=column.padding)

        self.attr_map = urwid.AttrMap(
            padding,
            attr_map = attr_map,
            focus_map = focus_map)
        super(DataTableCell, self).__init__(self.attr_map)

    @property
    def value(self):
        return self._value

    
class DataTableRow(urwid.WidgetWrap):
    
    def __init__(self, data, **kwargs):
        self.border_char = kwargs.get('border_char', " ")
        attr_map = kwargs.get('attr_map', {})
        focus_map = {None: 'focused'}
        border_map = kwargs.get('border_map', {})
        focus_map.update(kwargs.get('focus_map', {}))
        self.highlighted = False
        cols = list()
        for i, c in enumerate(kwargs['columns']):
            l = list()
            if c.sizing == None or c.sizing == "given":
                l.append(c.width)
            else:
                l += ['weight', c.width]
            cell = DataTableCell(c, data[i], attr_map = attr_map, focus_map = focus_map)
            l.append(cell)
            cols.append(tuple(l))

        self.columns = urwid.Columns(cols)

        self.columns.contents = intersperse(
            (urwid.AttrMap(urwid.Divider(self.border_char),
                          attr_map=border_map,
                          focus_map=focus_map), ('given', 1, False)),
            self.columns.contents)
        super(DataTableRow, self).__init__(
            urwid.AttrMap(self.columns, attr_map, focus_map)
        )

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key
        # super(DataTableRow, self).keypress(size, key)

    def set_attr_map(self, attr_map):
        self._w.set_attr_map(attr_map)

    def set_focus_map(self, focus_map):
        self._w.set_focus_map(focus_map)

    def __len__(self): return len(self.columns)

    def __getitem__(self, i): return self.columns[i*2]

    def __delitem__(self, i): del self.columns[i*2]

    def __setitem__(self, i, v): self.columns[i*2] = v


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
                 attr_map={}, focus_map={}, border_map={}):

        self.border_char = border_char
        self.attr_map = attr_map
        self.focus_map = focus_map
        self.border_map = border_map

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

    @property
    def focus(self):
        return self.columns.focus


class DataTable(urwid.WidgetWrap):

    query_presorted = False

    def __init__(self, columns=None, data=[], 
                 sort_field=None, sort_disabled=False, search_key=None, 
                 wrap=False,
                 padding=0, border_char=" ",
                 attr_map={}, focus_map={}, border_map = {},
                 *args, **kwargs):
        if columns:
            self.columns = columns
            
        if not self.columns:
            raise Exception("must define columns in class or constructor")
        
        self.sort_field = sort_field
        self.sort_disabled = sort_disabled
        self.search_key = search_key
        self.wrap = wrap
        self.border_char = border_char
        self.attr_map = attr_map
        self.focus_map = focus_map
        self.border_map = border_map
        self.selected_index = 0
        self.sort_reverse = False
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

        self.listbox = ScrollingListBox(urwid.SimpleFocusListWalker([]))

        self._pile = urwid.Pile([('pack', self.header),
                                 ('weight', 1, self.listbox)
                             ])
        self._pile.focus_position = 1
        super(DataTable,self).__init__(self._pile)
        for r in data:
            self.add_row(r)
        if self.sort_field:
            self.sort_by(self.sort_field)

        if not len(self.columns):
            self._w.selectable = lambda: False
        self.refresh()


    def query(self, **kwargs):
        raise Exception("Must override datatable query method")

    def refresh(self, **kwargs):
        self.clear()
        for r in self.query(**kwargs):
            self.data.append(r)
            self.add_row(r)
        if self.sort_field and not self.query_presorted:
            self.sort_by(self.sort_field)
            
        if self.body and len(self.body):
            self.listbox.set_focus(0)


    def column_clicked(self, header, index, *args):
        
        if self.sort_disabled:
            return
        
        label = self.header.label_for_column(index)
        if index != self.selected_index:
            self.sort_reverse = False
        else:
            self.sort_reverse = not self.sort_reverse

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

        try:
            sort_key = self.columns[index].sort_key
        except:
            return

        if self.columns[index].sort_key:
            kwargs['key'] = lambda x: self.columns[index].sort_key(x[index].value)
        else:
            kwargs['key'] = lambda x: x[index].value

        if self.columns[index].sort_fn:
            kwargs['cmp'] = self.columns[index].sort_fn
        self.listbox.body.sort(**kwargs)
        self.selected_index = index
        self.highlight_column(self.selected_index)

        
    def add_row(self, data):
                
        self.listbox.body.append(DataTableRow(
            data,
            columns = self.columns,
            border_char = self.border_char,
            attr_map = self.attr_map,
            focus_map = self.focus_map,
            border_map = self.border_map))

    def apply_filter(self, filter_fn):

        matches = filter(filter_fn, self.data)
        
        del self.listbox.body[:]
        for m in matches:
            self.add_row(m)

        if self.sort_field:
            self.sort_by(self.sort_field)


    def focus(self, idx):

        if len(self.listbox.body):
            self.listbox.set_focus(0)
        
    # def apply_text_filter(self, filter_text):
        
    #     if not self.search_key:
    #         return False
        
    #     matches = filter(
    #         lambda x:
    #         filter_text.lower() in self.search_key(x).lower(),
    #         self.data)
        
    #     del self.listbox.body[:]
    #     for m in matches:
    #         self.add_row(m)

    def clear(self):
        del self.data[:]
        del self.listbox.body[:]

