#!/usr/bin/python

import urwid
from urwid_utils.palette import *
import random
from itertools import chain, repeat, islice
from panwid.sparkwidgets import *


screen = urwid.raw_display.Screen()
screen.set_terminal_properties(1<<24)

LABEL_COLOR_DARK = "black"
LABEL_COLOR_LIGHT = "white"

entries = {}

all_colors = [ urwid.display_common._color_desc_256(x)
                   for x in range(32,224) ]
random_colors = [ random.choice(all_colors) for i in range(1,15) ]

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


def intersperse(delimiter, seq):
    return islice(chain.from_iterable(zip(repeat(delimiter), seq)), 1, None)


# raise Exception(entries)
palette = Palette("default", **entries)

spark1 = urwid.Filler(SparkColumnWidget(list(range(0, random.randint(1, 20)))))
spark2 = urwid.Filler(SparkColumnWidget(list(range(0, 100)), color_scheme="rotate_16", scale_min=20, scale_max=90))
spark3 = urwid.Filler(SparkColumnWidget([5*random.random() for i in range(0, 100)], color_scheme="rotate_true"))
spark4 = urwid.Filler(SparkColumnWidget(list(range(-5, 100)), color_scheme="signed", underline="negative"))
custom_scheme ={ "mode": "rotate",  "colors": ["dark cyan", "brown", "dark magenta"]}
spark5 = urwid.Filler(SparkColumnWidget(list(range(1, 20)), color_scheme=custom_scheme))

spark_random_text = urwid.Filler(urwid.Text(""))
spark_random_ph = urwid.WidgetPlaceholder(urwid.Text(""))



bark1 = urwid.Filler(SparkBarWidget([30, 30, 30], random.randint(10, 40), color_scheme="rotate_16"))
bark2 = urwid.Filler(SparkBarWidget([40, 30, 20, 10], random.randint(10, 60), color_scheme="rotate_true"))
bark3 = urwid.Filler(SparkBarWidget([0, 0, 0], random.randint(1, 10), color_scheme="rotate_true"))
bark4 = urwid.Filler(SparkBarWidget([19, 42, 17], random.randint(1, 5), color_scheme="rotate_true"))
bark5 = urwid.Filler(SparkBarWidget([
    SparkBarItem(19, bcolor="light red", label="\u2588"*2, fcolor="yellow"),
    SparkBarItem(42, bcolor="light green", label="bar", align="^"),
    SparkBarItem(17, bcolor="light blue", label="baz", align=">")
], random.randint(1, 60), fit_label=True))
bark6 = urwid.Filler(SparkBarWidget(
    [
        SparkBarItem(0, bcolor="light green", label=0, fcolor="dark red"),
        SparkBarItem(6, bcolor="light blue",label=6, fcolor="dark red", align=">")
    ],
    random.randint(10, 30), color_scheme="rotate_256", min_width=5))
bark6=urwid.Filler(SparkBarWidget(
    [SparkBarItem(value=1, label='  1', fcolor='black', bcolor='dark green', align='<'),
     SparkBarItem(value=13, label='☼ 14', fcolor='black', bcolor='dark blue', align='>'),
     SparkBarItem(value=0, label='✓  0', fcolor='black', bcolor='light blue', align='>'),
     SparkBarItem(value=50, label='↓ 50', fcolor='black', bcolor='dark red', align='>'),
     SparkBarItem(value=2802, label='🌐2852', fcolor='black', bcolor='dark gray', align='>')
     ], width=130, fit_label=True))
# raise Exception
bark_random_text = urwid.Filler(urwid.Text(""))
bark_random_ph = urwid.WidgetPlaceholder(urwid.Text(""))


progress_random_text = urwid.Filler(urwid.Text(""))
progress_random_ph = urwid.WidgetPlaceholder(urwid.Text(""))


def get_label_color(color,
                    dark=DEFAULT_LABEL_COLOR_DARK,
                    light=DEFAULT_LABEL_COLOR_LIGHT):
    # http://jsfiddle.net/cu4z27m7/66/
    (r, g, b) = urwid.AttrSpec(color, color).get_rgb_values()[:3]
    colors = [r / 255, g / 255, b / 255]
    c = [ (c / 12.92)
          if c < 0.03928
          else ((c + 0.055) / 1.055)**2.4
          for c in colors ]

    L = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    return dark if L > 0.179 else light


def get_random_spark():
    return SparkColumnWidget([
        (random_colors[i%len(random_colors)],
         random.randint(1, 100),
        )
        for i in range(random.randint(2, 32))
    ], underline="min", overline="max")

def get_random_bark():
    num = random.randint(1, 10)
    bcolors = [random_colors[i%len(random_colors)] for i in range(num)]
    lcolors = [
        get_label_color(bcolor)
        for bcolor in bcolors
    ]
    # raise Exception(lcolors)
    # r, g, b = a.get_rgb_values()[:3]
    # lcolor = get_label_color(r, g, b)
    randos = [random.randint(50,150) for i in range(0, num)]
    return SparkBarWidget([
        SparkBarItem(
            randos[i],
            bcolor=bcolors[i],
            label=("%s {value} ({pct}%%)" %(chr(65+i if i < 26 else 71 + i))),
            fcolor=lcolors[i]
        )
        for i in range(0, num)
    ], fit_label=True, width=random.randint(10, 80), label_color="black", normalize=(1, 100),
                                       min_width=random.randint(0, 5))

def randomize_spark():
    spark = get_random_spark()
    filler = urwid.Filler(spark)
    values = list(intersperse(",", [(i[0], "%s" %(i[1])) for i in spark.items]))
    spark_random_text.original_widget.set_text(values)
    spark_random_ph.original_widget = filler

def randomize_bark():
    bark = get_random_bark()
    filler = urwid.Filler(bark)
    values = list(intersperse(",", [(i.value, "%s" %(i.value)) for i in bark.items]))
    bark_random_text.original_widget.set_text(values)
    bark_random_ph.original_widget = filler

def main():

    pile = urwid.Pile([
        (2, spark1),
        (2, spark2),
        (2, spark3),
        (2, spark4),
        (2, spark5),
        (2, spark_random_text),
        (2, spark_random_ph),
        (2, bark1),
        (2, bark2),
        (2, bark3),
        (2, bark4),
        (2, bark5),
        (2, bark6),
        (2, bark_random_text),
        (2, bark_random_ph)
    ])

    randomize_bark()
    randomize_spark()

    def keypress(key):

        if key == "b":
            randomize_bark()
        elif key == "s":
            randomize_spark()
        elif key == " ":
            randomize_bark()
            randomize_spark()
        elif key == "q":
            raise urwid.ExitMainLoop()
        else:
            return key


    loop = urwid.MainLoop(
        pile,
        palette = palette,
        screen = screen,
        unhandled_input = keypress
    )

    loop.run()

if __name__ == "__main__":
    main()
