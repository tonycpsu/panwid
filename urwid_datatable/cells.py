import urwid

DEFAULT_CELL_PADDING = 0
DEFAULT_TABLE_BORDER_WIDTH = 1
DEFAULT_TABLE_BORDER_CHAR = " "
DEFAULT_TABLE_BORDER_ATTR = "table_border"

DEFAULT_TABLE_BORDER = (
    DEFAULT_TABLE_BORDER_WIDTH,
    DEFAULT_TABLE_BORDER_CHAR,
    DEFAULT_TABLE_BORDER_ATTR
)

intersperse = lambda e,l: sum([[x, e] for x in l],[])[:-1]

class DataTableCell(urwid.WidgetWrap):

    ATTR = "table_cell"
    PADDING_ATTR = "table_row_padding"

    def __init__(self, column, value, padding=0):

        self.attr = self.ATTR
        self.attr_focused = "%s focused" %(self.attr)
        self.attr_highlight = "%s highlight" %(self.attr)
        self.attr_highlight_focused = "%s focused" %(self.attr_highlight)

        self.column = column
        self.value = value
        if column.padding:
            self.padding = column.padding
        else:
            self.padding = padding

        self.attr_map =  {}

        self.normal_attr_map = {
            None: self.attr,
        }


        self.highlight_attr_map = {
            None: self.attr_highlight,
        }

        self.normal_focus_map = {
            None: self.attr_focused,
        }

        self.highlight_focus_map = {
            None: self.attr_highlight,
            self.attr_highlight: self.attr_highlight_focused,
        }

        self.contents = self._format(value)

        self.padding = urwid.Padding(
            self.contents,
            left=self.padding,
            right=self.padding
        )

        # self.columns = urwid.Columns(
        #     [self.padding], dividechars=self.column.margin or 0
        # )
        # logger.info(self.columns.dividechars)

        self.attr = urwid.AttrMap(
            self.padding,
            attr_map = self.normal_attr_map,
            focus_map = self.normal_focus_map
        )
        super(DataTableCell, self).__init__(self.attr)

    def highlight(self):
        self.attr.set_attr_map(self.highlight_attr_map)
        self.attr.set_focus_map(self.highlight_focus_map)


    def unhighlight(self):
        self.attr.set_attr_map(self.normal_attr_map)
        self.attr.set_focus_map(self.normal_focus_map)

    def selectable(self):
        return False

    def keypress(self, size, key):
        return key
        # return super(DataTableCell, self).keypress(size, key)

    def _format(self, v):
        return self.column._format(v)

    def set_attr_map(self, attr_map):
        self.attr.set_attr_map(attr_map)


class DataTableBodyCell(DataTableCell):
    ATTR = "table_row_body"
    PADDING_ATTR = "table_row_body_padding"


class DataTableHeaderCell(DataTableCell):
    ATTR = "table_row_header"
    PADDING_ATTR = "table_row_header_padding"


class DataTableFooterCell(DataTableCell):
    ATTR = "table_row_footer"
    PADDING_ATTR = "table_row_footer_padding"
