from urwid_datatable import *

def main():

    import urwid.raw_display

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
    ]

    BASE_FOCUS_MAP = dict()
    BASE_FOCUS_MAP["normal"] = "normal focused"
    BASE_FOCUS_MAP["header"] = "header focused"
    BASE_FOCUS_MAP["highlight"] = "highlight focused"

    screen = urwid.raw_display.Screen()
    screen.set_terminal_properties(256)

    def format_bar(val):
        return "%.03f" %(val)


    COLUMN_DEFS =  [
        DataTableColumnDef("foo", width=12, sort_fn=lambda a, b: cmp(b,a)),
        DataTableColumnDef("bar", width=15, align="right", format_fn=format_bar),
        DataTableColumnDef("baz", width=8),
    ]

    l = [ (1, 2.12314, "c"),
          (6, 4, "a"),
          (2, 99.9555, "q"),
          (5, 6.9555, "b"),
          (4, 103, "a"),
      ]


    class DataTableTest(DataTable):

        def query(self, **kwargs):
            for r in l:
                yield r

        def keypress(self, size, key):
            if key in ('<', '>'):
                self.cycle_index((key == '>') and 1 or -1)
            return super(DataTableTest, self).keypress(size, key)

    tables = list()

    tables.append(
        DataTableTest(
            COLUMN_DEFS,
            sort_field="foo",
            attr_map = {None: "normal"},
            focus_map = BASE_FOCUS_MAP,
        )
    )

    tables.append(
        DataTableTest(
            COLUMN_DEFS,
            sort_field="bar",
            attr_map = {None: "normal"},
            focus_map = BASE_FOCUS_MAP,
            border_map = {None: "normal"}
        )
    )

    tables.append(
        DataTableTest(
            COLUMN_DEFS,
            sort_field="baz",
            border_char = u"\u007c",
            attr_map = {None: "normal"},
            focus_map = BASE_FOCUS_MAP,
        )
    )

    main = urwid.Columns(
        [ ('weight', 1, urwid.LineBox(t)) for t in tables ]
    )

    loop = urwid.MainLoop(main, palette, screen=screen)
    loop.run()


if __name__ == "__main__":
    main()
