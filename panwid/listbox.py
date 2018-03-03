from __future__ import division
import logging
logger = logging.getLogger(__name__.split(".")[0])

import urwid
from urwid_utils.palette import *

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
        else:
            scroll_position = -1

        pos_marker = urwid.AttrMap(urwid.Text(" "),
                                   {None: "scroll_pos"}
        )

        down_marker = urwid.AttrMap(urwid.Text(u"\N{DOWNWARDS ARROW}"),
                                   {None: "scroll_marker"}
        )

        begin_marker = urwid.AttrMap(urwid.Text(u"\N{CIRCLED MINUS}"),
                                   {None: "scroll_marker"}
        )

        end_marker = urwid.AttrMap(urwid.Text(u"\N{CIRCLED PLUS}"),
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
                if i == 0 and self.parent.focus_position == 0:
                    marker = begin_marker
                elif i+1 == height and self.parent.row_count == self.parent.focus_position+1:
                    marker = end_marker
                elif len(self.parent.body) == self.parent.focus_position+1 and i == scroll_position + scroll_marker_height//2:
                    marker = down_marker
                else:
                    marker = pos_marker
            else:
                if i < scroll_position:
                    marker = view_marker
                elif self.parent.row_count and i/height < ( len(self.parent.body) / self.parent.row_count):
                    marker = view_marker
                else:
                    marker = bg_marker
            self.pile.contents.append(
                (urwid.Filler(marker), self.pile.options("weight", 1))
            )
        self._invalidate()

    def selectable(self):
        # FIXME: mouse click/drag
        return False


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
        self.load_more = False
        self.height = 0
        self.page = 0

        self.queued_keypress = None

        self.listbox = urwid.ListBox(body)
        self.columns = urwid.Columns([
            ('weight', 1, self.listbox)
        ])
        if self.with_scrollbar:
            self.scroll_bar = ListBoxScrollBar(self)
            self.columns.contents.append(
                (self.scroll_bar, self.columns.options("given", 1))
            )
        super(ScrollingListBox, self).__init__(self.columns)

    @classmethod
    def get_palette_entries(cls):

        return {

            "scroll_pos": PaletteEntry(
                mono = "white",
                foreground = "black",
                background = "white",
                foreground_high = "black",
                background_high = "white"
            ),
            "scroll_marker": PaletteEntry(
                mono = "white,bold",
                foreground = "black,bold",
                background = "white",
                foreground_high = "black,bold",
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

        }

    def mouse_event(self, size, event, button, col, row, focus):

        SCROLL_WHEEL_HEIGHT_RATIO = 0.5
        if row < 0 or row >= self.height:
            return
        if event == 'mouse press':
            if button == 1:
                self.mouse_state = 1
                self.drag_from = self.drag_last = (col, row)
            elif button == 4:
                pos = self.listbox.focus_position - int(self.height * SCROLL_WHEEL_HEIGHT_RATIO)
                if pos < 0:
                    pos = 0
                self.listbox.focus_position = pos
                self.listbox.make_cursor_visible(size)
                self._invalidate()
            elif button == 5:
                pos = self.listbox.focus_position + int(self.height * SCROLL_WHEEL_HEIGHT_RATIO)
                if pos > len(self.listbox.body) - 1:
                    if self.infinite:
                        self.load_more = True
                    pos = len(self.listbox.body) - 1
                self.listbox.focus_position = pos
                self.listbox.make_cursor_visible(size)
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
        return super(ScrollingListBox, self).mouse_event(size, event, button, col, row, focus)


    def keypress(self, size, key):

        command = self._command_map[key]
        if not command:
            return super(ScrollingListBox, self).keypress(size, key)

        # down, page down at end trigger load of more data
        if (
                command in ["cursor down", "cursor page down"]
                and self.infinite
                and (
                    not len(self.body)
                    or self.focus_position == len(self.body)-1)
        ):
                self.load_more = True
                self.queued_keypress = key
                self._invalidate()

        elif command == "activate":
            urwid.signals.emit_signal(self, "select", self, self.selection)

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
        if (self.load_more
            and (len(self.body) == 0
                 or "bottom" in self.ends_visible((maxcol, maxrow))
            )
        ):

            self.load_more = False
            self.page += 1
            # old_len = len(self.body)
            urwid.signals.emit_signal(
                self, "load_more")
            try:
                focus = self.focus_position
            except IndexError:
                focus = None
            if (self.queued_keypress
                and focus
                and focus < len(self.body)
            ):
                # logger.info("send queued keypress")
                self.keypress(size, self.queued_keypress)
            self.queued_keypress = None
            # self.listbox._invalidate()
            # self._invalidate()

        if self.with_scrollbar and len(self.body):
            self.scroll_bar.update(size)

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
        if not len(self.body):
            return
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

__all__ = ["ScrollingListBox"]
