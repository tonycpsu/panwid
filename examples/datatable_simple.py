#!/usr/bin/env python3

import urwid
from panwid.datatable import *


def unhandled_input(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop()

def main():

    data_table = DataTable(
        columns = [
            DataTableColumn("foo"),
            DataTableColumn("bar")
        ],
        data=[
            dict(foo=1, bar="a"),
            dict(foo=2, bar="b")
        ]
    )

    loop = urwid.MainLoop(
        urwid.Frame(data_table),
        unhandled_input=unhandled_input
    )
    loop.run()


if __name__ == "__main__":
    main()
