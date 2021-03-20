import logging
logger = logging.getLogger()
import os

import urwid
import urwid.raw_display
from urwid_utils.palette import *
from orderedattrdict import AttrDict

import panwid.keymap

panwid.keymap.KEYMAP_GLOBAL = {
    "movement": {
        "up": "up",
        "down": "down",
    },
    "dropdown": {
        "k": "up",
        "j": "down",
        "page up": "page up",
        "page down": "page down",
        "ctrl up": ("cycle", [1]),
        "ctrl down": ("cycle", [-1]),
        "home": "home",
        "end": "end",
        "/": "complete prefix",
        "?": "complete substring",
        "ctrl p": "complete_prev",
        "ctrl n": "complete_next",
    },
    "auto_complete_edit": {
        "enter": "confirm",
        "esc": "cancel",
        "/": "complete prefix",
        "?": "complete substring",
        "ctrl p": "complete_prev",
        "ctrl n": "complete_next",
    }
}


from panwid.dropdown import *
from panwid.listbox import *
from panwid.keymap import *

class TestDropdown(KeymapMovementMixin, Dropdown):
    pass

def main():

    data = AttrDict([('Adipisci eius dolore consectetur.', 34),
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

    if os.environ.get("DEBUG"):
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s [%(module)16s:%(lineno)-4d] [%(levelname)8s] %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh = logging.FileHandler("dropdown.log")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        logger.addHandler(logging.NullHandler())

    entries = Dropdown.get_palette_entries()
    entries.update(ScrollingListBox.get_palette_entries())
    palette = Palette("default", **entries)
    screen = urwid.raw_display.Screen()
    screen.set_terminal_properties(256)

    boxes = [
        TestDropdown(
            data,
            label="Foo",
            border = True,
            scrollbar = True,
            right_chars_top = u" \N{BLACK DOWN-POINTING TRIANGLE}",
            auto_complete = True,
        ),

        TestDropdown(
            data,
            border = False,
            margin = 2,
            left_chars = u"\N{LIGHT LEFT TORTOISE SHELL BRACKET ORNAMENT}",
            right_chars = u"\N{LIGHT RIGHT TORTOISE SHELL BRACKET ORNAMENT}",
            auto_complete = True
        ),
        TestDropdown(
            data,
            default = list(data.values())[10],
            label="Foo",
            border = True,
            scrollbar = False,
            auto_complete = False,
        ),
        TestDropdown(
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
