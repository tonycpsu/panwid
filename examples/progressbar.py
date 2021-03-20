#!/usr/bin/env python3

import urwid
from urwid_utils.palette import *
import random
from itertools import chain, repeat, islice

from panwid.sparkwidgets import *
from panwid.progressbar import *

screen = urwid.raw_display.Screen()
screen.set_terminal_properties(1<<24)

LABEL_COLOR_DARK = "black"
LABEL_COLOR_LIGHT = "white"

entries = {}


all_colors = [ urwid.display_common._color_desc_256(x)
                   for x in range(32,224) ]
random_colors = [ random.choice(all_colors) for i in range(16) ]

label_colors = [ LABEL_COLOR_DARK, LABEL_COLOR_LIGHT ]

entries.update(
    get_palette_entries(
        label_colors = label_colors
    )
)

entries.update(
    get_palette_entries(
        chart_colors = random_colors,
        label_colors = label_colors
    )
)


for fcolor in random_colors + label_colors:

    entries.update({
        fcolor: PaletteEntry(
            mono = "white",
            foreground = (fcolor
                          if fcolor in urwid.display_common._BASIC_COLORS
                          else "white"),
            background = "black",
            foreground_high = fcolor,
            background_high = "black"
        ),
    })

    for bcolor in random_colors:

        entries.update({
            "%s:%s" %(fcolor, bcolor): PaletteEntry(
                mono = "white",
                foreground = (fcolor
                              if fcolor in urwid.display_common._BASIC_COLORS
                              else "white"),
                background = (bcolor
                              if bcolor in urwid.display_common._BASIC_COLORS
                              else "black"),
                foreground_high = fcolor,
                background_high = bcolor
            ),
        })

palette = Palette("default", **entries)

progress = None

progress_text = urwid.Filler(urwid.Text(""))
progress_ph = urwid.WidgetPlaceholder(urwid.Text(""))

def intersperse(delimiter, seq):
    return islice(chain.from_iterable(zip(repeat(delimiter), seq)), 1, None)

def get_random_progress():

    return ProgressBar(
        width=random.randint(10, 100),
        maximum=random.randint(200, 300),
        value=random.randint(0, 100),
        # maximum=90,
        # value=0,
        progress_color="light red",
        remaining_color="light green"
    )

def randomize_progress():
    global progress
    progress = get_random_progress()
    filler = urwid.Filler(progress)
    # values = list(intersperse(",", [(i.value, "%s" %(i.value)) for i in progress.items]))
    progress_text.original_widget.set_text(f"{progress.value}, {progress.maximum}")
    progress_ph.original_widget = filler

def cycle_progress(step):
    global progress
    # values = list(intersperse(",", [(i.value, "%s" %(i.value)) for i in progress.items]))
    value = max(min(progress.value + step, progress.maximum), 0)
    progress.set_value(value)
    progress_text.original_widget.set_text(f"{progress.value}, {progress.maximum}")


def main():

    pile = urwid.Pile([
        (2, progress_text),
        (2, progress_ph),
    ])

    randomize_progress()

    def keypress(key):

        if key == "q":
            raise urwid.ExitMainLoop()
        elif key == " ":
            randomize_progress()
        elif key == "left":
            cycle_progress(-1)
        elif key == "right":
            cycle_progress(1)
        elif key == "down":
            cycle_progress(-10)
        elif key == "up":
            cycle_progress(10)
        else:
            return key


    loop = urwid.MainLoop(
        pile,
        palette=palette,
        screen=screen,
        unhandled_input=keypress
    )

    loop.run()

if __name__ == "__main__":
    main()
