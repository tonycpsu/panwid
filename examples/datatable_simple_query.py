#!/usr/bin/env python3

import urwid
from panwid.datatable import *


def unhandled_input(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop()

class ExampleDataTable(DataTable):

    columns = [
        DataTableColumn("foo"),
        DataTableColumn("bar")
    ]

    def query(self, *args, **kwargs):
        for i in range(20):
            yield(dict(foo=i+1, bar=chr(97+i)))

def main():

    data_table = ExampleDataTable()

    loop = urwid.MainLoop(
        urwid.Frame(data_table),
        unhandled_input=unhandled_input
    )
    loop.run()


if __name__ == "__main__":
    main()
