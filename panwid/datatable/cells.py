import logging
logger = logging.getLogger("panwid.datatable")

from .common import *

import urwid
class DataTableCell(urwid.WidgetWrap):

    signals = ["click", "select"]

    ATTR = "table_cell"

    def __init__(self, table, column, row,
                 fill=False,
                 value_attr=None,
                 cell_selection=False,
                 padding=0,
                 *args, **kwargs):


        self.table = table
        self.column = column
        self.row = row

        self.fill = fill
        self.value_attr = value_attr
        self.cell_selection = cell_selection

        self.attr = self.ATTR
        self.attr_focused = "%s focused" %(self.attr)
        self.attr_column_focused = "%s column_focused" %(self.attr)
        self.attr_highlight = "%s highlight" %(self.attr)
        self.attr_highlight_focused = "%s focused" %(self.attr_highlight)
        self.attr_highlight_column_focused = "%s column_focused" %(self.attr_highlight)

        self._width = None
        self._height = None
        # self.width = None

        if column.padding:
            self.padding = column.padding
        else:
            self.padding = padding

        self.update_contents()

        self.cell_widget = urwid.Padding(
            self.contents,
            min_width = self.column.min_width,
            left=self.padding,
            right=self.padding
        )
        # if self.row.row_height is not None:
        self.cell_widget = urwid.Filler(self.cell_widget)

        self.normal_attr_map = {}
        self.highlight_attr_map = {}

        self.normal_focus_map = {}
        self.highlight_focus_map = {}
        self.highlight_column_focus_map = {}

        self.set_attr_maps()

        self.highlight_attr_map.update(self.table.highlight_map)
        self.highlight_focus_map.update(self.table.highlight_focus_map)

        self.attrmap = urwid.AttrMap(
            self.cell_widget,
            attr_map = self.normal_attr_map,
            focus_map = self.normal_focus_map
        )
        super(DataTableCell, self).__init__(self.attrmap)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.column.name}>"

    @property
    def value(self):
        return self.row[self.column.name]

    @value.setter
    def value(self, value):
        self.table.df[self.row.index, self.column.name] = value

    @property
    def formatted_value(self):

        v = self._format(self.value)
        if not self.width:
            return v
        # try:
        v = str(v)[:self.width-self.padding*2]
        # logger.info(f"formatted_value: {v}")
        return v
        # except TypeError:
            # raise Exception(f"{v}, {type(v)}")

    def update_contents(self):
        pass

    def set_attr_maps(self):

        self.normal_attr_map[None] = self.attr
        self.highlight_attr_map [None] = self.attr_highlight
        self.normal_focus_map[None] = self.attr_focused
        self.highlight_focus_map[None] = self.attr_highlight_focused

        if self.value_attr:
            self.normal_attr_map.update({None: self.value_attr})
            self.normal_focus_map.update({None: "%s focused" %(self.value_attr)})
            self.highlight_attr_map.update({None: "%s highlight" %(self.value_attr)})
            if self.cell_selection:
                self.highlight_focus_map.update({None: "%s highlight column_focused" %(self.value_attr)})
            else:
                self.highlight_focus_map.update({None: "%s highlight focused" %(self.value_attr)})

    def highlight(self):
        self.attrmap.set_attr_map(self.highlight_attr_map)
        self.attrmap.set_focus_map(self.highlight_focus_map)

    def unhighlight(self):
        self.attrmap.set_attr_map(self.normal_attr_map)
        self.attrmap.set_focus_map(self.normal_focus_map)

    def enable_selection(self):
        self.cell_selection = True

    def disable_selection(self):
        self.cell_selection = False

    def selectable(self):
        return self.cell_selection

    def keypress(self, size, key):
        try:
            key = super(DataTableCell, self).keypress(size, key)
        except AttributeError:
            pass
        return key
        # return super(DataTableCell, self).keypress(size, key)

    def _format(self, v):
        return self.column._format(v)

    def set_attr_map(self, attr_map):
        self.attrmap.set_attr_map(attr_map)

    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            urwid.emit_signal(self, "click")

    def set_attr(self, attr):
        attr_map = self.attrmap.get_attr_map()
        attr_map[None] = attr
        # self.attrmap.set_attr_map(attr_map)
        focus_map = self.attrmap.get_focus_map()
        focus_map[None] = "%s focused" %(attr)
        self.attrmap.set_focus_map(focus_map)

    def clear_attr(self, attr):
        attr_map = self.attrmap.get_attr_map()
        attr_map = self.normal_attr_map
        # attr_map[None] = self.attr
        self.attrmap.set_attr_map(attr_map)
        focus_map = self.normal_focus_map #.attr.get_focus_map()
        # focus_map[None] = self.attr_focused
        self.attrmap.set_focus_map(focus_map)

    def render(self, size, focus=False):
        maxcol = size[0]
        self._width = size[0]
        if len(size) > 1:
            maxrow = size[1]
            self._height = maxrow
        else:
            contents_rows = self.contents.rows(size, focus)
            self._height = contents_rows
        if (getattr(self.column, "truncate", None)
            and isinstance(self.contents, urwid.Widget)
            and hasattr(self.contents, "truncate")
        ):
            self.contents.truncate(
                self.width - (self.padding*2), end_char=self.column.truncate
            )
        # try:
        return super().render(size, focus)
        # except Exception as e:
        #     raise Exception(self, size, self.contents, e)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    # def rows(self, size, focus=False):
    #     if getattr(self.column, "truncate", None):
    #         return 1
    #     contents_rows = self.contents.rows((maxcol,), focus)
    #     return contents_rows
        # try:
        #     return super().rows(size, focus)
        # except Exception as e:
        #     raise Exception(self, size, self.contents, e)

class DataTableDividerCell(DataTableCell):

    # @property
    # def fiil(self):
    #     return self.row.row_height is not None

    def selectable(self):
        return False

    def update_contents(self):
        divider = self.column.value
        contents = urwid.Padding(
            divider,
            left = self.column.padding_left,
            right = self.column.padding_right
        )
        self.contents = contents
        # self._invalidate()

class DataTableBodyCell(DataTableCell):

    ATTR = "table_row_body"

    # @property
    # def formatted_value(self):
    #     v = self._format(
    #         self.value
    #         if not self.column.format_record
    #         else self.table.get_dataframe_row(self.row.index)
    #     )
    #     # if self.column.format_record:
    #     #     raise Exception(v)
    #     if not self.width:
    #         return v
    #     # raise Exception(self.width)
    #     return v[:self.width-self.padding*2]


    def update_contents(self):
        self.contents = self.table.decorate(
            self.row,
            self.column,
            self.formatted_value
        )


class DataTableDividerBodyCell(DataTableDividerCell, DataTableBodyCell):
    pass

class DataTableDetailCell(DataTableBodyCell):

    @property
    def value(self):
        return self.row.content


    def update_contents(self):
        self.contents = self.table.decorate(
            self.row,
            self.column,
            self.value
        )

class DataTableHeaderCell(DataTableCell):

    ATTR = "table_row_header"

    ASCENDING_SORT_MARKER = u"\N{UPWARDS ARROW}"
    DESCENDING_SORT_MARKER = u"\N{DOWNWARDS ARROW}"

    def __init__(self, *args, **kwargs):
        self.mouse_dragging = False
        self.mouse_drag_start = None
        self.mouse_drag_end = None
        super().__init__(*args, **kwargs)

    @property
    def index(self):
        return next(i for i, c in enumerate(self.table.visible_columns)
                    if c.name == self.column.name)

    @property
    def min_width(self):
        return len(self.label) + self.padding*2 + (1 if self.sort_icon else 0)

    def update_contents(self):

        self.label = self.column.label
        self.sort_icon = self.column.sort_icon or self.table.sort_icons

        self.columns = urwid.Columns([
            ('weight', 1,
             self.label
             if isinstance(self.label, urwid.Widget)
             else
             DataTableText(
                 self.label,
                 wrap = "space" if self.column.no_clip_header else "clip",
                 align=self.column.align
             )
            )
        ])

        if self.sort_icon:
            if self.column.align == "right":
                self.columns.contents.insert(0,
                    (DataTableText(""), self.columns.options("given", 1))
                )
            else:
                self.columns.contents.append(
                    (DataTableText(""), self.columns.options("given", 1))
                )
        self.contents = self.columns
        self.update_sort(self.table.sort_by)

    def set_attr_maps(self):

        self.normal_attr_map[None] = self.attr
        self.highlight_attr_map [None] = self.attr_highlight
        # if self.cell_selection:
        self.normal_focus_map[None] = self.attr_column_focused
        self.highlight_focus_map[None] = self.attr_highlight_column_focused


    def _format(self, v):
        return self.column.format(v)

    def selectable(self):
        return self.table.ui_sort

    def keypress(self, size, key):
        if key != "enter":
            return key
        urwid.emit_signal(self, "select", self)

    def mouse_event(self, size, event, button, col, row, focus):
        if event == "mouse press":
            logger.info("cell press")
            if self.mouse_drag_start is None:
                self.row.mouse_drag_source_column = col
            self.row.mouse_drag_source = self
            return False
        elif event == "mouse drag":
            logger.info("cell drag")
            self.mouse_dragging = True
            return False
                # urwid.emit_signal(self, "drag_start")
        elif event == "mouse release":
            logger.info("cell release")
            if self.mouse_dragging:
                self.mouse_dragging = False
                self.mouse_drag_start = None
            else:
                urwid.emit_signal(self, "select", self)
            self.mouse_drag_source = None
        #     self.mouse_drag_end = col
        #     raise Exception(self.mouse_drag_start, self.mouse_drag_end)
        #     self.mouse_drag_start = None
        super().mouse_event(size, event, button, col, row, focus)

    def update_sort(self, sort):
        if not self.sort_icon: return

        index = 0 if self.column.align=="right" else 1
        if sort and sort[0] == self.column.name:
            direction = self.DESCENDING_SORT_MARKER if sort[1] else self.ASCENDING_SORT_MARKER
            self.columns.contents[index][0].set_text(direction)
        else:
            self.columns.contents[index][0].set_text("")


class DataTableDividerHeaderCell(DataTableDividerCell, DataTableHeaderCell):
    pass


class DataTableFooterCell(DataTableCell):

    ATTR = "table_row_footer"

    def update_contents(self):
        if self.column.footer_fn and len(self.table.df):
            # self.table.df.log_dump()
            if self.column.footer_arg == "values":
                footer_arg = self.table.df[self.column.name].to_list()
            elif self.column.footer_arg == "rows":
                footer_arg = self.table.df.iterrows()
            elif self.column.footer_arg == "table":
                footer_arg = self.table.df
            else:
                raise Exception
            self.contents = self.table.decorate(
                self.row,
                self.column,
                self._format(self.column.footer_fn(self.column, footer_arg))
            )
        else:
            self.contents = DataTableText("")


class DataTableDividerFooterCell(DataTableDividerCell, DataTableHeaderCell):

    DIVIDER_ATTR = "table_divider_footer"
