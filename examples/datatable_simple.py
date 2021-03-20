#!/usr/bin/env python3

import urwid
from panwid.datatable import *


def unhandled_input(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop()

def main():

    data_table = DataTable(
        columns = [
            DataTableColumn("num"),
            DataTableColumn("char")
        ],
        data=[
            dict(num=i, char=chr(i+33))
            for i in range(100)
        ],
        with_scrollbar=True
    )

    loop = urwid.MainLoop(
        urwid.Frame(data_table),
        unhandled_input=unhandled_input
    )
    loop.run()


if __name__ == "__main__":
    main()
