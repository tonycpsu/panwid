#!/usr/bin/python

import logging
logger = logging.getLogger(__name__)
import urwid
from panwid.datatable import *
from panwid.listbox import ScrollingListBox
from urwid_utils.palette import *
from orderedattrdict import AttrDict
import os
import random
import string
from optparse import OptionParser
from dataclasses import *
import typing
from collections.abc import MutableMapping

screen = urwid.raw_display.Screen()
# screen.set_terminal_properties(1<<24)
screen.set_terminal_properties(256)

NORMAL_FG_MONO = "white"
NORMAL_FG_16 = "light gray"
NORMAL_BG_16 = "black"
NORMAL_FG_256 = "light gray"
NORMAL_BG_256 = "g0"

@dataclass
class BaseDataClass(MutableMapping):

    def keys(self):
        return self.__dataclass_fields__.keys()

    def get(self, key, default=None):

        try:
            return self[key]
        except (KeyError, AttributeError):
            return default

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        delattr(self, key)

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

@dataclass
class Foo(BaseDataClass):
    uniqueid: int
    foo: int
    bar: float
    baz: str
    qux: urwid.Widget
    xyzzy: str
    baz_len: typing.Any
    a: dict
    d: dict
    color: list
    # _details: dict = field(default_factory=lambda: {"open": True, "disabled": False})
    # _cls: typing.Optional[type] = None
    @property
    def _details(self):
        return {"open": True, "disabled": False}

def main():


    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="count", default=0),
    (options, args) = parser.parse_args()

    if options.verbose:
        formatter = logging.Formatter(
            "%(asctime)s [%(module)16s:%(lineno)-4d] [%(levelname)8s] %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh = logging.FileHandler("datatable.log")
        # fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        if options.verbose > 0:
            logger.setLevel(logging.DEBUG)
            logging.getLogger("panwid.datatable").setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            logging.getLogger("panwid.datatable").setLevel(logging.INFO)
        logger.addHandler(fh)
        logging.getLogger("panwid.datatable").addHandler(fh)
        # logging.getLogger("raccoon.dataframe").setLevel(logging.DEBUG)
        # logging.getLogger("raccoon.dataframe").addHandler(fh)


    attr_entries = {}
    for attr in ["dark red", "dark green", "dark blue", "dark cyan"]:
        attr_entries[attr.split()[1]] = PaletteEntry(
            mono = "white",
            foreground = attr,
            background = "black"
        )
    entries = ScrollingListBox.get_palette_entries()
    entries.update(DataTable.get_palette_entries(user_entries=attr_entries))
    # entries.update(attr_entries)
    palette = Palette("default", **entries)


    COLUMNS = [
        DataTableColumn("foo", label="Foo", align="right",
                        # width=("weight", 1),
                        width=3,
                        sort_key = lambda v: (v is None, v),
                        pack=True,
                        attr="color", padding=0,
                        footer_fn = lambda column, values: sum(v for v in values if v is not None)
        ),
        DataTableDivider(u"\N{DOUBLE VERTICAL LINE}"),
        DataTableColumn("bar", label="Bar", width=10, align="right",
                        format_fn = lambda v: round(v, 2) if v is not None else v,
                        decoration_fn = lambda v: ("cyan", v),
                        sort_reverse=True, sort_icon=False, padding=0),# margin=5),
        DataTableColumn("baz", label="Baz!",
                        width=("weight", 5),
                        # pack=True,
                        min_width=5,
                        align="right",
                        truncate=True),
        DataTableColumn(
            "qux",
            label=urwid.Text([("red", "q"), ("green", "u"), ("blue", "x")]),
            width=5, hide=True),
    ]

    class BazColumns(urwid.WidgetWrap):
        def __init__(self, value):
            self.text = DataTableText(value)
            super().__init__(urwid.Columns([
                (1, urwid.Text("[")),
                ("weight", 1, self.text),
                (1, urwid.Text("]")),
            ]))

        def truncate(self, width, end_char=None):
            self.text.truncate(width-2, end_char=end_char)


    class ExampleDataTable(DataTable):

        columns = COLUMNS[:]

        index="index"

        with_sidecar = True

        def __init__(self, num_rows = 10, random=False, *args, **kwargs):
            self.num_rows = num_rows
            # indexes = random.sample(range(self.num_rows*2), num_rows)
            if random:
                self.randomize_query_data()
            else:
                self.fixed_query_data()

            self.last_rec = len(self.query_data)
            super(ExampleDataTable, self).__init__(*args, **kwargs)

        def fixed_query_data(self):
            self.query_data = [
                self.fixed_row(i) for i in range(self.num_rows)
                # self.random_row(i) for i in range(self.num_rows)
            ]

        def randomize_query_data(self):
            indexes = list(range(self.num_rows))
            self.query_data = [
                self.random_row(indexes[i]) for i in range(self.num_rows)
                # self.random_row(i) for i in range(self.num_rows)
            ]
            random.shuffle(self.query_data)

        def fixed_row(self, uniqueid):
            # return AttrDict(uniqueid=uniqueid,
            f = Foo(uniqueid=uniqueid,
                        foo=uniqueid,
                        bar = (random.uniform(0, 1000)
                               if random.randint(0, 5)
                               else None),
                        baz =(''.join(random.choice(
                            string.ascii_uppercase
                            + string.ascii_lowercase
                            + string.digits + ' ' * 10
                        ) for _ in range(random.randint(20, 80)))
                              if random.randint(0, 5)
                              else None),
                        qux = urwid.Text([("red", "1"),("green", "2"), ("blue", "3")]),
                        xyzzy = ( "%0.1f" %(random.uniform(0, 100))
                               if random.randint(0, 5)
                               else None),
                        baz_len = lambda r: len(r["baz"]) if r.get("baz") else 0,
                        # xyzzy = random.randint(10, 100),
                        a = dict(b=dict(c=random.randint(0, 100))),
                        d = dict(e=dict(f=random.randint(0, 100))),
                        color = ["red", "green", "blue"][random.randrange(3)],
            )
            return f


        def random_row(self, uniqueid):
            return AttrDict(uniqueid=uniqueid,
                        foo=random.choice(list(range(100)) + [None]*20),
                        bar = (random.uniform(0, 1000)
                               if random.randint(0, 5)
                               else None),
                        baz =(''.join(random.choice(
                            string.ascii_uppercase
                            + string.ascii_lowercase
                            + string.digits + ' ' * 10
                        ) for _ in range(random.randint(5, 80)))
                              if random.randint(0, 5)
                              else None),
                        qux = urwid.Text([("red", "1"),("green", "2"), ("blue", "3")]),
                        xyzzy = ( "%0.1f" %(random.uniform(0, 100))
                               if random.randint(0, 5)
                               else None),
                        baz_len = lambda r: len(r["baz"]) if r.get("baz") else 0,
                        # xyzzy = random.randint(10, 100),
                        a = dict(b=dict(c=random.randint(0, 100))),
                        d = dict(e=dict(f=random.randint(0, 100))),
                        color = ["red", "green", "blue"][random.randrange(3)],

            )


        def query(self, sort=(None, None), offset=None, limit=None, load_all=False, **kwargs):

            logger.info("query: offset=%s, limit=%s, sort=%s" %(offset, limit, sort))
            try:
                sort_field, sort_reverse = sort
            except:
                sort_field = sort
                sort_reverse = None

            if sort_field:
                kwargs = {}
                kwargs["key"] = lambda x: (x.get(sort_field) is None,
                                           x.get(sort_field),
                                           x.get(self.index))
                if sort_reverse:
                    kwargs["reverse"] = sort_reverse
                self.query_data.sort(
                    **kwargs
                )
            if offset is not None:
                if not load_all:
                    start = offset
                    end = offset + limit
                    r = self.query_data[start:end]
                else:
                    r = self.query_data[offset:]
            else:
                r = self.query_data

            for d in r:
                yield (d, dict(zzzz=1))


        def query_result_count(self):
            return self.num_rows


        def keypress(self, size, key):
            if key == "r":
                self.refresh()
            elif key == "meta r":
                # self.randomize_query_data()
                # self.reset(reset_sort=True)
                self.refresh()
            elif key == "ctrl r":
                self.reset(reset_sort=True)
            elif key == "ctrl d":
                logger.info(type(self.selection.data))
                self.log_dump(20)
            elif key == "meta d":
                self.log_dump(20, columns=["foo", "baz"])
            elif key == "ctrl f":
                self.focus_position = 0
            elif key == "ctrl t":
                logger.info(self.selection.data)
            elif key == "ctrl k":
                self.selection["foo"] = 123
                logger.info(self.selection.data["foo"])
                self.selection.update()
                # self.selection.details_disabled = not self.selection.details_disabled
                # logger.info(self.selection.details_disabled)
            elif key == "meta i":
                logger.info("foo %s, baz: %s" %(self.selection.get("foo"),
                                                    self.selection.get("baz")))
            elif self.ui_sort and key.isdigit() and int(key)-1 in range(len(self.columns)):
                col = int(key)-1
                self.sort_by_column(col, toggle=True)
            elif key == "ctrl l":
                self.load("test.json")
            elif key == "ctrl s":
                self.save("test.json")
            elif key == "0":
                # self.sort_by_column(self.index, toggle=True)
                self.sort_index()
            elif key == "a":
                self.add_row(self.random_row(self.last_rec))
                self.last_rec += 1
            elif key == "A":
                self.add_row(self.random_row(self.last_rec), sort=False)
                self.last_rec += 1
            elif key == "d":
                if len(self):
                    self.delete_rows(self.df.index[self.focus_position])
            elif key == "meta a":
                name = "".join( random.choice(
                            string.ascii_uppercase
                            + string.lowercase
                            + string.digits
                        ) for _ in range(5) )
                data = [ "".join( random.choice(
                            string.ascii_uppercase
                            + string.lowercase
                            + string.digits
                        ) for _ in range(5)) for _ in range(len(self)) ]
                col = DataTableColumn(name, label=name, width=6, padding=0)
                self.add_columns(col, data=data)
            elif key == "t":
                self.toggle_columns("qux")
            elif key == ";":
                self.set_columns(COLUMNS)
            elif key == "T":
                self.toggle_columns(["foo", "baz"])
            elif key == "D":
                self.remove_columns(len(self.columns)-1)
            elif key == "f":
                self.apply_filters([lambda x: x["foo"] > 20, lambda x: x["bar"] < 800])
            elif key == "F":
                self.clear_filters()
            elif key == ".":
                self.selection.toggle_details()
            elif key == "s":
                self.selection.set_attr("red")
            elif key == "S":
                self.selection.clear_attr("red")
            elif key == "k":
                self.selection[2].set_attr("red")
            elif key == "K":
                self.selection[2].clear_attr("red")
            elif key == "u":
                logger.info(self.footer.values)
            elif key == "c":
                self.toggle_cell_selection()
            elif key == "z":
                # self.columns[0].width = 12
                self.resize_column("foo", ("given", 12))
                # self.reset()
            elif key == "shift left":
                self.cycle_sort_column(-1)
            elif key == "shift right":
                self.cycle_sort_column(1)
            elif self.ui_sort and key == "shift up":
                self.sort_by_column(reverse=True)
            elif self.ui_sort and key == "shift down":
                self.sort_by_column(reverse=False)
            elif key == "shift end":
                self.load_all()
                # self.listbox.focus_position = len(self) -1
            elif key == "ctrl up":
                if self.focus_position > 0:
                    self.swap_rows(self.focus_position, self.focus_position-1, "foo")
                    self.focus_position -= 1
            elif key == "ctrl down":
                if self.focus_position < len(self)-1:
                    self.swap_rows(self.focus_position, self.focus_position+1, "foo")
                    self.focus_position += 1
            else:
                return super(ExampleDataTable, self).keypress(size, key)

        def decorate(self, row, column, value):
            # if column.name == "baz":
            #     return BazColumns(value)
            return super().decorate(row, column, value)

    class ExampleDataTableBox(urwid.WidgetWrap):

        def __init__(self, *args, **kwargs):

            self.table = ExampleDataTable(*args, **kwargs)
            # urwid.connect_signal(
            #     self.table, "select",
            #     lambda source, selection: logger.info("selection: %s" %(selection))
            # )
            label = "sz:%d pgsz:%s sort:%s%s hdr:%s ftr:%s ui_sort:%s cell_sel:%s" %(
                self.table.query_result_count(),
                self.table.limit if self.table.limit else "-",
                "-" if self.table.sort_by[1]
                else "+" if self.table.sort_by[0]
                else "n",
                self.table.sort_by[0] or " ",

                "y" if self.table.with_header else "n",
                "y" if self.table.with_footer else "n",
                "y" if self.table.ui_sort else "n",
                "y" if self.table.cell_selection else "n",
            )
            self.pile = urwid.Pile([
                ("pack", urwid.Text(label)),
                ("pack", urwid.Divider(u"\N{HORIZONTAL BAR}")),
                ("weight", 1, self.table)
            ])
            self.box = urwid.BoxAdapter(urwid.LineBox(self.pile), 25)
            super(ExampleDataTableBox, self).__init__(self.box)

    def detail_fn(data):

        # return urwid.Padding(urwid.Columns([
        #     ("weight", 1, data.get("qux")),
        #     # ("weight", 1, urwid.Text(str(data.get("baz_len")))),
        #     ("weight", 2, urwid.Text(str(data.get("xyzzy")))),
        # ]))

        # return urwid.Pile([
        #     (1, urwid.Filler(urwid.Padding(urwid.Text("adassdda")))),
        #     (1, urwid.Filler(urwid.Padding(urwid.Text("adassdda")))),
        #     (1, urwid.Filler(urwid.Padding(urwid.Text("adassdda")))),
        #     (1, urwid.Filler(urwid.Padding(urwid.Text("adassdda")))),
        # ])

        return urwid.BoxAdapter(ExampleDataTable(
            100,
            limit=10,
            index="uniqueid",
            divider = DataTableDivider(".q", width=3),
            # detail_fn=detail_fn,
            cell_selection=True,
            sort_refocus = True,
            with_scrollbar=True,
            row_attr_fn = row_attr_fn,
        ), 20)

    def row_attr_fn(position, data, row):
        if data.baz and "R" in data.baz:
            return "red"
        elif data.baz and "G" in data.baz:
            return "green"
        elif data.baz and "B" in data.baz:
            return "blue"
        return None

    boxes = [

        ExampleDataTableBox(
            100,
            limit=10,
            index="uniqueid",
            divider = DataTableDivider("."),
            # divider = False,
            detail_fn=detail_fn,
            detail_auto_open=True,
            detail_replace=True,
            cell_selection=True,
            sort_refocus = True,
            with_scrollbar=True,
            row_attr_fn = row_attr_fn,
            detail_selectable = True,
            sort_icons=False,
            # row_height=2,
            # no_load_on_init = True

        ),

        # ExampleDataTableBox(
        #     500,
        #     index="uniqueid",
        #     sort_by = "foo",
        #     query_sort=False,
        #     ui_sort=False,
        #     ui_resize=False,
        #     with_footer=True,
        #     with_scrollbar=True,
        #     row_height=2,
        # ),

        # ExampleDataTableBox(
        #     500,
        #     columns = [DataTableColumn("row", width=7, value="{row}/{rows_total}")] + ExampleDataTable.columns,
        #     limit=25,
        #     index="uniqueid",
        #     sort_by = ("bar", True),
        #     sort_icons = False,
        #     query_sort=True,
        #     with_footer=True,
        #     with_scrollbar=True,
        #     cell_selection=True,
        #     padding=3,
        #     row_style = "grid"
        # ),
        # ExampleDataTableBox(
        #     5000,
        #     limit=500,
        #     index="uniqueid",
        #     sort_by = ("foo", True),
        #     query_sort=True,
        #     with_scrollbar=True,
        #     with_header=False,
        #     with_footer=False,
        # ),

    ]


    grid_flow = urwid.GridFlow(
        boxes, 60, 1, 1, "left"
    )

    def global_input(key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        else:
            return False

    old_signal_keys = screen.tty_signal_keys()
    l = list(old_signal_keys)
    l[0] = 'undefined'
    l[3] = 'undefined'
    l[4] = 'undefined'
    screen.tty_signal_keys(*l)

    grid_box = urwid.LineBox(grid_flow)

    table = ExampleDataTable(
        100,
        columns = [
        DataTableColumn("bar", label="Bar", width=10, align="right",
                        format_fn = lambda v: round(v, 2) if v is not None else v,
                        decoration_fn = lambda v: ("cyan", v),
                        sort_reverse=True, sort_icon=False, padding=0),# margin=5),
        DataTableColumn("baz", label="Baz!",
                        #width="pack",
                        width=("weight", 5),
                        pack=True,
                        min_width=5,
                        truncate=False),
        DataTableColumn(
            "qux",
            label=urwid.Text([("red", "q"), ("green", "u"), ("blue", "x")]),
            width=5, hide=True),
        DataTableColumn("foo", label="Foo", align="right",
                        width=("weight", 1),
                        sort_key = lambda v: (v is None, v),
                        pack=True,
                        attr="color", padding=0,
                        footer_fn = lambda column, values: sum(v for v in values if v is not None)
        ),
        ],
        limit=10,
        index="uniqueid",
        divider = DataTableDivider(".", width=3),
        detail_fn=detail_fn,
        detail_hanging_indent=1,
        cell_selection=True,
        sort_refocus = True,
        with_scrollbar=True,
        row_attr_fn = row_attr_fn,
    )

    main = urwid.MainLoop(
        urwid.Pile([
            ("pack", grid_box),
            ("weight", 1, table),
            ("weight", 1, DataTable(columns=[DataTableColumn("a")], data={})),
        ]),
        palette = palette,
        screen = screen,
        unhandled_input=global_input

    )

    try:
        main.run()
    finally:
        screen.tty_signal_keys(*old_signal_keys)

if __name__ == "__main__":
    main()
