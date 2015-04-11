import string
import random

from urwid_datatable import *

def main():

    import urwid.raw_display

    global loop

    NORMAL_FG_16 = "default"
    NORMAL_BG_16 = "black"

    NORMAL_FG_256 = "default"
    NORMAL_BG_256 = "black"

    FOCUSED_FG_16 = "black"
    FOCUSED_FG_256 = "black"

    FOCUSED_BG_16 = "light gray"
    FOCUSED_BG_256 = "g40"

    HEADER_FG_16 = "black,bold"
    HEADER_FG_256 = "black,bold"

    HEADER_BG_16 = "dark gray"
    HEADER_BG_256 = "g25"

    HIGHLIGHT_FG_16 = "light green,bold"
    HIGHLIGHT_BG_16 = HEADER_BG_16

    HIGHLIGHT_FG_256 = "light green,bold"
    HIGHLIGHT_BG_256 = HEADER_BG_256

    palette = [
        ("normal",
         NORMAL_FG_16, NORMAL_BG_16, "default",
         NORMAL_FG_256, NORMAL_BG_256),
        ("focused",
         FOCUSED_FG_16, FOCUSED_BG_16, "default,underline",
         FOCUSED_FG_256, FOCUSED_BG_256),
        ("normal focused",
         FOCUSED_FG_16, FOCUSED_BG_16, "default,underline",
         FOCUSED_FG_256, FOCUSED_BG_256),
        ("header",
         HEADER_FG_16, HEADER_BG_16, "standout",
         HEADER_FG_256, HEADER_BG_256),
        ("header focused",
         HEADER_FG_16, FOCUSED_BG_16, "standout,underline",
         HEADER_FG_256, FOCUSED_BG_256),
        ("highlight",
         HIGHLIGHT_FG_16, HEADER_BG_16, "standout,bold",
         HIGHLIGHT_FG_256, HEADER_BG_256),
        ("highlight focused",
         HIGHLIGHT_FG_16, FOCUSED_BG_16, "standout,bold,underline",
         HIGHLIGHT_FG_256, FOCUSED_BG_256),
        ("red",
         "light red", NORMAL_BG_16, "default",
         "light red", NORMAL_BG_256),
        ("red focused",
         "light red", FOCUSED_BG_16, "default",
         "light red", FOCUSED_BG_256),
        ("green",
         "light green", NORMAL_BG_16, "default",
         "light green", NORMAL_BG_256),
        ("green focused",
         "light green", FOCUSED_BG_16, "default",
         "light green", FOCUSED_BG_256),

    ]

    BASE_FOCUS_MAP = dict()
    BASE_FOCUS_MAP["normal"] = "normal focused"
    BASE_FOCUS_MAP["red"] = "red focused"
    BASE_FOCUS_MAP["green"] = "green focused"
    BASE_FOCUS_MAP["header"] = "header focused"
    BASE_FOCUS_MAP["highlight"] = "highlight focused"

    screen = urwid.raw_display.Screen()
    screen.set_terminal_properties(256)

    # def format_bar(val):
    #     return "%.03f" %(val)

    class MyDataTableColumnDef(DataTableColumnDef):

        def default_format(self, v):
            textattr = "normal"
            if not isinstance(v, tuple):
                return super(MyDataTableColumnDef, self).default_format(v)

            textattr, t = v
            text = urwid.Text( (textattr, s), align=self.align)
            text.val = t
            cell = urwid.Padding(text, left=self.padding, right=self.padding)
            text.sort_key = self.sort_key
            text.sort_fn = self.sort_fn
            l = list()
            cell = urwid.AttrMap(cell, self.attr_map, self.focus_map)
            if self.sizing == None or self.sizing == "given":
                l.append(self.width)
            else:
                l += ['weight', self.width]
            l.append(cell)
            return tuple(l)



    COLUMN_DEFS =  [
        MyDataTableColumnDef("foo", details="foo_details",
                             width=12, sort_fn=lambda a, b: cmp(b,a)),
        MyDataTableColumnDef("bar", width=15, align="right"),
        MyDataTableColumnDef("baz", width=32, padding=0,
                             attr_map={None: "red"}),
    ]

    l = [ (random.randint(1, 1000),
           random.uniform(0, 100),
           ''.join(random.choice(
               string.ascii_uppercase
               + string.lowercase
               + string.digits + ' ' * 10
           ) for _ in range(32))) for i in range(1000)]

    # l = [ (1, 2.12314, "c"),
    #       { 'foo': 6, 'foo_details': ("green", "abcdef abcdef"), 'bar': 4, 'baz': "a"},
    #       (2, 99.9555, "q"),
    #       (5, 6.9555, "b"),
    #       (4, 103, "a"),
    #   ]


    class DataTableTest(DataTable):

        columns = COLUMN_DEFS

        def __init__(self, *kargs, **kwargs):

            super(DataTableTest, self).__init__(*kargs, **kwargs)
            urwid.connect_signal(
                self, "select", lambda source, selection: selection.toggle_details()
            )
            urwid.connect_signal(
                self, "refresh", lambda source: loop.draw_screen()
            )

        def query(self, offset=None):
            start = offset
            end = offset + self.limit
            r = l[start:end]
            return r

        def keypress(self, size, key):
            if key in ('<', '>'):
                self.cycle_index((key == '>') and 1 or -1)


            return super(DataTableTest, self).keypress(size, key)

    tables = list()

    # tables.append(
    #     DataTableTest(
    #         sort_field="foo",
    #         attr_map = {None: "normal"},
    #         focus_map = BASE_FOCUS_MAP,
    #     )
    # )

    tables.append(
        DataTableTest(
            limit = 10,
            # sort_field="bar",
            attr_map = {None: "normal"},
            focus_map = BASE_FOCUS_MAP,
            border_map = {None: "normal"}
        )
    )

    # tables.append(
    #     DataTableTest(
    #         limit = 100,
    #         sort_field="baz",
    #         border_char = u"\u007c",
    #         attr_map = {None: "normal"},
    #         focus_map = BASE_FOCUS_MAP,
    #     )
    # )

    main = urwid.Columns(
        [ ('weight', 1, urwid.LineBox(t)) for t in tables ]
    )

    def global_input(key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

    loop = urwid.MainLoop(main,
                          palette,
                          screen=screen,
                          unhandled_input=global_input)
    loop.run()


if __name__ == "__main__":
    main()
