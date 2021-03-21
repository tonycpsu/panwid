#!/usr/bin/env python3

import urwid
from panwid.datatable import *
from panwid.scroll import ScrollBar
from urwid_utils.palette import *

def unhandled_input(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop()

class ExampleScrollBar(ScrollBar):

    _thumb_char = ("light blue", "\u2588")
    _trough_char = ("dark blue", "\u2591")
    _thumb_indicator_top = ("white inverse", "\u234d")
    _thumb_indicator_bottom = ("white inverse", "\u2354")

def main():

    data_table = DataTable(
        columns = [
            DataTableColumn("num"),
            DataTableColumn("char")
        ],
        data=[
            dict(num=i, char=chr((i%58)+65))
            for i in range(500)
        ],
        with_scrollbar=ExampleScrollBar
    )

    entries = DataTable.get_palette_entries()
    entries["white inverse"] = PaletteEntry(
        mono = "black",
        foreground = "black",
        background = "white"
    )
    entries["light blue"] = PaletteEntry(
        mono = "white",
        foreground = "light blue",
        background = "black"
    )
    entries["dark blue"] = PaletteEntry(
        mono = "white",
        foreground = "dark blue",
        background = "black"
    )
    palette = Palette("default", **entries)

    loop = urwid.MainLoop(
        urwid.Frame(data_table),
        palette = palette,
        unhandled_input=unhandled_input
    )
    loop.run()


if __name__ == "__main__":
    main()
