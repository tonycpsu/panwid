import urwid

from .cells import *
import functools
from orderedattrdict import AttrDict

DEFAULT_CELL_PADDING = 0
DEFAULT_TABLE_BORDER_WIDTH = 1
DEFAULT_TABLE_BORDER_CHAR = " "
DEFAULT_TABLE_BORDER_ATTR = None

DEFAULT_TABLE_BORDER = (
    DEFAULT_TABLE_BORDER_WIDTH,
    DEFAULT_TABLE_BORDER_CHAR,
)

class DataTableRow(urwid.WidgetWrap):

    def __init__(self, table, index=None,
                 border=None, padding=None,
                 cell_selection=False,
                 *args, **kwargs):

        self.table = table
        self.index = index
        self.border = border
        self.padding = padding
        self.cell_selection = cell_selection
        self.sort = self.table.sort_by
        self.attr = self.ATTR
        self.attr_focused = "%s focused" %(self.attr)
        self.attr_column_focused = "%s column_focused" %(self.attr)
        self.attr_highlight = "%s highlight" %(self.attr)
        self.attr_highlight_focused = "%s focused" %(self.attr_highlight)
        self.attr_highlight_column_focused = "%s column_focused" %(self.attr_highlight)
        self.attr_map =  {
            None: self.attr,
        }

        self.focus_map = {
            self.attr: self.attr_focused,
            self.attr_highlight: self.attr_highlight_focused,
        }

        # needed to restore if cell selection is toggled
        self.original_focus_map = self.focus_map.copy()

        # if self.cell_selection:
        self.focus_map.update({
            self.attr_focused: self.attr_column_focused,
            self.attr_highlight_focused: self.attr_highlight_column_focused,
        })
        self.focus_map.update(self.table.column_focus_map)
        self.cell_selection_focus_map = self.focus_map.copy()

        if cell_selection:
            self.enable_cell_selection()
        else:
            self.disable_cell_selection()

        self.focus_map.update(table.focus_map)

        self.columns_placeholder = urwid.WidgetPlaceholder(urwid.Text(""))
        self.attrmap = urwid.AttrMap(
            self.columns_placeholder,
            attr_map = self.attr_map,
            focus_map = self.focus_map,
        )
        self.update()
        super(DataTableRow, self).__init__(self.attrmap)

    def keypress(self, size, key):
        try:
            key = super(DataTableRow, self).keypress(size, key)
        except AttributeError:
            pass
        return key

    def enable_cell_selection(self):
        self.cell_selection = True
        self.focus_map = self.cell_selection_focus_map

    def disable_cell_selection(self):
        self.cell_selection = False
        self.focus_map = self.original_focus_map

    def update(self):

        self.cells = self.make_cells()

        self.columns = urwid.Columns([])

        for i, cell in enumerate(self.cells):
            col = self.table.visible_columns[i]
            self.columns.contents.append(
                (cell, self.columns.options(col.sizing, col.width_with_padding(self.padding)))
            )

        border_width = DEFAULT_TABLE_BORDER_WIDTH
        border_char = DEFAULT_TABLE_BORDER_CHAR
        border_attr_map = self.attr_map.copy()

        if isinstance(self.border, tuple):

            try:
                border_width, border_char, border_attr = self.border
                border_attr_map.update({None: border_attr})
                # border_focus_map.update({None: "%s focused" %(border_attr)})
            except ValueError:
                try:
                    border_width, border_char = self.border
                except ValueError:
                    border_width = self.border

        elif isinstance(self.border, int):
            border_width = self.border

        self.columns.contents = intersperse(
            (urwid.AttrMap(urwid.Text(border_char),
                           attr_map = border_attr_map),
             ('given', border_width, False)),
            self.columns.contents)

        self.pile = urwid.Pile([
            ('weight', 1, self.columns)
        ])
        self.columns_placeholder.original_widget = self.pile


    def selectable(self):
        return True

    def set_focus_column(self, index):
        for i, cell in enumerate(self):
            if i == index:
                cell.highlight()
            else:
                cell.unhighlight()

    def __getitem__(self, position):
        # return self.columns.contents[position][0]
        return self.cells[position]

    def __len__(self):
        return len(self.columns.contents)

    def __iter__(self):
        return iter( self.columns[i] for i in range(0, len(self.columns.contents), 2) )

    @property
    def values(self):
        return AttrDict(list(zip([c.name for c in self.table.visible_columns], [ c.value for c in self ])))


class DataTableBodyRow(DataTableRow):

    ATTR = "table_row_body"

    def __init__(self, table, data, *args, **kwargs):

        if isinstance(data, list):
            data = dict(list(zip([c.name for c in table.columns], data)))
        self.data = AttrDict(
            (k, v(data) if callable(v) else v)
            for k, v in list(data.items())
        )

        self.details_open = False
        super(DataTableBodyRow, self).__init__(table, *args, **kwargs)

    def open_details(self):

        if not self.table.detail_fn or self.details_open:
            return
        content = self.table.detail_fn(self.data)
        if self.table.detail_column:
            try:
                col_index = self.table.visible_column_index(self.table.detail_column)
            except IndexError:
                col_index = 0
        else:
            col_index = 0

        v = [ None for n in range(len(self.table.header.columns.contents)+1) ]
        row = DataTableBodyRow(self.table, v)

        for i in range(0, len(row.columns.contents)):
            if i/2 == col_index:
                row.columns.contents[i] = (content, row.columns.options("weight", 1))
            else:
                row.columns.contents[i] = (urwid.Text(""), row.columns.contents[i][1])
        if col_index*2 < len(self.table.header.columns.contents):
            del row.columns.contents[(col_index*2)+1:]
        self.pile.contents.insert(0,
            (urwid.Filler(urwid.Text("")), self.pile.options("given", 1))
        )
        row.selectable = lambda: False
        self.pile.contents.append(
            (row, self.pile.options("pack"))
        )
        self.pile.focus_position = 1
        self.details_open = True

    def close_details(self):
        if not self.table.detail_fn or not self.details_open:
            return
        self.details_open = False
        del self.pile.contents[0]
        del self.pile.contents[1]

    def toggle_details(self):

        if self.details_open:
            self.close_details()
        else:
            self.open_details()

    def set_attr(self, attr):
        attr_map = self.attrmap.get_attr_map()
        attr_map[self.ATTR] = attr
        self.attrmap.set_attr_map(attr_map)
        focus_map = self.attrmap.get_focus_map()
        focus_map[self.ATTR] = "%s focused" %(attr)
        self.attrmap.set_focus_map(focus_map)

    def clear_attr(self, attr):
        attr_map = self.attrmap.get_attr_map()
        if self.ATTR in attr_map:
            del attr_map[self.ATTR]
        self.attrmap.set_attr_map(attr_map)
        focus_map = self.attrmap.get_focus_map()
        focus_map[self.ATTR] = "%s focused" %(self.ATTR)
        self.attrmap.set_focus_map(focus_map)

    def make_cells(self):

        def col_to_attr(col):
            if callable(col.attr):
                return col.attr(self.data)
            elif col.attr in self.data:
                return self.data[col.attr]
            # elif isinstance(col.attr, str):
            #     return col.attr
            else:
                return None

        return [
            DataTableBodyCell(
                self.table,
                col,
                self.data[col.name],
                value_attr=col_to_attr(col),
                cell_selection=self.cell_selection
            )
            for i, col in enumerate(self.table.visible_columns)]



class DataTableHeaderRow(DataTableRow):

    signals = ['column_click']

    ATTR = "table_row_header"

    def make_cells(self):
        cells = [
            DataTableHeaderCell(
                self.table,
                col,
                sort=self.sort,
            )
            for i, col in enumerate(self.table.visible_columns)]

        def sort_by_index(source, index):
            urwid.emit_signal(self, "column_click", index)

        if self.table.ui_sort:
            for i, cell in enumerate(cells):
                urwid.connect_signal(
                    cell,
                    'click',
                    functools.partial(sort_by_index, index=i)
                )
                urwid.connect_signal(
                    cell,
                    "select",
                    functools.partial(sort_by_index, index=i)
                )

        return cells

    def selectable(self):
        return self.table.ui_sort

    def update_sort(self, sort):
        for c in self.cells:
            c.update_sort(sort)


class DataTableFooterRow(DataTableRow):

    ATTR = "table_row_footer"

    def make_cells(self):
        return [
            DataTableFooterCell(
                self.table,
                col,
                sort=self.sort,
            )
            for i, col in enumerate(self.table.visible_columns)]

    def selectable(self):
        return False

    # def update(self):
    #     super(DataTableFooterRow, self).update()
    #     for c in self.cells:
    #         c.update()
