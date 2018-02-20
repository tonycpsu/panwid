import os
import random
import string
import re

import urwid
import urwid.raw_display

from urwid_utils.palette import *
from .datatable import *
from .listbox import ScrollingListBox

class DropdownButton(urwid.Button):

    left_chars = u""
    right_chars = u""

    def __init__(self, label, left_chars=None, right_chars=None):

        self.label_text = label
        if left_chars:
            self.left_chars = left_chars
        if right_chars:
            self.right_chars = right_chars

        self.button_left = urwid.Text(self.left_chars)
        self.button_right = urwid.Text(self.right_chars)

        self._label = urwid.SelectableIcon("")
        self.cols = urwid.Columns([
            (len(self.left_chars), self.button_left),
            ('weight', 1, self._label),
            (len(self.right_chars), self.button_right)
        ], dividechars=0)
        self.set_label(("dropdown_text", self.label_text))
        super(urwid.Button, self).__init__(self.cols)

    @property
    def decoration_width(self):
        return len(self.left_chars) + len(self.right_chars)

    @property
    def width(self):
        return self.decoration_width + len(self.label_text)


class DropdownItem(urwid.WidgetWrap):

    signals = ["click"]

    def __init__(self, label, value,
                 margin=0, left_chars=None, right_chars=None):

        self.label_text = label
        self.value = value
        self.margin = margin
        # self.button = urwid.Button(("dropdown_text", self.label_text))
        self.button = DropdownButton(
            self.label_text,
            left_chars=left_chars, right_chars=right_chars
        )
        # self.padding = urwid.Padding(self.button, width=("relative", 100),
        #                              left=self.margin, right=self.margin)
        self.padding = self.button
        self.attr = urwid.AttrMap(self.padding, {None: "dropdown_text"})
        self.attr.set_focus_map({
            None: "dropdown_focused",
            "dropdown_text": "dropdown_focused"
        })
        super(DropdownItem, self).__init__(self.attr)
        urwid.connect_signal(
            self.button,
            "click",
            lambda source: self._emit("click")
        )

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

    def set_label(self, label):
        self.button.set_label(label)

    def highlight_text(self, s, case_sensitive=False):

        # (a, b, c) = self.label_text.partition(s)
        (a, b, c) = re.search(
            r"(.*?)(%s)(.*)" %(s),
            self.label_text,
            re.IGNORECASE if not case_sensitive else 0
        ).groups()
        self.set_label([
            ("dropdown_text", a),
            ("dropdown_highlight", b),
            ("dropdown_text", c),
        ])

    def unhighlight(self):
        self.set_label(("dropdown_text", self.label_text))



class AutoCompleteEdit(urwid.Edit):

    signals = ["close"]

    def kepyress(self, size, key):
        if key == "enter":
            self._emit("close")
        return self.text.keypress(size, key)


class AutoCompleteBar(urwid.WidgetWrap):

    signals = ["change", "close"]
    def __init__(self):

        self.prompt = urwid.Text(("dropdown_prompt", "> "))
        self.text = AutoCompleteEdit("")
        # self.text.selectable = lambda x: False
        self.cols = urwid.Columns([
            (2, self.prompt),
            ("weight", 1, self.text)
        ], dividechars=0)
        self.cols.focus_position = 1
        self.filler = urwid.Filler(self.cols, valign="bottom")
        urwid.connect_signal(self.text, "postchange", self.text_changed)
        urwid.connect_signal(self.text, "close", lambda source: self._emit("close"))
        super(AutoCompleteBar, self).__init__(self.filler)

    def set_prompt(self, text):

        self.prompt.set_text(("dropdown_prompt", text))

    def set_text(self, text):

        self.text.set_edit_text(text)

    def text_changed(self, source, text):
        self._emit("change", text)


class DropdownDialog(urwid.WidgetWrap):

    signals = ["select", "close"]

    min_width = 4

    def __init__(
            self,
            drop_down,
            items,
            initial_value=None,
            label=None, border=False,
            scrollbar=False,
            auto_complete=False,
            margin = 0,
            left_chars=None,
            right_chars=None,
            left_chars_top=None,
            rigth_chars_top=None,
            max_height=10
    ):
        self.drop_down = drop_down
        self.items = items
        self.label = label
        self.border = border
        self.scrollbar = scrollbar
        self.auto_complete = auto_complete
        self.margin = margin
        self.max_height = max_height

        self.completing = False
        self.complete_anywhere = False

        self.selected_button = 0
        buttons = []

        buttons = [
                DropdownItem(
                    label=l, value=v, margin=self.margin,
                    left_chars=left_chars,
                    right_chars=right_chars,
                )
                for l, v in self.items.items()
        ]
        self.dropdown_buttons = ScrollingListBox(buttons, with_scrollbar=scrollbar)

        urwid.connect_signal(
            self.dropdown_buttons,
            'select',
            lambda source, selection: self._emit("select", selection)
        )

        urwid.connect_signal(
            self.dropdown_buttons,
            'select',
            lambda source, selection: self.select_button(selection)
        )

        box_height = self.height -2 if self.border else self.height
        self.box = urwid.BoxAdapter(self.dropdown_buttons, box_height)
        self.fill = urwid.Filler(self.box)
        kwargs = {}
        if self.label is not None:
            kwargs["title"] = self.label
            kwargs["tlcorner"] = u"\N{BOX DRAWINGS LIGHT DOWN AND HORIZONTAL}"
            kwargs["trcorner"] = u"\N{BOX DRAWINGS LIGHT DOWN AND LEFT}"

        w = self.fill
        if self.border:
           w = urwid.LineBox(w, **kwargs)

        if self.auto_complete:
            self.auto_complete_bar = AutoCompleteBar()

            urwid.connect_signal(self.auto_complete_bar,
                                 "change",
                                 lambda source, text: self.complete())

            urwid.connect_signal(self.auto_complete_bar,
                                 "close",
                                 lambda source, text: self.complete_off())

        self.pile = urwid.Pile([
            ("weight", 1, w),
        ])
        self.__super.__init__(self.pile)

    @property
    def filter_text(self):
        return self.auto_complete_bar.text.get_text()[0]

    @filter_text.setter
    def filter_text(self, value):
        return self.auto_complete_bar.set_text(value)

    @property
    def max_item_width(self):
        # logger.debug("max: %s" %(max(w.width for w in self)))
        if not len(self):
            return self.min_width
        return max(w.width for w in self)

    @property
    def width(self):
        width = self.max_item_width
        if self.border:
            width += 2
        # if self.scrollbar:
        #     width += 1
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
        logger.debug("set pos")
        self.dropdown_buttons.listbox.set_focus_valign("top")
        self.dropdown_buttons.focus_position = pos

    @property
    def selection(self):
        return self.dropdown_buttons.selection

    def select_button(self, button):
        # (label, value) = label_value
        label = button.label
        value = button.value
        self.selected_button = self.focus_position
        # self.drop_down.make_selection(label, value)
        # self.dropdown_buttons.listbox.set_focus_valign("top")
        self._emit("close")

    def keypress(self, size, key):
        if self.auto_complete and key in ["/", "?"]:
            self.complete_on(case_sensitive=False, anywhere = (key == "?"))

        elif key == "esc":
            self.cancel()

        elif self.completing:
            if key in ["enter", "up", "down"]:
                self.complete_off()
            else:
                return super(DropdownDialog, self).keypress(size, key)

        else:
            key = super(DropdownDialog, self).keypress(size, key)
            self[self.focus_position].unhighlight()
            return key

    @property
    def selected_value(self):

        return self.body[self.focus_position].value


    def complete_on(self, case_sensitive=False, anywhere=False):

        if self.completing:
            return
        self.completing = True
        # self.auto_complete_bar.set_prompt("> ")
        # self.pile.focus_position = 1
        self.show_bar()
        if anywhere:
            self.complete_anywhere = True
        else:
            self.complete_anywhere = False


    def complete_off(self):

        if not self.completing:
            return
        self.filter_text = ""

        self.hide_bar()
        self.completing = False

    def complete(self, case_sensitive=False):

        self[self.focus_position].unhighlight()
        if not self.filter_text:
            return

        if case_sensitive:
            g = lambda x: x
        else:
            g = lambda x: str(x).lower()

        if self.complete_anywhere:
            f = lambda x: g(self.filter_text) in g(x)
        else:
            f = lambda x: g(x).startswith(g(self.filter_text))

        for i, w in enumerate(self.body):
            if f(w):
                self[i].highlight_text(self.filter_text)
                self.focus_position = i
                break

    def cancel(self):
        self.focus_position = self.selected_button
        self.close()

    def close(self):
        self._emit("close")

    def show_bar(self):
        self.pile.contents.append(
            (self.auto_complete_bar, self.pile.options("given", 1))
        )
        self.pile.focus_position = 1

    def hide_bar(self):
        self[self.focus_position].unhighlight()
        self.pile.focus_position = 0
        del self.pile.contents[1]

class Dropdown(urwid.PopUpLauncher):

    # Based in part on SelectOne widget from
    # https://github.com/tuffy/python-audio-tools

    empty_label = u"\N{EMPTY SET}"
    margin = 0

    def __init__(
            self, items,
            selected_value=None,
            label=None, border=False, scrollbar = False,
            margin = None,
            left_chars = None, right_chars = None,
            left_chars_top = None, right_chars_top = None,
            auto_complete = False,
            arrow_cycle = False
    ):

        self.items = items
        self.label = label
        self.border = border
        self.scrollbar = scrollbar
        self.auto_complete = auto_complete
        self.arrow_cycle = arrow_cycle

        if margin:
            self.margin = margin

        if isinstance(self.items, list):
            self.items = { item: n for n, item in enumerate(items) }

        self.selected_value = None  # set by make_selection, below

        self.button = DropdownItem(
            u"", None,
            margin=self.margin,
            left_chars = left_chars_top if left_chars_top else left_chars,
            right_chars = right_chars_top if right_chars_top else right_chars
        )

        self.pop_up = DropdownDialog(
            self,
            self.items,
            self.selected_value,
            label = self.label,
            border = self.border,
            margin = self.margin,
            left_chars = left_chars,
            right_chars = right_chars,
            auto_complete = self.auto_complete,
            scrollbar = scrollbar
        )

        urwid.connect_signal(
            self.pop_up,
            "select",
            lambda souce, selection: self.select(selection)
        )

        urwid.connect_signal(
            self.pop_up,
            "close",
            lambda button: self.close_pop_up()
        )

        try:
            initial_index = next(
                v for v in self.items.items()
                if v == self.selected_value)
            self.focus_position = initial_index
        except StopIteration:
            initial_index = 0

        if len(self):
            self.select(self.selection)
        else:
            self.button.set_label(("dropdown_text", self.empty_label))

        cols = [ (self.button_width, self.button) ]

        if self.label:
            cols[0:0] = [
                ("pack", urwid.Text([("dropdown_label", "%s: " %(self.label))])),
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

    def keypress(self, size, key):
        # key = super(Dropdown, self).keypress(size, key)
        if self.arrow_cycle and key in ["up", "down"]:
            self.cycle(-1 if key == "up" else 1)
        elif key in ["page up", "page down"]:
            h = self.pop_up.height
            self.cycle(-h if key == "page up" else h)
        elif key == "home":
            self.focus_position = 0
        elif key == "end":
            self.focus_position = len(self)-1
        elif self.auto_complete and key in ["/", "?"]:
            self.open_pop_up()
            self.pop_up.keypress(size, key)

        else:
            return super(Dropdown, self).keypress(size, key)

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
        logger.debug("%s, %s" %(self.pop_up.width, w))
        return max(self.pop_up.width, w)

    @property
    def width(self):
        width = max(self.contents_width, self.pop_up.width)
        # width = max(self.pop_up.width, contents_width)
        # if self.label:
        #     width += len(self.label) + 2
        if self.border:
            width += 2
        return width

    @property
    def height(self):
        height = self.pop_up.height + 1
        return height

    def open_pop_up(self):
        # print("open")
        super(Dropdown, self).open_pop_up()

    def close_pop_up(self):
        self.selected_value = self.pop_up.selected_value
        super(Dropdown, self).close_pop_up()

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
        # self.select_index(pos)
        self.pop_up.selected_button = self.pop_up.focus_position = pos
        self.select(self.selection)

    @property
    def selection(self):
        return self.pop_up.selection

    def cycle(self, n):
        pos = self.focus_position + n
        if pos > len(self) - 1:
            pos = len(self) - 1
        elif pos < 0:
            pos = 0
        # self.focus_position = pos
        self.focus_position = pos

    def select(self, button):
        self.button.set_label(("dropdown_text", button.label))
        self.pop_up.dropdown_buttons.listbox.set_focus_valign("top")

    def set_items(self, items, selected_value):
        self.items = items
        self.make_selection([label for (label, value) in items if
                             value is selected_value][0],
                            selected_value)
    def __len__(self):
        return len(self.items)

def main():

    data = dict([('Adipisci eius dolore consectetur.', 34),
            ('Aliquam consectetur velit dolore', 19),
            ('Amet ipsum quaerat numquam.', 25),
            ('Amet quisquam labore dolore.', 30),
            ('Amet velit consectetur.', 20),
            ('Consectetur consectetur aliquam voluptatem', 23),
            ('Consectetur ipsum aliquam.', 28),
            ('Consectetur sit neque est', 15),
            ('Dolore voluptatem etincidunt sit', 40),
            ('Dolorem porro tempora tempora.', 37),
            ('Eius numquam dolor ipsum', 26),
            ('Eius tempora etincidunt est', 12),
            ('Est adipisci numquam adipisci', 7),
            ('Est aliquam dolor.', 38),
            ('Etincidunt amet quisquam.', 33),
            ('Etincidunt consectetur velit.', 29),
            ('Etincidunt dolore eius.', 45),
            ('Etincidunt non amet.', 14),
            ('Etincidunt velit adipisci labore', 6),
            ('Ipsum magnam velit quiquia', 21),
            ('Ipsum modi eius.', 3),
            ('Labore voluptatem quiquia aliquam', 18),
            ('Magnam etincidunt porro magnam', 39),
            ('Magnam numquam amet.', 44),
            ('Magnam quisquam sit amet.', 27),
            ('Magnam voluptatem ipsum neque', 32),
            ('Modi est ipsum adipisci', 2),
            ('Neque eius voluptatem voluptatem', 42),
            ('Neque quisquam ipsum.', 10),
            ('Neque quisquam neque.', 48),
            ('Non dolore voluptatem.', 41),
            ('Non numquam consectetur voluptatem.', 35),
            ('Numquam eius dolorem.', 43),
            ('Numquam sed neque modi', 9),
            ('Porro voluptatem quaerat voluptatem', 11),
            ('Quaerat eius quiquia.', 17),
            ('Quiquia aliquam etincidunt consectetur.', 0),
            ('Quiquia ipsum sit.', 49),
            ('Quiquia non dolore quiquia', 8),
            ('Quisquam aliquam numquam dolore.', 1),
            ('Quisquam dolorem voluptatem adipisci.', 22),
            ('Sed magnam dolorem quisquam', 4),
            ('Sed tempora modi est.', 16),
            ('Sit aliquam dolorem.', 46),
            ('Sit modi dolor.', 31),
            ('Sit quiquia quiquia non.', 5),
            ('Sit quisquam numquam quaerat.', 36),
            ('Tempora etincidunt quiquia dolor', 13),
            ('Tempora velit etincidunt.', 24),
            ('Velit dolor velit.', 47)])

    NORMAL_FG = 'light gray'
    NORMAL_BG = 'black'

    if os.environ["DEBUG"]:
        import logging
        global logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s [%(levelname)8s] %(message)s",
                                      datefmt='%Y-%m-%d %H:%M:%S')
        fh = logging.FileHandler("dropdown.log")
        fh.setFormatter(formatter)
        logger.addHandler(fh)


    entries = {
        "dropdown_text": PaletteEntry(
            foreground = "light gray",
            background = "dark blue",
            foreground_high = "light gray",
            background_high = "#003",
        ),
        "dropdown_focused": PaletteEntry(
            foreground = "white",
            background = "light blue",
            foreground_high = "white",
            background_high = "#009",
        ),
        "dropdown_highlight": PaletteEntry(
            foreground = "yellow",
            background = "light blue",
            foreground_high = "yellow",
            background_high = "#009",
        ),
        "dropdown_label": PaletteEntry(
            foreground = "white",
            background = "black"
        ),
        "dropdown_prompt": PaletteEntry(
            foreground = "light blue",
            background = "black"
        ),
    }

    entries = DataTable.get_palette_entries(user_entries=entries)
    # raise Exception(entries["dropdown_text"])
    palette = Palette("default", **entries)
    screen = urwid.raw_display.Screen()
    screen.set_terminal_properties(256)

    boxes = [
        Dropdown(
            data,
            label="Foo",
            border = True,
            scrollbar = True,
            right_chars_top = u" \N{BLACK DOWN-POINTING TRIANGLE}",
            auto_complete = True,
            arrow_cycle = True
        ),

        Dropdown(
            data,
            border = False,
            margin = 2,
            left_chars = u"\N{LIGHT LEFT TORTOISE SHELL BRACKET ORNAMENT}",
            right_chars = u"\N{LIGHT RIGHT TORTOISE SHELL BRACKET ORNAMENT}",
            auto_complete = True
        ),
        Dropdown(
            data,
            selected_value = list(data.values())[10],
            label="Foo",
            border = True,
            scrollbar = False,
            auto_complete = False,
            arrow_cycle = True
        ),
        Dropdown(
            [],
        ),
    ]

    grid = urwid.GridFlow(
        [ urwid.Padding(b) for b in boxes],
        60, 1, 1, "left"
    )

    main = urwid.Frame(urwid.Filler(grid))

    def global_input(key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        else:
            return False


    loop = urwid.MainLoop(main,
                          palette,
                          screen=screen,
                          unhandled_input=global_input,
                          pop_ups=True
    )
    loop.run()

if __name__ == "__main__":
    main()

__all__ = ["Dropdown"]
