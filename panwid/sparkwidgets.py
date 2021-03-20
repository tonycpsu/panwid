"""
```sparkwidgets```
========================

A set of sparkline-ish widgets for urwid

This module contains a set of urwid text-like widgets for creating tiny but
hopefully useful sparkline-like visualizations of data.
"""

import urwid
from urwid_utils.palette import *
from collections import deque
import math
import operator
import itertools
import collections
from dataclasses import dataclass

BLOCK_VERTICAL = [ chr(x) for x in range(0x2581, 0x2589) ]
BLOCK_HORIZONTAL = [" "] + [ chr(x) for x in range(0x258F, 0x2587, -1) ]

DEFAULT_LABEL_COLOR = "black"
DEFAULT_LABEL_COLOR_DARK = "black"
DEFAULT_LABEL_COLOR_LIGHT = "white"

DEFAULT_BAR_COLOR = "white"

DISTINCT_COLORS_16 = urwid.display_common._BASIC_COLORS[1:]

DISTINCT_COLORS_256 = [
    '#f00', '#080', '#00f', '#d6f', '#0ad', '#f80', '#8f0', '#666',
    '#f88', '#808', '#0fd', '#66f', '#aa8', '#060', '#faf', '#860',
    '#60a', '#600', '#ff8', '#086', '#8a6', '#adf', '#88a', '#f60',
    '#068', '#a66', '#f0a', '#fda'
]

DISTINCT_COLORS_TRUE = [
    '#ff0000', '#008c00', '#0000ff', '#c34fff',
    '#01a5ca', '#ec9d00', '#76ff00', '#595354',
    '#ff7598', '#940073', '#00f3cc', '#4853ff',
    '#a6a19a', '#004301', '#edb7ff', '#8a6800',
    '#6100a3', '#5c0011', '#fff585', '#007b69',
    '#92b853', '#abd4ff', '#7e79a3', '#ff5401',
    '#0a577d', '#a8615c', '#e700b9', '#ffc3a6'
]

COLOR_SCHEMES = {
    "mono": {
        "mode": "mono"
    },
    "rotate_16": {
        "mode": "rotate",
        "colors": DISTINCT_COLORS_16
    },
    "rotate_256": {
        "mode": "rotate",
        "colors": DISTINCT_COLORS_256
    },
    "rotate_true": {
        "mode": "rotate",
        "colors": DISTINCT_COLORS_TRUE
    },
    "signed": {
        "mode": "rules",
        "colors": {
            "nonnegative": "default",
            "negative": "dark red"
        },
        "rules": [
            ( "<", 0, "negative" ),
            ( "else", "nonnegative" ),
        ]
    }
}

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def get_palette_entries(
        chart_colors = None,
        label_colors = None
):

    NORMAL_FG_MONO = "white"
    NORMAL_FG_16 = "light gray"
    NORMAL_BG_16 = "black"
    NORMAL_FG_256 = "light gray"
    NORMAL_BG_256 = "black"

    palette_entries = {}

    if not label_colors:
        label_colors = list(set([
            DEFAULT_LABEL_COLOR,
            DEFAULT_LABEL_COLOR_DARK,
            DEFAULT_LABEL_COLOR_LIGHT
        ]))


    if chart_colors:
        colors = chart_colors
    else:
        colors = (urwid.display_common._BASIC_COLORS
                  + DISTINCT_COLORS_256
                  + DISTINCT_COLORS_TRUE )

    fcolors = colors + label_colors
    bcolors = colors

    for fcolor in fcolors:
        if isinstance(fcolor, PaletteEntry):
            fname = fcolor.name
            ffg = fcolor.foreground
            fbg = NORMAL_BG_16
            ffghi = fcolor.foreground_high
            fbghi = NORMAL_BG_256
        else:
            fname = fcolor
            ffg = (fcolor
                  if fcolor in urwid.display_common._BASIC_COLORS
                  else NORMAL_FG_16)
            fbg = NORMAL_BG_16
            ffghi = fcolor
            fbghi = NORMAL_BG_256

        palette_entries.update({
            fname: PaletteEntry(
                name = fname,
                mono = NORMAL_FG_MONO,
                foreground = ffg,
                background = fbg,
                foreground_high = ffghi,
                background_high = fbghi
            ),
        })

        for bcolor in bcolors:

            if isinstance(bcolor, PaletteEntry):
                bname = "%s:%s" %(fname, bcolor.name)
                bfg = ffg
                bbg = bcolor.background
                bfghi = ffghi
                bbghi = bcolor.background_high
            else:
                bname = "%s:%s" %(fname, bcolor)
                bfg = fcolor
                bbg = bcolor
                bfghi = fcolor
                bbghi = bcolor

            palette_entries.update({
                bname: PaletteEntry(
                    name = bname,
                    mono = NORMAL_FG_MONO,
                    foreground = (bfg
                                  if bfg in urwid.display_common._BASIC_COLORS
                                  else NORMAL_BG_16),
                    background = (bbg
                                  if bbg in urwid.display_common._BASIC_COLORS
                                  else NORMAL_BG_16),
                    foreground_high = bfghi,
                    background_high = bbghi
                ),
            })

    return palette_entries



OPERATOR_MAP = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "=": operator.eq,
    "else": lambda a, b: True
}


class SparkWidget(urwid.Text):

    @staticmethod
    def make_rule_function(scheme):

        rules = scheme["rules"]
        def rule_function(value):
            return scheme["colors"].get(
                next(iter(filter(
                    lambda rule: all(
                        OPERATOR_MAP[cond[0]](value, cond[1] if len(cond) > 1 else None)
                        for cond in [rule]
                    ), scheme["rules"]
                )))[-1]
            )
        return rule_function


    @staticmethod
    def normalize(v, a, b, scale_min, scale_max):

        if scale_max == scale_min:
            return v
        return max(
            a,
            min(
                b,
                (((v - scale_min) / (scale_max - scale_min) ) * (b - a) + a)
            )
        )


    def parse_scheme(self, scheme):

        if isinstance(scheme, dict):
            color_scheme = scheme
        else:
            try:
                color_scheme = COLOR_SCHEMES[scheme]
            except:
                return lambda x: scheme
                # raise Exception("Unknown color scheme: %s" %(scheme))

        mode = color_scheme["mode"]
        if mode == "mono":
            return None

        elif mode == "rotate":
            return deque(color_scheme["colors"])

        elif mode == "rules":
            return self.make_rule_function(color_scheme)

        else:
            raise Exception("Unknown color scheme mode: %s" %(mode))

    @property
    def current_color(self):

        return self.colors[0]

    def next_color(self):
        if not self.colors:
            return
        self.colors.rotate(-1)
        return self.current_color

    def get_color(self, item):
        if not self.colors:
            color = None
        elif callable(self.colors):
            color = self.colors(item)
        elif isinstance(self.colors, collections.Iterable):
            color = self.current_color
            self.next_color()
            return color
        else:
            raise Exception(self.colors)

        return color


class SparkColumnWidget(SparkWidget):
    """
    A sparkline-ish column widget for Urwid.

    Given a list of numeric values, this widget will draw a small text-based
    vertical bar graph of the values, one character per value.  Column segments
    can be colorized according to a color scheme or by assigning each
    value a color.

    :param items: A list of items to be charted in the widget.  Items can be
    either numeric values or tuples, the latter of which must be of the form
    ('attribute', value) where attribute is an urwid text attribute and value
    is a numeric value.

    :param color_scheme: A string or dictionary containing the name of or
    definition of a color scheme for the widget.

    :param underline: one of None, "negative", or "min", specifying values that
    should be marked in the chart.  "negative" shows negative values as little
    dots at the bottom of the chart, while "min" uses a unicode combining
    three dots character to indicate minimum values.  Results of this and the
    rest of these parameters may not look great with all terminals / fonts,
    so if this looks weird, don't use it.

    :param overline: one of None or "max" specfying values that should be marked
    in the chart.  "max" draws three dots above the max value.  See underline
    description for caveats.

    :param scale_min: Set a minimum scale for the chart.  By default, the range
    of the chart's Y axis will expand to show all values, but this parameter
    can be used to restrict or expand the Y-axis.

    :param scale_max: Set the maximum for the Y axis. -- see scale_min.
    """

    chars = BLOCK_VERTICAL

    def __init__(self, items,
                 color_scheme = "mono",
                 scale_min = None,
                 scale_max = None,
                 underline = None,
                 overline = None,
                 *args, **kwargs):

        self.items = items
        self.colors = self.parse_scheme(color_scheme)

        self.underline = underline
        self.overline = overline

        self.values = [ i[1] if isinstance(i, tuple) else i for i in self.items ]

        v_min = min(self.values)
        v_max = max(self.values)


        def item_to_glyph(item):

            color = None

            if isinstance(item, tuple):
                color = item[0]
                value = item[1]
            else:
                color = self.get_color(item)
                value = item

            if self.underline == "negative" and value < 0:
                glyph = " \N{COMBINING DOT BELOW}"
            else:


                # idx = scale_value(value, scale_min=scale_min, scale_max=scale_max)
                idx = self.normalize(
                    value, 0, len(self.chars)-1,
                    scale_min if scale_min else v_min,
                    scale_max if scale_max else v_max)

                glyph = self.chars[int(round(idx))]

                if self.underline == "min" and value == v_min:
                    glyph = "%s\N{COMBINING TRIPLE UNDERDOT}" %(glyph)

                if self.overline == "max" and value == v_max:
                    glyph = "%s\N{COMBINING THREE DOTS ABOVE}" %(glyph)

            if color:
                return (color, glyph)
            else:
                return glyph

        self.sparktext = [
            item_to_glyph(i)
            for i in self.items
        ]
        super(SparkColumnWidget, self).__init__(self.sparktext, *args, **kwargs)


# via https://github.com/rg3/dhondt
def dhondt_formula(votes, seats):
    return votes / (seats + 1)

def bar_widths(party_votes, total_seats):
    # Calculate the quotients matrix (list in this case).
    quot = []
    ret = dict()
    for p in dict(enumerate(party_votes)):
        ret[p] = 0
        for s in range(0, total_seats):
            q = dhondt_formula(party_votes[p], s)
            quot.append((q, p))

    # Sort the quotients by value.
    quot.sort(reverse=True)

    # Take the highest quotients with the assigned parties.
    for s in range(0, total_seats):
        ret[quot[s][1]] += 1
    return list(ret.values())


@dataclass
class SparkBarItem:

    value: int
    label: str = None
    fcolor: str = None
    bcolor: str = None
    align: str = "<"
    fill: str = " "

    @property
    def steps(self):
        return len(BLOCK_HORIZONTAL)

    def formatted_label(self, total):
        if self.label is None:
            return None
        try:
            pct = int(round(self.value/total*100, 0))
        except:
            pct = ""

        return str(self.label).format(
            value=self.value,
            pct=pct
        )
    def truncated_label(self, width, total):

        label = self.formatted_label(total)
        if not label:
            return None
        return (
            label[:width-1] + "\N{HORIZONTAL ELLIPSIS}"
            if len(label) > width
            else label
        )

        # s = "{label:.{n}}".format(
        #     label=self.formatted_label(total),
        #     n=min(len(label), width),
        # )
        # if len(s) > width:
        #     chars[-1] = "\N{HORIZONTAL ELLIPSIS}"


    def output(self, width, total, next_color=None):

        steps_width = width % self.steps if next_color else None
        chars_width = width // self.steps# - (1 if steps_width else 0)
        # print(width, chars_width, steps_width)
        label = self.truncated_label(chars_width, total)
        if label:
            chars = "{:{a}{m}.{m}}".format(
                label,
                m=max(chars_width, 0),
                a=self.align or "<",
            )
            # if len(label) > chars_width:
            #     chars[-1] = "\N{HORIZONTAL ELLIPSIS}"
        else:
            chars = self.fill * chars_width



        output = [
            (
                "%s:%s" %(
                    self.fcolor or DEFAULT_LABEL_COLOR,
                    self.bcolor or DEFAULT_BAR_COLOR), chars
            )
        ]

        if steps_width:
            attr = f"{self.bcolor}:{next_color}"
            output.append(
                (attr, BLOCK_HORIZONTAL[steps_width])
            )
        return output


class SparkBarWidget(SparkWidget):
    """
    A sparkline-ish horizontal stacked bar widget for Urwid.

    This widget graphs a set of values in a horizontal bar style.

    :param items: A list of items to be charted in the widget.  Items can be
    either numeric values or tuples, the latter of which must be of the form
    ('attribute', value) where attribute is an urwid text attribute and value
    is a numeric value.

    :param width: Width of the widget in characters.

    :param color_scheme: A string or dictionary containing the name of or
    definition of a color scheme for the widget.
    """

    fill_char = " "

    def __init__(self, items, width,
                 color_scheme="mono",
                 label_color=None,
                 min_width=None,
                 fit_label=False,
                 normalize=None,
                 fill_char=None,
                 *args, **kwargs):

        self.items = [
            i if isinstance(i, SparkBarItem) else SparkBarItem(i)
            for i in items
        ]

        self.colors = self.parse_scheme(color_scheme)

        for i in self.items:
            if not i.bcolor:
                i.bcolor = self.get_color(i)
            if fill_char:
                i.fill_char = fill_char

        self.width = width
        self.label_color = label_color
        self.min_width = min_width
        self.fit_label = fit_label

        values = None
        total = None

        if normalize:
            values = [ item.value for item in self.items ]
            v_min = min(values)
            v_max = max(values)
            values = [
                int(self.normalize(v,
                                   normalize[0], normalize[1],
                                   v_min, v_max))
                for v in values
            ]
            for i, v in enumerate(values):
                self.items[i].value = v


        filtered_items = self.items
        values = [i.value for i in filtered_items]
        total = sum(values)

        charwidth = total / self.width

        self.sparktext = []

        position = 0
        lastcolor = None

        values = [i.value for i in filtered_items]

        # number of steps that can be represented within each screen character
        # represented by Unicode block characters
        steps = len(BLOCK_HORIZONTAL)

        # use a prorportional representation algorithm to distribute the number
        # of available steps among each bar segment
        self.bars = bar_widths(values, self.width*steps)

        if self.min_width or self.fit_label:
            # make any requested adjustments to bar widths
            for i in range(len(self.bars)):
                if self.min_width and self.bars[i] < self.min_width*steps:
                    self.bars[i] = self.min_width*steps
                if self.fit_label:
                    # need some slack here to compensate for self.bars that don't
                    # begin on a character boundary
                    label_len = len(self.items[i].formatted_label(total))+2
                    if self.bars[i] < label_len*steps:
                        self.bars[i] = label_len*steps
            # use modified proportions to calculate new proportions that try
            # to account for min_width and fit_label
            self.bars = bar_widths(self.bars, self.width*steps)

        # filtered_items = [item for i, item in enumerate(self.items) if self.bars[i]]
        # self.bars = [b for b in self.bars if b]

        for i, (item, item_next) in enumerate(pairwise(filtered_items)):
            width = self.bars[i]
            output = item.output(width, total=total, next_color=item_next.bcolor)
            self.sparktext += output

        output = filtered_items[-1].output(self.bars[-1], total=total)
        self.sparktext += output

        if not self.sparktext:
            self.sparktext = ""
        self.set_text(self.sparktext)
        super(SparkBarWidget, self).__init__(self.sparktext, *args, **kwargs)

    def bar_width(self, index):
        return self.bars[index]//len(BLOCK_HORIZONTAL)


__all__ = [
    "SparkColumnWidget", "SparkBarWidget", "SparkBarItem",
    "get_palette_entries",
    "DEFAULT_LABEL_COLOR", "DEFAULT_LABEL_COLOR_DARK", "DEFAULT_LABEL_COLOR_LIGHT"
]
