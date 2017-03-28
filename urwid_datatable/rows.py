import urwid

from .cells import *

class DataTableRow(urwid.WidgetWrap):

    border_attr_map = { None: "table_border" }
    border_focus_map = { None: "table_border focused" }

    def __init__(self, table, data, index=None, row_number=None,
                 border=None, padding=None,
                 sort=None, sort_icons=None,
                 *args, **kwargs):

        self.table = table
        self.data = data
        self.index = index
        self._row_number = row_number
        self.border = border
        self.padding = padding
        self.sort = sort
        self.sort_icons = sort_icons
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
            self.data = dict(zip([c.name for c in self.table.columns], self.data))

        self.columns_placeholder = urwid.WidgetPlaceholder(urwid.Text(""))
        self.attr = urwid.AttrMap(
            self.columns_placeholder,
            attr_map = self.attr_map,
            focus_map = self.focus_map,
        )
        self.update()
        super(DataTableRow, self).__init__(self.attr)

    def update(self):

        self.cells = self.make_cells()

        self.columns = urwid.Columns([])

        for i, cell in enumerate(self.cells):
            col = self.table.columns[i]
            self.columns.contents.append(
                (cell, self.columns.options(col.sizing, col.width_with_padding(self.padding)))
            )

        border_width = DEFAULT_TABLE_BORDER_WIDTH
        border_char = DEFAULT_TABLE_BORDER_CHAR
        border_attr = DEFAULT_TABLE_BORDER_ATTR

        if isinstance(self.border, tuple):

            try:
                border_width, border_char, border_attr = self.border
            except ValueError:
                try:
                    border_width, border_char = self.border
                except ValueError:
                    border_width = self.border

        elif isinstance(self.border, int):
            border_width = self.border

        self.columns.contents = intersperse(
            (urwid.AttrMap(urwid.Divider(border_char),
                          attr_map = self.border_attr_map,
                          focus_map = self.border_focus_map),
             ('given', border_width, False)),
            self.columns.contents)

        self.columns_placeholder.original_widget = self.columns


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

    @property
    def row_number(self):
        return self._row_number


class DataTableBodyRow(DataTableRow):

    ATTR = "table_row_body"

    def make_cells(self):
        return [
            DataTableBodyCell(
                col,
                self.data[col.name] if not col.value_fn else col.value_fn(self),
                sort=self.sort,
                sort_icon=self.sort_icons,
                attr=self.data.get(col.attr, None))
            for i, col in enumerate(self.table.columns)]



class DataTableHeaderRow(DataTableRow):

    signals = ['column_click']

    ATTR = "table_row_header"

    def __init__(self, table,
                 border=None, padding=None, sort=None,
                 *args, **kwargs):

        super(DataTableHeaderRow, self).__init__(
            table,
            [c.label if c.label else c.name for c in table.columns],
            border=border,
            padding=padding,
            sort = sort,
            *args,
            **kwargs
        )

    def make_cells(self):
        return [
            DataTableHeaderCell(
                col,
                sort=self.sort,
                sort_icon=self.sort_icons,
                attr=self.data.get(col.attr, None))
            for i, col in enumerate(self.table.columns)]


    def selectable(self):
        return False

    def update_sort(self, sort):
        for c in self.cells:
            # raise Exception(c)
            c.update_sort(sort)


class DataTableFooterRow(DataTableRow):

    ATTR = "table_row_footer"

    def __init__(self, table, *args, **kwargs):
        super(DataTableFooterRow, self).__init__(
            table,
            ["footer" for n in range(len(table.columns))]
        )

    def make_cells(self):
        return [
            DataTableFooterCell(
                col,
                self.data.get(col.name),
                sort=self.sort,
                sort_icon=self.sort_icons,
                attr=self.data.get(col.attr, None))
            for i, col in enumerate(self.table.columns)]

    def selectable(self):
        return False
