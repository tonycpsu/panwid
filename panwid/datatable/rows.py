import functools
from collections import MutableMapping
import itertools

import urwid

from .cells import *
from .columns import *
from orderedattrdict import AttrDict

class DataTableRow(urwid.WidgetWrap):

    def __init__(self, table,
                 content=None,
                 row_height=None,
                 divider=None, padding=None,
                 cell_selection=False,
                 style = None,
                 *args, **kwargs):

        self.table = table
        self.row_height = row_height
        self.content = content
        # if not isinstance(self.content, int):
        #     raise Exception(self.content, type(self))
        self.divider = divider
        self.padding = padding
        self.cell_selection = cell_selection
        self.style = style

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

        self.contents_placeholder = urwid.WidgetPlaceholder(urwid.Text(""))

        w = self.contents_placeholder

        self.update()

        # if self.row_height:
        self.box = urwid.BoxAdapter(w, self.row_height or 1)

        self.pile = urwid.Pile([
            ("weight", 1, self.box)
        ])

        self.attrmap = urwid.AttrMap(
            self.pile,
            attr_map = self.attr_map,
            focus_map = self.focus_map,
        )

        super(DataTableRow, self).__init__(self.attrmap)

    def on_resize(self):

        if self.row_height is not None:
            return
        l = [1]
        # for i, c in enumerate(self.cells):
        for c, w in zip(self.cells, self.column_widths( (self.table.width,) )):
            # try:
            # c.contents.render( (self.table.visible_columns[i].width,), False)
            # except Exception as e:
            #     raise Exception(c, c.contents, e)

            try:
                rows = c.contents.rows( (w,) )
            except AttributeError:
                continue
            # logger.debug(f"{c}, {c.contents}, {w}, {rows}")

            # self.table.header.render((self.table.width, self.row_height), False)
            # raise Exception(self.table.header.data_cells[i].width)
            # rows = self.table.header.rows( (self.table.header.cells[i].width,) )
            # except Exception as e:
                # raise Exception(type(self), type(self.contents), e)
            # print(c, rows)
            l.append(rows)
        self.box.height = max(l)

        if self.details_open:
            self.open_details()

        # logger.debug(f"height: {self.box.height}")
        # (w, o) = self.pile.contents[0]
        # self.pile.contents[0] = (w, self.pile.options("given", max(l)))


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

    def resize_column(self, index, width):
        # col = self.table.visible_columns[index*2]
        (widget, options) = self.columns.contents[index*2]
        self.columns.contents[index*2] = (widget, self.columns.options(*width))

    def make_columns(self):

        # logger.info("make_columns")
        self.cells = self.make_cells()

        columns = urwid.Columns([])

        idx = None
        for i, cell in enumerate(self.cells):
            if not (idx or isinstance(cell, DataTableDividerCell)):
                idx = i
            col = self.table.visible_columns[i]
            options = columns.options(col.sizing, col.width_with_padding(self.padding))
            columns.contents.append(
                (cell, options)

            )
        if idx:
            columns.focus_position = idx
        return columns

    def make_contents(self):
        self.columns = self.make_columns()
        return self.columns

    @property
    def contents(self):
        return self.contents_placeholder.original_widget

    def update(self):
        contents = self.make_contents()
        # if self.row_height is None:
        #     contents = urwid.Filler(contents)
        self.contents_placeholder.original_widget = contents

    def selectable(self):
        return True

    def set_focus_column(self, index):
        for i, cell in enumerate(self):
            if i == index:
                cell.highlight()
            else:
                cell.unhighlight()
    def __len__(self):
        return len(self.columns.contents)

    def __iter__(self):
        return iter( self.columns[i] for i in range(0, len(self.columns.contents)) )

    @property
    def values(self):
        return AttrDict(list(zip([c.name for c in self.table.visible_columns], [ c.value for c in self ])))

    @property
    def data_cells(self):
        return [ c for c in self.cells if not isinstance(c, DataTableDividerCell)]

    def column_widths(self, size=None):
        if not size:
            size = (self.table.width,)
        return self.columns.column_widths(size)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height


class DataTableDetails(urwid.WidgetWrap):

    def __init__(self, row, content, indent=None):

        self.row = row

        self.columns = urwid.Columns([
            ("weight", 1, content)
        ])
        if indent:
            self.columns.contents.insert(0,
                (urwid.Padding(urwid.Text(" ")),
                 self.columns.options("given", indent)
                )
            )

        super().__init__(self.columns)

    def selectable(self):
        return not self.row.details_disabled


class DataTableBodyRow(DataTableRow):

    ATTR = "table_row_body"

    DIVIDER_CLASS = DataTableDividerBodyCell

    @property
    def index(self):
        return self.content

    @property
    def data(self):
        return self.table.get_dataframe_row(self.index)

    def __getitem__(self, column):
        cls = self.table.df[self.index, "_cls"]
        # row = self.data
        if (
                column not in self.table.df.columns
                and
                hasattr(cls, "__dataclass_fields__")
                and
                type(getattr(cls, column, None)) == property):
            # logger.info(f"__getitem__ property: {column}={getattr(self.data, column)}")
            return getattr(self.data, column)
        else:
            if column in self.table.df.columns:
                # logger.info(f"__getitem__: {column}={self.table.df.get(self.index, column)}")
                return self.table.df[self.index, column]
            else:
                raise Exception(column, self.table.df.columns)


    def __setitem__(self, column, value):
        self.table.df[self.index, column] = value
        # logger.info(f"__setitem__: {column}, {value}, {self.table.df[self.index, column]}")

    def get(self, key, default=None):

        try:
            return self[key]
        except KeyError:
            return default

    @property
    def details_open(self):
        # logger.info(f"{self['_details']}")
        return (self.get("_details") or {}).get("open")

    @details_open.setter
    def details_open(self, value):
        details = self["_details"]
        details["open"] = value
        self["_details"] = details

    @property
    def details_disabled(self):
        return (self.get("_details") or {}).get("disabled")

    @details_disabled.setter
    def details_disabled(self, value):
        details = self["_details"]
        details["disabled"] = value
        if value == True:
            self.details_focused = False
        self["_details"] = details

    @property
    def details_focused(self):
        return self.details_open and (self.pile.focus_position > 0)

    @details_focused.setter
    def details_focused(self, value):
        if value:
            self.pile.focus_position = 1
        else:
            self.pile.focus_position = 0

    def open_details(self):

        if not self.table.detail_fn or len(self.pile.contents) > 1:
            return
        content = self.table.detail_fn(self.data)

        self.table.header.render( (self.table.width,) )
        indent_width = 0
        visible_count = itertools.count()

        def should_indent(x):
            if (isinstance(self.table.detail_hanging_indent, int)
                and (x[2] is None or x[2] <= self.table.detail_hanging_indent)):
                return True
            elif (isinstance(self.table.detail_hanging_indent, str)
                and x[1].name != self.table.detail_hanging_indent):
                  return True
            return False

        if self.table.detail_hanging_indent:
            indent_width = sum([
                x[1].width if not x[1].hide else 0
                for x in itertools.takewhile(
                        should_indent,
                        [ (i, c, next(visible_count) if not c.hide else None)
                          for i, c in enumerate(self.table._columns) ]
                )
            ])

        self.details = DataTableDetails(self, content, indent_width)
        self.pile.contents.append(
            (self.details, self.pile.options("pack"))
        )
        self["_details"]["open"] = True


    def close_details(self):
        if not self.table.detail_fn or not self.details_open:
            return
        self["_details"]["open"] = False
        # del self.contents.contents[0]

        # self.box.height -= self.pile.contents[1][0].rows( (self.table.width,) )
        del self.pile.contents[1]

    def toggle_details(self):

        if self.details_open:
            self.close_details()
        else:
            self.open_details()

    # def enable_details(self):
    #     self["_details"]["disabled"] = False

    # def disable_details(self):
    #     self["_details"]["disabled"] = True

    # def focus_details(self):
    #     self.pile.focus_position = 1

    # def unfocus_details(self):
    #     self.pile.focus_position = 0


    def set_attr(self, attr):
        attr_map = self.attrmap.get_attr_map()
        attr_map[self.ATTR] = attr
        if self.cell_selection:
            attr_map[self.attr_highlight] = "%s highlight focused" %(attr)
        else:
            attr_map[self.attr_highlight] = "%s highlight" %(attr)
        self.attrmap.set_attr_map(attr_map)

        focus_map = self.attrmap.get_focus_map()
        focus_map[self.ATTR] = "%s focused" %(attr)
        focus_map[self.attr_highlight] = "%s highlight focused" %(attr)
        if self.cell_selection:
            focus_map[self.attr_focused] = "%s column_focused" %(attr)
            focus_map[self.attr_highlight_focused] = "%s highlight column_focused" %(attr)
        else:
            focus_map[self.attr_focused] = "%s focused" %(attr)
            focus_map[self.attr_highlight_focused] = "%s highlight focused" %(attr)
        self.attrmap.set_focus_map(focus_map)

    def clear_attr(self, attr):
        attr_map = self.attrmap.get_attr_map()
        for a in [self.ATTR, self.attr_highlight]:
            if a in attr_map:
                del attr_map[a]
        self.attrmap.set_attr_map(attr_map)
        focus_map = self.attrmap.get_focus_map()
        for a in [self.attr_focused, self.attr_highlight_focused]:
            if a in focus_map:
                del focus_map[a]
        focus_map[self.ATTR] = "%s focused" %(self.ATTR)
        self.attrmap.set_focus_map(focus_map)

    def make_cells(self):

        def col_to_attr(col):
            if col.attr is None:
                return None
            if callable(col.attr):
                return col.attr(self.data)
            elif col.attr in self.data:
                return self.data[col.attr]
            elif isinstance(col.attr, str):
                return col.attr
            else:
                return None

        return [
            DataTableBodyCell(
                self.table,
                col,
                self,
                # self.data[col.name] if not col.format_record else self.data,
                value_attr=col_to_attr(col),
                cell_selection=self.cell_selection
            )
            if isinstance(col, DataTableColumn)
            else DataTableDividerBodyCell(self.table, col, self)
            for i, col in enumerate(self.table.visible_columns)]

# class DataTableDetailRow(DataTableRow):

#     ATTR = "table_row_detail"

#     @property
#     def details(self):
#         return self.content

#     def make_contents(self):
#         col = DataTableColumn("details")
#         return DataTableDetailCell(self.table, col, self)

#     def selectable(self):
#         return self.table.detail_selectable


class DataTableHeaderRow(DataTableRow):

    signals = ["column_click", "drag"]

    ATTR = "table_row_header"

    DIVIDER_CLASS = DataTableDividerHeaderCell

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mouse_press = False
        self.mouse_dragging = False
        self.mouse_drag_start = None
        self.mouse_drag_end = None
        self.mouse_drag_source = None
        self.mouse_drag_source_column = None

    def make_cells(self):
        cells = [
            DataTableHeaderCell(
                self.table,
                col,
                self,
                sort=self.sort,
            )
            if isinstance(col, DataTableColumn)
            else DataTableDividerHeaderCell(self.table, col, self)
            for i, col in enumerate(self.table.visible_columns)]

        def sort_by_index(source, index):
            urwid.emit_signal(self, "column_click", index)

        if self.table.ui_sort:
            for i, cell in enumerate([c for c in cells if not isinstance(c, DataTableDividerCell)]):
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
        for c in self.data_cells:
            c.update_sort(sort)

    def mouse_event(self, size, event, button, col, row, focus):

        if not super().mouse_event(size, event, button, col, row, focus):
            if event == "mouse press":
                self.mouse_press = True
                if self.mouse_drag_start is None:
                    self.mouse_drag_start = col
            elif event == "mouse drag":
                if self.mouse_press:
                    self.mouse_dragging = True
                    # FIXME
                    # self.mouse_drag_end = col
                    # urwid.emit_signal(
                    #     self,
                    #     "drag",
                    #     self.mouse_drag_source,
                    #     self.mouse_drag_source_column,
                    #     self.mouse_drag_start, self.mouse_drag_end
                    # )
                    # self.mouse_dragging = False
                    # self.mouse_drag_start = None
                    # FIXME
            elif event == "mouse release":
                self.mouse_press = False
                if self.mouse_dragging:
                    # raise Exception(f"drag: {self.mouse_drag_source}")
                    self.mouse_dragging = False
                    self.mouse_drag_end = col
                    # raise Exception(self.mouse_drag_start)
                    urwid.emit_signal(
                        self,
                        "drag",
                        self.mouse_drag_source,
                        self.mouse_drag_source_column,
                        self.mouse_drag_start, self.mouse_drag_end
                    )
                    # raise Exception(self.mouse_drag_source.column.name, self.mouse_drag_start, self.mouse_drag_end)
                    self.mouse_drag_source = None
                    self.mouse_drag_start = None



class DataTableFooterRow(DataTableRow):

    ATTR = "table_row_footer"

    DIVIDER_CLASS = DataTableDividerFooterCell

    def make_cells(self):
        return [
            DataTableFooterCell(
                self.table,
                col,
                self,
                sort=self.sort,
            )
            if isinstance(col, DataTableColumn)
            else DataTableDividerBodyCell(self.table, col, self)
            for i, col in enumerate(self.table.visible_columns)]

    def selectable(self):
        return False
