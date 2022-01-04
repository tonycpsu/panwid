import logging
logger = logging.getLogger(__name__)
import os
import random
import string
from functools import wraps
import re
import itertools

import six
import urwid
from urwid_utils.palette import *
# import urwid_readline
from orderedattrdict import AttrDict

# from .datatable import *
from .listbox import ScrollingListBox
from .keymap import *
from .highlightable import HighlightableTextMixin
from .autocomplete import AutoCompleteMixin

class DropdownButton(urwid.Button):

    text_attr = "dropdown_text"

    left_chars = u""
    right_chars = u""


    def __init__(
            self, label,
            text_attr=None,
            left_chars=None, right_chars=None
    ):

        self.label_text = label
        if text_attr:
            self.text_attr = text_attr
        if left_chars:
            self.left_chars = left_chars
        if right_chars:
            self.right_chars = right_chars

        self.button_left = urwid.Text(self.left_chars)
        self.button_right = urwid.Text(self.right_chars)

        self._label = urwid.SelectableIcon("", cursor_position=0)
        self.cols = urwid.Columns([
            (len(self.left_chars), self.button_left),
            ('weight', 1, self._label),
            (len(self.right_chars), self.button_right)
        ], dividechars=0)
        self.set_label((self.text_attr, self.label_text))
        super(urwid.Button, self).__init__(self.cols)

    @property
    def decoration_width(self):
        return len(self.left_chars) + len(self.right_chars)

    @property
    def width(self):
        return self.decoration_width + len(self.label_text)


class DropdownItem(HighlightableTextMixin, urwid.WidgetWrap):

    signals = ["click"]

    text_attr = "dropdown_text"
    highlight_attr = "dropdown_highlight"
    focused_attr = "dropdown_focused"

    def __init__(self, label, value,
                 margin=0,
                 text_attr=None,
                 focused_attr=None,
                 highlight_attr=None,
                 left_chars=None, right_chars=None):

        self.label_text = label
        self.value = value
        self.margin = margin
        if text_attr:
            self.text_attr = text_attr
        if focused_attr:
            self.focused_attr = focused_attr
        if highlight_attr:
            self.highlight_attr = highlight_attr
        self.button = DropdownButton(
            self.label_text,
            text_attr=self.text_attr,
            left_chars=left_chars, right_chars=right_chars
        )

        self.padding = urwid.Padding(self.button, width=("relative", 100),
                                     left=self.margin, right=self.margin)


        self.attr = urwid.AttrMap(self.padding, {None: self.text_attr})
        self.attr.set_focus_map({
            None: self.focused_attr,
            self.text_attr: self.focused_attr
        })
        super(DropdownItem, self).__init__(self.attr)
        urwid.connect_signal(
            self.button,
            "click",
            lambda source: self._emit("click")
        )

    @property
    def highlight_source(self):
        return self.label_text

    @property
    def highlightable_attr_normal(self):
        return self.text_attr

    @property
    def highlightable_attr_highlight(self):
        return self.highlight_attr

    def on_highlight(self):
        self.set_text(self.highlight_content)

    def on_unhighlight(self):
        self.set_text(self.highlight_source)

    @property
    def width(self):
        return self.button.width + 2*self.margin

    @property
    def decoration_width(self):
        return self.button.decoration_width + 2*self.margin

    def __str__(self):
        return self.label_text

    def __contains__(self, s):
        return s in self.label_text

    def startswith(self, s):
        return self.label_text.startswith(s)

    @property
    def label(self):
        return self.button.label

    def set_text(self, text):
        self.button.set_label(text)

@keymapped()
class DropdownDialog(AutoCompleteMixin, urwid.WidgetWrap, KeymapMovementMixin):

    signals = ["select", "close"]

    text_attr = "dropdown_text"

    min_width = 4

    label = None
    border = None
    scrollbar = False
    margin = 0
    max_height = None

    def __init__(
            self,
            drop_down,
            items,
            default=None,
            label=None,
            border=False,
            margin = None,
            scrollbar=None,
            text_attr=None,
            focused_attr=None,
            prompt_attr=None,
            left_chars=None,
            right_chars=None,
            left_chars_top=None,
            rigth_chars_top=None,
            max_height=None,
            keymap = {},
            **kwargs
    ):

        self.drop_down = drop_down
        self.items = items
        if label is not None: self.label = label
        if border is not None: self.border = border
        if margin is not None: self.margin = margin
        if scrollbar is not None: self.scrollbar = scrollbar
        if text_attr:
            self.text_attr = text_attr
        if focused_attr:
            self.focused_attr = focused_attr
        if prompt_attr:
            self.prompt_attr = prompt_attr
        if max_height is not None: self.max_height = max_height
        self.selected_button = 0
        buttons = []

        buttons = [
                DropdownItem(
                    label=l, value=v, margin=self.margin,
                    text_attr=self.text_attr,
                    focused_attr=self.focused_attr,
                    left_chars=left_chars,
                    right_chars=right_chars,
                )
                for l, v in self.items.items()
        ]
        self.dropdown_buttons = ScrollingListBox(
            urwid.SimpleListWalker(buttons), with_scrollbar=scrollbar
        )

        urwid.connect_signal(
            self.dropdown_buttons,
            'select',
            lambda source, selection: self.on_complete_select(source)
        )

        kwargs = {}
        if self.label is not None:
            kwargs["title"] = self.label
            kwargs["tlcorner"] = u"\N{BOX DRAWINGS LIGHT DOWN AND HORIZONTAL}"
            kwargs["trcorner"] = u"\N{BOX DRAWINGS LIGHT DOWN AND LEFT}"

        w = self.dropdown_buttons
        if self.border:
           w = urwid.LineBox(w, **kwargs)

        self.pile = urwid.Pile([
            ("weight", 1, w),
        ])
        super().__init__(self.pile)

    @property
    def complete_container(self):
        return self.pile

    @property
    def complete_container_pos(self):
        return 1

    @property
    def complete_body(self):
        return self.body

    @property
    def complete_items(self):
        return self.body

    @property
    def max_item_width(self):
        if not len(self):
            return self.min_width
        return max(w.width for w in self)

    @property
    def width(self):
        width = self.max_item_width
        if self.border:
            width += 2
        return width

    @property
    def height(self):
        height = min(len(self), self.max_height)
        if self.border:
            height += 2
        return height

    @property
    def body(self):
        return self.dropdown_buttons.body

    def __getitem__(self, i):
        return self.body[i]

    def __len__(self):
        return len(self.body)

    @property
    def focus_position(self):
        return self.dropdown_buttons.focus_position

    @focus_position.setter
    def focus_position(self, pos):
        self.dropdown_buttons.listbox.set_focus_valign("top")
        self.dropdown_buttons.focus_position = pos

    @property
    def selection(self):
        return self.dropdown_buttons.selection

    # def on_complete_select(self, pos, widget):

    #     # logger.debug("select_button: %s" %(button))
    #     label = widget.label
    #     value = widget.value
    #     self.selected_button = self.focus_position
    #     self.complete_off()
    #     self._emit("select", widget)
    #     self._emit("close")

    # def keypress(self, size, key):
    #     return super(DropdownDialog, self).keypress(size, key)


    @property
    def selected_value(self):
        if not self.focus_position:
            return None
        return self.body[self.focus_position].value

@keymapped()
class Dropdown(urwid.PopUpLauncher):
    # Based in part on SelectOne widget from
    # https://github.com/tuffy/python-audio-tools

    signals = ["change"]

    text_attr = "dropdown_text"
    label_attr = "dropdown_label"
    focused_attr = "dropdown_focused"
    highlight_attr = "dropdown_highlight"
    prompt_attr = "dropdown_prompt"

    auto_complete = None
    label = None
    empty_label = u"\N{EMPTY SET}"
    expanded = False
    margin = 0

    def __init__(
            self,
            items=None,
            label=None,
            default=None,
            expanded=None,
            border=False, scrollbar=False,
            margin=None,
            text_attr=None,
            label_attr=None,
            focused_attr=None,
            highlight_attr=None,
            prompt_attr=None,
            left_chars=None, right_chars=None,
            left_chars_top=None, right_chars_top=None,
            auto_complete=None,
            max_height=10,
            # keymap = {}
    ):

        if items is not None:
            self._items = items
        if label is not None:
            self.label = label
        if expanded is not None:
            self.expanded = expanded
        self.default = default

        self.border = border
        self.scrollbar = scrollbar
        if auto_complete is not None: self.auto_complete = auto_complete

        # self.keymap = keymap

        if margin:
            self.margin = margin

        if text_attr:
            self.text_attr = text_attr
        if label_attr:
            self.label_attr = label_attr
        if focused_attr:
            self.focused_attr = focused_attr
        if highlight_attr:
            self.highlight_attr = highlight_attr
        if prompt_attr:
            self.prompt_attr = prompt_attr

        if isinstance(self.items, list):
            if len(self.items):
                self._items = AttrDict(
                    item if isinstance(item, tuple) else (item, n)
                    for n, item in enumerate(self.items)
                )
            else:
                self._items = AttrDict()
        else:
            self._items = self.items


        self.button = DropdownItem(
            u"", None,
            margin=self.margin,
            text_attr=self.text_attr,
            highlight_attr=self.highlight_attr,
            focused_attr=self.focused_attr,
            left_chars = left_chars_top if left_chars_top else left_chars,
            right_chars = right_chars_top if right_chars_top else right_chars
        )

        self.pop_up = DropdownDialog(
            self,
            self._items,
            self.default,
            label=self.label,
            border=self.border,
            margin=self.margin,
            text_attr=self.text_attr,
            focused_attr=self.focused_attr,
            prompt_attr=self.prompt_attr,
            left_chars=left_chars,
            right_chars=right_chars,
            auto_complete=self.auto_complete,
            scrollbar=scrollbar,
            max_height=max_height,
            # keymap=self.KEYMAP
        )

        urwid.connect_signal(
            self.pop_up,
            "select",
            lambda souce, pos, selection: self.select(selection)
        )

        urwid.connect_signal(
            self.pop_up,
            "close",
            lambda source: self.close_pop_up()
        )

        if self.default is not None:
            try:
                if isinstance(self.default, str):
                    try:
                        self.select_label(self.default)
                    except ValueError:
                        pass
                else:
                    raise StopIteration
            except StopIteration:
                try:
                    self.select_value(self.default)
                except ValueError:
                    self.focus_position = 0

        if len(self):
            self.select(self.selection)
        else:
            self.button.set_text((self.text_attr, self.empty_label))

        cols = [ (self.button_width, self.button) ]

        if self.label:
            cols[0:0] = [
                ("pack", urwid.Text([(self.label_attr, "%s: " %(self.label))])),
            ]
        self.columns = urwid.Columns(cols, dividechars=0)

        w = self.columns
        if self.border:
            w = urwid.LineBox(self.columns)
        w = urwid.Padding(w, width=self.width)

        super(Dropdown, self).__init__(w)
        urwid.connect_signal(
            self.button,
            'click',
            lambda button: self.open_pop_up()
        )
        if self.expanded:
            self.open_pop_up()

    @classmethod
    def get_palette_entries(cls):
        return {
            "dropdown_text": PaletteEntry(
                foreground="light gray",
                background="dark blue",
                foreground_high="light gray",
                background_high="#003",
            ),
            "dropdown_focused": PaletteEntry(
                foreground="white",
                background="light blue",
                foreground_high="white",
                background_high="#009",
            ),
            "dropdown_highlight": PaletteEntry(
                foreground="yellow",
                background="light blue",
                foreground_high="yellow",
                background_high="#009",
            ),
            "dropdown_label": PaletteEntry(
                foreground="white",
                background="black"
            ),
            "dropdown_prompt": PaletteEntry(
                foreground="light blue",
                background="black"
            )
        }


    @keymap_command()
    def complete_prefix(self):
        if not self.auto_complete:
            return
        self.open_pop_up()
        self.pop_up.complete_prefix()

    @keymap_command()
    def complete_substring(self):
        if not self.auto_complete:
            return
        self.open_pop_up()
        self.pop_up.complete_substring()

    def create_pop_up(self):
        # print("create")
        return self.pop_up

    @property
    def button_width(self):
        return self.pop_up.max_item_width + self.button.decoration_width

    @property
    def pop_up_width(self):
        w = self.button_width
        if self.border:
            w += 2
        return w

    @property
    def contents_width(self):
        # raise Exception(self.button.width)
        w = self.button_width
        if self.label:
            w += len(self.label) + 2
        return max(self.pop_up.width, w)

    @property
    def width(self):
        width = max(self.contents_width, self.pop_up.width)
        if self.border:
            width += 2
        return width

    @property
    def height(self):
        height = self.pop_up.height + 1
        return height

    def pack(self, size, focus=False):
        return (self.width, self.height)

    @property
    def page_size(self):
        return self.pop_up.height

    def open_pop_up(self):
        # print("open")
        super(Dropdown, self).open_pop_up()

    def close_pop_up(self):
        super().close_pop_up()

    def get_pop_up_parameters(self):
        return {'left': (len(self.label) + 2 if self.label else 0),
                'top': 0,
                'overlay_width': self.pop_up_width,
                'overlay_height': self.pop_up.height
        }

    @property
    def focus_position(self):
        return self.pop_up.focus_position

    @focus_position.setter
    def focus_position(self, pos):
        if pos == self.focus_position:
            return
        # self.select_index(pos)
        old_pos = self.focus_position
        self.pop_up.selected_button = self.pop_up.focus_position = pos
        self.select(self.selection)

    @property
    def items(self):
        return self._items

    @property
    def selection(self):
        return self.pop_up.selection

    @property
    def items(self):
        return self._items

    @property
    def selection(self):
        return self.pop_up.selection

    def select_label(self, label, case_sensitive=False):

        old_value = self.value

        f = lambda x: x
        if not case_sensitive:
            f = lambda x: x.lower() if isinstance(x, str) else x

        try:
            index = next(itertools.dropwhile(
                    lambda x: f(x[1]) != f(label),
                    enumerate((self._items.keys())
                )
            ))[0]
        except (StopIteration, IndexError):
            raise ValueError
        self.focus_position = index

    def select_value(self, value):

        try:
            index = next(
                itertools.dropwhile(
                    lambda x: x[1] != value,
                enumerate((self._items.values()))
                )
            )[0]
        except (StopIteration, IndexError):
            raise ValueError
        self.focus_position = index


    @property
    def labels(self):
        return self._items.keys()

    @property
    def values(self):
        return self._items.values()

    @property
    def selected_label(self):
        return self.selection.label

    @selected_label.setter
    def selected_label(self, label):
        return self.select_label(label)

    @property
    def selected_value(self):
        if not self.selection:
            return None
        return self.selection.value

    @selected_value.setter
    def selected_value(self, value):
        return self.select_value(value)

    @property
    def value(self):
        return self.selected_value

    @value.setter
    def value(self, value):
        old_value = self.value

        # try to set by value.  if not found, try to set by label
        try:
            self.selected_value = value
        except StopIteration:
            self.selected_label = value

    def cycle_prev(self):
        self.cycle(-1)

    def action(self):
        pass

    @keymap_command("cycle")
    def cycle(self, n):
        pos = self.focus_position + n
        if pos > len(self) - 1:
            pos = len(self) - 1
        elif pos < 0:
            pos = 0
        # self.focus_position = pos
        self.focus_position = pos

    def select(self, button):
        logger.debug("select: %s" %(button))
        self.button.set_text((self.text_attr, button.label))
        self.pop_up.dropdown_buttons.listbox.set_focus_valign("top")
        # if old_pos != pos:
        self.action()
        self._emit("change", self.selected_label, self.selected_value)

    # def set_items(self, items, selected_value):
    #     self._items = items
    #     self.make_selection([label for (label, value) in items if
    #                          value is selected_value][0],
    #                         selected_value)
    def __len__(self):
        return len(self.items)

__all__ = ["Dropdown"]
