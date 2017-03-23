#!/usr/bin/python
from __future__ import division
import logging
logger = logging.getLogger(__name__)
import urwid
from urwid_datatable import *
from urwid_utils.palette import *
import os
import random
import string
from optparse import OptionParser

screen = urwid.raw_display.Screen()
# screen.set_terminal_properties(1<<24)
screen.set_terminal_properties(256)

NORMAL_FG_MONO = "white"
NORMAL_FG_16 = "light gray"
NORMAL_BG_16 = "black"
NORMAL_FG_256 = "light gray"
NORMAL_BG_256 = "g0"

def main():


    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", default=False),
    (options, args) = parser.parse_args()

    if options.verbose:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s [%(levelname)8s] %(message)s",
                                        datefmt='%Y-%m-%d %H:%M:%S')
        fh = logging.FileHandler("datatable.log")
        fh.setFormatter(formatter)
        logging.getLogger("urwid_datatable.datatable").setLevel(logging.DEBUG)
        logging.getLogger("urwid_datatable.datatable").addHandler(fh)
        logging.getLogger("urwid.listbox").setLevel(logging.DEBUG)
        logging.getLogger("urwid.listbox").addHandler(fh)
        # logging.getLogger("raccoon.dataframe").setLevel(logging.DEBUG)
        # logging.getLogger("raccoon.dataframe").addHandler(fh)
        # fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)


    entries = DataTable.get_palette_entries()
    palette = Palette("default", **entries)
    # raise Exception(entries)

    class ExampleDataTable(DataTable):

        columns = [
            # DataTableColumn("uniqueid", width=10, align="right", padding=1),
            DataTableColumn("foo", width=10, align="right", padding=1),
            DataTableColumn("bar", width=30, align="right", padding=1),
            DataTableColumn("baz", width=("weight", 1)),
        ]

        index="index"


        def __init__(self, num_rows = 10, *args, **kwargs):
            self.num_rows = num_rows
            # indexes = random.sample(range(self.num_rows*2), num_rows)
            indexes = range(self.num_rows)
            self.query_data = [
                self.random_row(indexes[i]) for i in range(self.num_rows)
                # self.random_row(i) for i in range(self.num_rows)
            ]
            random.shuffle(self.query_data)
            self.last_rec = len(self.query_data)
            super(ExampleDataTable, self).__init__(*args, **kwargs)

        def random_row(self, uniqueid):
            return dict(uniqueid=uniqueid,
                        foo=random.choice(range(100) + [None]*20),
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

            logger.debug("query: offset=%s, sort=%s" %(offset, sort))
            try:
                sort_field, sort_reverse = sort
            except:
                sort_field = sort
                sort_reverse = False

            if sort_field:
                kwargs = {}
                kwargs["key"] = lambda x: (x[sort_field], x[self.index])
                kwargs["reverse"] = sort_reverse
                # if not sort_reverse:
                #     # kwargs["key"] = lambda x: sort_key_natural_none_last(x[sort_field])
                #     kwargs["key"] = lambda x: sort_key_natural_none_last(get_value(x, sort_field))
                # else:
                #     # kwargs["key"] = lambda x: sort_key_reverse_none_last(x[sort_field])
                #     kwargs["key"] = lambda x: sort_key_reverse_none_last(get_value(x, sort_field))
                # # logger.debug("query: %s" %(kwargs))
                self.query_data.sort(**kwargs)
                # logger.debug("s" %(self.query_data))
            # print l[0]
            if offset is not None:
                start = offset
                end = offset + self.limit
                # raise Exception(start, end)
                r = self.query_data[start:end]
                logger.debug("%s:%s (%s)" %(start, end, len(r)))
                # print "%s, %s, %d, %d" %(sort_field, sort_reverse, start, end)
            else:
                r = self.query_data

            for d in r:
                yield d


        def query_result_count(self):
            return self.num_rows


        def keypress(self, size, key):
            # if key == "`":
            #     datatable.sort_by_column_index()
            if key == "ctrl r":
                datatable.reset()
            elif key == "0":
                datatable.sort_by_column("uniqueid")
            elif key == "1":
                datatable.sort_by_column("foo")
            elif key == "2":
                datatable.sort_by_column("bar")
            elif key == "3":
                datatable.sort_by_column("baz")
            elif key == "a":
                self.add_row(self.random_row(self.last_rec))
                self.last_rec += 1
            else:
                return super(ExampleDataTable, self).keypress(size, key)


    datatable = ExampleDataTable(100,
                                 index="uniqueid",
                                 limit = 10,
                                 sort_by = ("bar", False),
                                 query_sort=True,
                                 with_header=True,
                                 with_footer=True,
                                 with_scrollbar=True
    )


    pile = urwid.Pile([
        ('weight', 1, datatable),
    ])


    def global_input(key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        else:
            return False

    main = urwid.MainLoop(
        # urwid.LineBox(urwid.Filler(urwid.BoxAdapter(pile, 10))),
        urwid.LineBox(pile),
        palette = palette,
        screen = screen,
        unhandled_input=global_input

    )

    main.run()

if __name__ == "__main__":
    main()
