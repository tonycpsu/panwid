from __future__ import division
import urwid
import logging
logger = logging.getLogger(__name__.split(".")[0])


class ListBoxScrollBar(urwid.WidgetWrap):

    def __init__(self, parent):
        self.parent = parent
        self.pile = urwid.Pile([])
        super(ListBoxScrollBar, self).__init__(self.pile)

    def update(self, size):
        width, height = size
        scroll_marker_height = 1
        del self.pile.contents[:]
        if (len(self.parent.body)
            and self.parent.focus is not None
            and self.parent.row_count > height):
            scroll_position = int(
                self.parent.focus_position / self.parent.row_count * height
            )
            scroll_marker_height = max( height * (height / self.parent.row_count ), 1)
            # print "height: %d" %(scroll_marker_height)
        else:
            scroll_position = -1

        pos_marker = urwid.AttrMap(urwid.Text(u" "),
                                   {None: "scroll_pos"}
        )

        down_marker = urwid.AttrMap(urwid.Text(u"\N{DOWNWARDS ARROW}"),
                                   {None: "scroll_marker"}
        )

        end_marker = urwid.AttrMap(urwid.Text(u"\N{CIRCLED DOT OPERATOR}"),
                                   {None: "scroll_marker"}
        )

        view_marker = urwid.AttrMap(urwid.Text(" "),
                                    {None: "scroll_view"}
        )

        bg_marker = urwid.AttrMap(urwid.Text(" "),
                                   {None: "scroll_bg"}
        )


        for i in range(height):
            if abs( i - scroll_position ) <= scroll_marker_height//2:
                # print self.parent.row_count, self.parent.focus_position
                if i+1 == height and self.parent.row_count == self.parent.focus_position+1:
                    marker = end_marker
                elif len(self.parent.body) == self.parent.focus_position+1 and i == scroll_position + scroll_marker_height//2:
                    marker = down_marker
                else:
                    marker = pos_marker
            else:
                if i < scroll_position:
                    marker = view_marker
                elif i/height < ( len(self.parent.body) / self.parent.row_count):
                    marker = view_marker
                else:
                    marker = bg_marker
            self.pile.contents.append(
                (urwid.Filler(marker), self.pile.options("weight", 1))
            )
        self._invalidate()


class ScrollingListBox(urwid.WidgetWrap):

    signals = ["select",
               "drag_start", "drag_continue", "drag_stop",
               "load_more"]

    def __init__(self, body,
                 infinite = False,
                 with_scrollbar=False,
                 scroll_rows=None,
                 row_count_fn = None):

        self.infinite = infinite
        self.with_scrollbar = with_scrollbar
        self.scroll_rows = scroll_rows
        self.row_count_fn = row_count_fn

        self.mouse_state = 0
        self.drag_from = None
        self.drag_last = None
        self.drag_to = None
        self.requery = False
        self.height = 0

        self.listbox = urwid.ListBox(body)
        self.columns = urwid.Columns([
            ('weight', 1, self.listbox)
        ])
        if self.with_scrollbar:
            self.scroll_bar = ListBoxScrollBar(self)
            self.columns.contents.append(
                (self.scroll_bar, self.columns.options("given", 1))
            )
        # self.pile = urwid.Pile([
        #     ('weight', 1, self.columns)
        # ])
        super(ScrollingListBox, self).__init__(self.columns)
        # super(ScrollingListBox, self).__init__(self.listbox)


    def mouse_event(self, size, event, button, col, row, focus):
        """Overrides ListBox.mouse_event method.

        Implements mouse scrolling.
        """
        if row < 0 or row >= self.height:
            return
        if event == 'mouse press':
            if button == 1:
                self.mouse_state = 1
                self.drag_from = self.drag_last = (col, row)
            elif button == 4:
                pct = self.focus_position / len(self.body)
                self.set_focus_valign(('relative', pct - 10))
                self._invalidate()
            elif button == 5:
                pct = self.focus_position / len(self.body)
                self.set_focus_valign(('relative', pct + 5))
                self._invalidate()
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
        # return self.__super.mouse_event(size, event, button, col, row, focus)
        return super(ScrollingListBox, self).mouse_event(size, event, button, col, row, focus)


    def keypress(self, size, key):
        """Overrides ListBox.keypress method.

        Implements vim-like scrolling and infinite scrolling.
        """

        # print "ListBox keypress"


        KEY_MAP = {
            "j": "down",
            "k": "up",
            "g": "home",
            "G": "end",
        }
        key = KEY_MAP.get(key, key)

        if len(self.body):
            if (self.infinite
            and key in ["page down", "down"]
            and len(self.body)
            and self.focus_position == len(self.body)-1):
                self.requery = True

            if key == "home":
                self.focus_position = 0
            elif key == "end":
                self.focus_position = 0
                self.focus_position = len(self.body) - 1

            if key in ["up", "down", "home", "end", "page up", "page down"]:
                # raise Exception(key)
                return super(ScrollingListBox, self).keypress(size, key)

            elif key == "enter":
                urwid.signals.emit_signal(self, "select", self, self.selection)

            else:
                return super(ScrollingListBox, self).keypress(size, key)

                # self._invalidate()
        else:
            return super(ScrollingListBox, self).keypress(size, key)

    @property
    def selection(self):

        if len(self.body):
            return self.body[self.focus_position]


    def render(self, size, focus=False):

        maxcol, maxrow = size

        # print
        # print
        # print self.listbox.get_focus_offset_inset(size)

        if self.requery and "bottom" in self.ends_visible(
                (maxcol, maxrow) ):
            self.requery = False
            urwid.signals.emit_signal(
                self, "load_more", len(self.body))
        if self.with_scrollbar and len(self.body):
            self.scroll_bar.update(size)

        # if len(self.body) and self.focus_position:
        #     scroll_pos = self.listbox.get_focus_offset_inset(size)[0]
        #     if self.scroll_rows:
        #         if (scroll_pos <= self.scroll_rows):
        #             pct = ((self.scroll_rows )/maxrow)*100
        #             self.set_focus_valign(("relative", pct))
        #         elif (scroll_pos >= (maxrow - self.scroll_rows)):
        #             pct = ((maxrow - self.scroll_rows )/maxrow)*100
        #             self.set_focus_valign(("relative", pct))

        self.height = maxrow
        return super(ScrollingListBox, self).render( (maxcol, maxrow), focus)


    def disable(self):
        self.selectable = lambda: False

    def enable(self):
        self.selectable = lambda: True


    @property
    def contents(self):
        return self.columns.contents

    @property
    def focus(self):
        return self.listbox.focus

    @property
    def focus_position(self):
        if not len(self.listbox.body):
            raise IndexError
        if len(self.listbox.body):
            return self.listbox.focus_position
        return None

    @focus_position.setter
    def focus_position(self, value):
        self.listbox.focus_position = value
        self.listbox._invalidate()

    def __getattr__(self, attr):
        if attr in ["ends_visible", "set_focus", "set_focus_valign", "body", "focus"]:
            return getattr(self.listbox, attr)
        # elif attr == "body":
        #     return self.walker
        raise AttributeError(attr)

    @property
    def row_count(self):
        if self.row_count_fn:
            return self.row_count_fn()
        return len(self.body)
