import urwid
import urwid.raw_display
import os
import random
import string
import re
from urwid_utils.palette import *
from .datatable import *
from .datatable.listbox import ScrollingListBox

class ComboButton(urwid.Button):

    button_left_text = u"\N{LIGHT LEFT TORTOISE SHELL BRACKET ORNAMENT}"
    button_right_text = u"\N{LIGHT RIGHT TORTOISE SHELL BRACKET ORNAMENT}"

    # button_left_text = ""
    # button_right_text = ""

    button_left = urwid.Text(button_left_text)
    button_right = urwid.Text(button_right_text)

    def __init__(self, label, value, on_press=None, user_data=None):

        self.label_text = label
        self.value = value
        self._label = urwid.SelectableIcon("", 0)
        self.attr = urwid.AttrMap(self._label, {})
        self.attr.set_focus_map({"combo_text": "combo_focused"})
        self.cols = urwid.Columns([
            (len(self.button_left_text), self.button_left),
            self.attr,
            (len(self.button_right_text), self.button_right)
        ], dividechars=0)

        # The old way of listening for a change was to pass the callback
        # in to the constructor.  Just convert it to the new way:
        if on_press:
            urwid.connect_signal(self, 'click', on_press, user_data)

        self.set_label(("combo_text", self.label_text))
        super(urwid.Button, self).__init__(self.cols)

    @property
    def width(self):

        return (
            len(self.button_left.get_text()[0])
            + len(self.label)
            + len(self.button_right.get_text()[0])
        )

    def __str__(self):
        return self.label_text

    def __contains__(self, s):
        return s in self.label_text

    def startswith(self, s):
        return self.label_text.startswith(s)

    def highlight_text(self, s, case_sensitive=False):

        # (a, b, c) = self.label_text.partition(s)
        (a, b, c) = re.search(
            "(.*?)(%s)(.*)" %(s),
            self.label_text,
            re.IGNORECASE if not case_sensitive else 0
        ).groups()
        self.set_label([
            ("combo_text", a),
            ("combo_highlight", b),
            ("combo_text", c),
        ])

    def unhighlight(self):
        self.set_label(("combo_text", self.label_text))

class ComboButtons(urwid.WidgetWrap):

    signals = ["select"]

    def __init__(self,
                 widget_list,
                 scrollbar = False,
                 focus_item=None,
                 cancelled=None,
                 auto_complete=False,
                 max_height=10):
        """cancelled is a callback which is called
        when the esc key is pressed
        it takes no arguments"""

        self.widget_list = widget_list
        self.auto_complete = auto_complete
        self.max_height = max_height

        # self.listbox = urwid.ListBox(self.widget_list)
        self.listbox = ScrollingListBox(self.widget_list, with_scrollbar=scrollbar)

        urwid.connect_signal(
            self.listbox,
            'select',
            lambda source, selection: self._emit("select", selection)
        )

        self.box = urwid.BoxAdapter(self.listbox, self.height)
        super(ComboButtons, self).__init__(self.box)
        self.cancelled = cancelled

    def keypress(self, size, key):
        key = super(ComboButtons, self).keypress(size, key)
        if (key == "esc"):
            self.cancel()
        return key

    def cancel(self):
        if self.cancelled is not None:
            self.cancelled()

    @property
    def width(self):
        return max(w.width for w in self.widget_list)

    @property
    def height(self):
        return min(len(self.widget_list), self.max_height)

    @property
    def body(self):
        return self.listbox.body

    def __getitem__(self, i):
        return self.body[i]

    @property
    def focus_position(self):
        return self.listbox.focus_position

    @focus_position.setter
    def focus_position(self, pos):
        self.listbox.focus_position = pos

class AutoCompleteEdit(urwid.Edit):

    signals = ["close"]

    def kepyress(self, size, key):
        if key == "enter":
            self._emit("close")
        return self.text.keypress(size, key)


class AutoCompleteBar(urwid.WidgetWrap):

    signals = ["change", "close"]
    def __init__(self):

        self.prompt = urwid.Text(("combo_prompt", "> "))
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

        self.prompt.set_text(("combo_prompt", text))

    def set_text(self, text):

        self.text.set_edit_text(text)

    # def selectable(self):
    #     return True

    # def kepyress(self, size, key):
    #     if key == "enter":
    #         return
    #     return self.text.keypress(size, key)

    def text_changed(self, source, text):
        self._emit("change", text)

class ComboBoxDialog(urwid.WidgetWrap):
    signals = ['close']

    def __init__(
            self, select_one, items, selected_value,
            label=None, border=False, scrollbar=False,
            auto_complete=False,
    ):
        self.select_one = select_one
        self.items = items
        self.label = label
        self.border = border
        self.scrollbar = scrollbar
        self.auto_complete = auto_complete

        self.completing = False
        self.complete_anywhere = False

        self.selected_button = 0
        # self.selected_value = selected_value
        buttons = []
        for (i, (l, value)) in enumerate(items):
            # buttons.append(ComboButton(label=l,
            #                             value = value,
            #                             on_press=self.select_button,
            # ))
            buttons.append(
                ComboButton(label=l, value = value)
            )

            if value == selected_value:
                self.selected_button = i

        self.combo_buttons = ComboButtons(
            buttons,
            # focus_item = self.selected_value
            scrollbar = scrollbar,
            cancelled = self.cancel,
            auto_complete = self.auto_complete
        )

        urwid.connect_signal(
            self.combo_buttons,
            'select',
            lambda source, selection: self.select_button(selection)
        )


        self.fill = urwid.Filler(self.combo_buttons)
        kwargs = {}
        if self.label is not None:
            kwargs["title"] = self.label
            kwargs["tlcorner"] = u"\N{BOX DRAWINGS LIGHT DOWN AND HORIZONTAL}"
            kwargs["trcorner"] = u"\N{BOX DRAWINGS LIGHT DOWN AND LEFT}"

        w = self.fill
        if self.border:
           w = urwid.LineBox(w, **kwargs)

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
    def max_width(self):
        return self.combo_buttons.width

    @property
    def width(self):
        width = self.combo_buttons.width
        if self.border:
            width += 2
        if self.scrollbar:
            width += 1
        return width

    @property
    def height(self):
        height = self.combo_buttons.height
        if self.border:
            height += 2
        return height

    @property
    def body(self):
        return self.combo_buttons.body

    def __getitem__(self, i):
        return self.body[i]

    @property
    def focus_position(self):
        return self.combo_buttons.focus_position

    @focus_position.setter
    def focus_position(self, pos):
        # self.combo_buttons.listbox.set_focus_valign("top")
        self.combo_buttons.focus_position = pos

    def select_button(self, button):
        # (label, value) = label_value
        label = button.label
        value = button.value
        self.selected_button = self.focus_position
        self.select_one.make_selection(label, value)
        self.combo_buttons.listbox.set_focus_valign("top")
        self._emit("close")

    def keypress(self, size, key):
        # if (key == "esc") and (self.cancelled is not None):
        #     self.complete_off()
        #     self.cancelled()
        #     return
        if key in ["/", "?"]:
            self.complete_on(case_sensitive=False, anywhere = (key == "?"))

        elif key == "*":
            raise Exception(self.focus_position)

        elif self.completing:
            # if key and len(key) == 1 and key in string.printable:
            #     self.filter_text = self.filter_text + key
            #     self.auto_complete_bar.set_text(self.filter_text)
            #     self.complete(anywhere=self.complete_anywhere)
            if key in ["enter", "up", "down"]:
                self.complete_off()
                # self.pile.focus_position = 0
                # return key
            else:
                return super(ComboBoxDialog, self).keypress(size, key)

        # elif key == "enter":
        #     self.selected_button = self.focus_position
        #     self._emit("select")
        else:
            key = super(ComboBoxDialog, self).keypress(size, key)
            # key = self.menu.keypress(size, key)
            self[self.focus_position].unhighlight()
            # self.filter_text = ""
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


    def complete_off(self):

        if not self.completing:
            return
        self.filter_text = ""
        # self.auto_complete_bar.set_prompt("")
        # self.auto_complete_bar.set_text("")
        self.hide_bar()
        self.completing = False

    def complete(self, anywhere=False, case_sensitive=False):

        self[self.focus_position].unhighlight()
        if not self.filter_text:
            return

        if case_sensitive:
            g = lambda x: x
        else:
            g = lambda x: str(x).lower()

        if anywhere:
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
        # self.focus_position = self.selected_button
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

class ComboBox(urwid.PopUpLauncher):

    # Based in part on SelectOne widget from
    # https://github.com/tuffy/python-audio-tools

    def __init__(
            self, items,
            selected_value=None, on_change=None,
            label=None, border=False, scrollbar = False,
            auto_complete = False,
            user_data=None,):
        """items is a list of (unicode, value) tuples
        where value can be any sort of object
        selected_value is a selected object
        on_change is a callback which takes a new selected object
        which is called as on_change(new_value, [user_data])
        label is a unicode label string for the selection box"""

        self.items = items
        self.label = label
        self.border = border
        self.scrollbar = scrollbar
        self.auto_complete = auto_complete

        self.selected_value = None  # set by make_selection, below

        self.button = ComboButton(u"", None)

        self.pop_up = ComboBoxDialog(
            self,
            self.items,
            self.selected_value,
            label = self.label,
            border = self.border,
            scrollbar = scrollbar,
            auto_complete = self.auto_complete
        )
        urwid.connect_signal(
            self.pop_up,
            'close',
            lambda button: self.close_pop_up())


        self.__on_change__ = None
        self.__user_data__ = None

        if selected_value is not None:
            try:
                (label, value) = [pair for pair in items
                                  if pair[1] == selected_value][0]
            except IndexError:
                (label, value) = items[0]
        else:
            (label, value) = items[0]

        self.make_selection(label, value)

        self.__on_change__ = on_change
        self.__user_data__ = user_data

        # cols = [ (self.pop_up.max_width, self.button) ]
        cols = [ (self.pop_up.max_width, self.button) ]

        if self.label:
            cols[0:0] = [
                ("pack", urwid.Text([("combo_label", "%s: " %(self.label))])),
            ]
        self.columns = urwid.Columns(cols, dividechars=0)

        w = self.columns
        if self.border:
            w = urwid.LineBox(self.columns)
        w = urwid.Padding(w, width=self.width)

        # w = urwid.BoxAdapter(urwid.Filler(w), self.height)
        super(ComboBox, self).__init__(w)
        urwid.connect_signal(
            self.button,
            'click',
            lambda button: self.open_pop_up()
        )

        assert(len(items) > 0)

    def keypress(self, size, key):
        # key = super(ComboBox, self).keypress(size, key)
        if key in ["up", "down"]:
            self.cycle(-1 if key == "up" else 1)
        elif key in ["page up", "page down"]:
            h = self.pop_up.height
            self.cycle(-h if key == "page up" else h)
        elif key == "home":
            self.select(0)
        elif key == "end":
            self.select(len(self)-1)
        elif key in ["/", "?"]:
            self.open_pop_up()
            self.pop_up.keypress(size, key)
        else:
            return super(ComboBox, self).keypress(size, key)

    def create_pop_up(self):
        # print("create")
        return self.pop_up

    @property
    def width(self):
        width = self.pop_up.width
        if self.label:
            width += len(self.label) + 2
        # if self.border:
        #     width += 2
        return width

    @property
    def height(self):
        height = self.pop_up.height + 1
        return height

    def open_pop_up(self):
        # print("open")
        super(ComboBox, self).open_pop_up()

    def close_pop_up(self):
        self.selected_value = self.pop_up.selected_value
        super(ComboBox, self).close_pop_up()

    def get_pop_up_parameters(self):
        return {'left': (len(self.label) + 2 if self.label else 0),
                'top': 0,
                'overlay_width': self.pop_up.width,
                'overlay_height': self.pop_up.height
        }

    @property
    def focus_position(self):
        return self.pop_up.focus_position

    @focus_position.setter
    def focus_position(self, pos):
        self.pop_up.selected_button = self.pop_up.focus_position = pos

    def cycle(self, n):
        pos = self.focus_position + n
        if pos > len(self) - 1:
            pos = len(self) - 1
        elif pos < 0:
            pos = 0
        # self.focus_position = pos
        self.select(pos)

    def make_selection(self, label, value):
        self.button.set_label(("combo_text", label))
        self.selected_value = value
        if self.__on_change__ is not None:
            if self.__user_data__ is not None:
                self.__on_change__(value, self.__user_data__)
            else:
                self.__on_change__(value)

    def select(self, index):
        self.focus_position = index
        self.make_selection(*self.items[index])


    def set_items(self, items, selected_value):
        self.items = items
        self.make_selection([label for (label, value) in items if
                             value is selected_value][0],
                            selected_value)
    def __len__(self):
        return len(self.items)

def main():

    data = [('Adipisci eius dolore consectetur.', 34),
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
            ('Velit dolor velit.', 47)]

    NORMAL_FG = 'light gray'
    NORMAL_BG = 'black'

    # import logging
    # global logger
    # logger = logging.getLogger(__name__)
    # logger.setLevel(logging.DEBUG)
    # formatter = logging.Formatter("%(asctime)s [%(levelname)8s] %(message)s",
    #                               datefmt='%Y-%m-%d %H:%M:%S')
    # fh = logging.FileHandler("combobox.log")
    # fh.setFormatter(formatter)
    # logger.addHandler(fh)


    entries = {
        "combo_text": PaletteEntry(
            foreground = "dark green",
            background = "black"
        ),
        "combo_focused": PaletteEntry(
            foreground = "light green",
            background = "black"
        ),
        "combo_label": PaletteEntry(
            foreground = "white",
            background = "black"
        ),
        "combo_highlight": PaletteEntry(
            foreground = "yellow",
            background = "black"
        ),
        "combo_prompt": PaletteEntry(
            foreground = "light blue",
            background = "black"
        ),
    }

    entries = DataTable.get_palette_entries(user_entries=entries)
    palette = Palette("default", **entries)
    screen = urwid.raw_display.Screen()
    screen.set_terminal_properties(256)

    boxes = [
        ComboBox(
            data,
            label="Foo",
            border = True,
            scrollbar = True,
            auto_complete = True
        ),

        ComboBox(
            data,
            border = False,
            auto_complete = True
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
