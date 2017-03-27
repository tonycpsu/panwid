import urwid

from .cells import *

class DataTableRow(urwid.WidgetWrap):

    border_attr_map = { None: "table_border" }
    border_focus_map = { None: "table_border focused" }

    def __init__(self, columns, data, index=None,
                 border=None, padding=None,
                 sort=None, sort_icons=None,
                 *args, **kwargs):

        self.data = data
        self._index = index
        self.attr = self.ATTR
        self.attr_focused = "%s focused" %(self.attr)
        self.attr_highlight = "%s highlight" %(self.attr)
        self.attr_highlight_focused = "%s focused" %(self.attr_highlight)
        self.attr_map =  {
            None: self.attr,
        }

        self.focus_map = {
            self.attr: self.attr_focused,
            self.attr_highlight: self.attr_highlight_focused
        }

        if isinstance(self.data, list):
            self.data = dict(zip([c.name for c in columns], self.data))

        self.cells = [
            self.CELL_CLASS(col, self.data[col.name],
                            sort=sort,
                            sort_icon=sort_icons,
                            attr=self.data.get(col.attr, None))
                 for i, col in enumerate(columns)]

        self.columns = urwid.Columns([])

        for i, cell in enumerate(self.cells):
            col = columns[i]
            self.columns.contents.append(
                (cell, self.columns.options(col.sizing, col.width_with_padding(padding)))
            )

        border_width = DEFAULT_TABLE_BORDER_WIDTH
        border_char = DEFAULT_TABLE_BORDER_CHAR
        border_attr = DEFAULT_TABLE_BORDER_ATTR

        if isinstance(border, tuple):

            try:
                border_width, border_char, border_attr = border
            except ValueError:
                try:
                    border_width, border_char = border
                except ValueError:
                    border_width = border

        elif isinstance(border, int):
            border_width = border

        self.columns.contents = intersperse(
            (urwid.AttrMap(urwid.Divider(border_char),
                          attr_map = self.border_attr_map,
                          focus_map = self.border_focus_map),
             ('given', border_width, False)),
            self.columns.contents)

        self.attr = urwid.AttrMap(
            self.columns,
            attr_map = self.attr_map,
            focus_map = self.focus_map,
        )
        super(DataTableRow, self).__init__(self.attr)

    def selectable(self):
        return True

    # def keypress(self, size, key):
    #     return super(DataTableRow, self).keypress(size, key)


    def set_focus_column(self, index):
        for i, cell in enumerate(self):
            if i == index:
                cell.highlight()
            else:
                cell.unhighlight()

    def __getitem__(self, position):
        return self.columns.contents[position][0]

    def __len__(self):
        return len(self.columns.contents)

    def __iter__(self):
        return iter( self.columns[i] for i in range(0, len(self.columns.contents), 2) )


class DataTableBodyRow(DataTableRow):

    ATTR = "table_row_body"

    CELL_CLASS = DataTableBodyCell


class DataTableHeaderRow(DataTableRow):

    signals = ['column_click']

    ATTR = "table_row_header"
    CELL_CLASS = DataTableHeaderCell

    def __init__(self, columns,
                 border=None, padding=None, sort=None,
                 *args, **kwargs):

        super(DataTableHeaderRow, self).__init__(
            columns, [c.label for c in columns],
            border=border,
            padding=padding,
            sort = sort,
            *args,
            **kwargs
        )

    def selectable(self):
        return False

    def update_sort(self, sort):
        for c in self.cells:
            # raise Exception(c)
            c.update_sort(sort)

class DataTableFooterRow(DataTableRow):

    ATTR = "table_row_footer"
    CELL_CLASS = DataTableFooterCell

    def __init__(self, columns, *args, **kwargs):
        super(DataTableFooterRow, self).__init__(columns, ["footer" for n in range(len(columns))])

    def selectable(self):
        return False

    def update(self):
        # FIXME
        pass
