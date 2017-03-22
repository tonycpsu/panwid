#!/usr/bin/python
from __future__ import division
import urwid
from urwid_datatable import *
from urwid_utils.palette import *

screen = urwid.raw_display.Screen()
# screen.set_terminal_properties(1<<24)
screen.set_terminal_properties(256)

NORMAL_FG_MONO = "white"
NORMAL_FG_16 = "light gray"
NORMAL_BG_16 = "black"
NORMAL_FG_256 = "light gray"
NORMAL_BG_256 = "g0"

def main():

    import os
    import random
    import string

    entries = DataTable.get_palette_entries()
    palette = Palette("default", **entries)
    # raise Exception(entries)

    class ExampleDataTable(DataTable):

        columns = [
            DataTableColumn("foo", width=10, align="right", padding=1),
            DataTableColumn("bar", width=30, align="right", padding=1),
            DataTableColumn("baz", width=("weight", 1)),
        ]

        def __init__(self, num_rows = 10, *args, **kwargs):
            self.num_rows = num_rows
            self.query_data = [
                self.random_row() for i in range(self.num_rows)
            ]
            super(ExampleDataTable, self).__init__(*args, **kwargs)

        def random_row(self):
            return dict(foo=random.choice(range(100) + [None]*20),
                        bar = (random.uniform(0, 1000)
                               if random.randint(0, 5)
                               else None),
                        baz =(''.join(random.choice(
                            string.ascii_uppercase
                            + string.lowercase
                            + string.digits + ' ' * 20
                        ) for _ in range(60))
                              if random.randint(0, 5)
                              else None),
                        qux = (random.uniform(0, 200)
                               if random.randint(0, 5)
                               else None),
                        xyzzy = random.randint(10, 100),
                        a = dict(b=dict(c=random.randint(0, 100))),
                        d = dict(e=dict(f=random.randint(0, 100)))

            )


        def query(self, sort=(None, None), offset=None):

            sort_field, sort_reverse = sort
            if sort_field:
                kwargs = {}
                # kwargs["reverse"] = sort_reverse
                if not sort_reverse:
                    # kwargs["key"] = lambda x: sort_key_natural_none_last(x[sort_field])
                    kwargs["key"] = lambda x: sort_key_natural_none_last(get_value(x, sort_field))
                else:
                    # kwargs["key"] = lambda x: sort_key_reverse_none_last(x[sort_field])
                    kwargs["key"] = lambda x: sort_key_reverse_none_last(get_value(x, sort_field))
                # logger.debug("query: %s" %(kwargs))
                self.query_data.sort(**kwargs)
                logger.debug("s" %(self.query_data))
            # print l[0]
            if offset is not None:
                start = offset
                end = offset + self.limit
                r = self.query_data[start:end]
                # print "%s, %s, %d, %d" %(sort_field, sort_reverse, start, end)
            else:
                r = self.query_data

            for d in r:
                yield d



        def query_result_count(self):
            return self.num_rows


    datatable = ExampleDataTable(1000, with_scrollbar=True)


    pile = urwid.Pile([
        ('weight', 1, datatable),
    ])


    def global_input(key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        if key == "1":
            datatable.sort("foo")
        if key == "2":
            datatable.sort("bar")
        if key == "3":
            datatable.sort("baz")
            # box.focus_position = random.randrange(0,9)
        else:
            return False

    main = urwid.MainLoop(
        urwid.LineBox(pile),
        palette = palette,
        screen = screen,
        unhandled_input=global_input

    )

    main.run()

if __name__ == "__main__":
    main()
