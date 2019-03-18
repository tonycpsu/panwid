import logging
logger = logging.getLogger("panwid.datatable")

from datetime import datetime, date as datetype

from .common import *

class NoSuchColumnException(Exception):
    pass

def make_value_function(template):

    def inner(table, row):
        pos = table.index_to_position(row.get(table.index))
        return template.format(
            data=row,
            row=pos+1,
            rows_loaded = len(table),
            rows_total = table.query_result_count() if table.limit else "?"
        )

    return inner

class DataTableBaseColumn(object):

    _width = ("weight", 1)

    def __init__(
            self,
            padding = DEFAULT_CELL_PADDING,
            hide=False,
            width=None,
            min_width=None,
            attr = None

    ):
        self.hide = hide
        self.padding = padding

        if isinstance(self.padding, tuple):
            self.padding_left, self.padding_right = self.padding
        else:
            self.padding_left = self.padding_right = self.padding

        if width is not None:  self._width = width
        self.min_width = min_width
        self.attr = attr

        if isinstance(self._width, tuple):
            if self._width[0] != "weight":
                raise Exception(
                    "Column width %s not supported" %(self._width[0])
                )
            self.initial_sizing, self.initial_width = self._width
            self.min_width = 3 # FIXME
        elif isinstance(self._width, int):
            self.initial_sizing = "given"
            self.initial_width = self._width
            self.min_width = self.initial_width = self._width # assume starting width is minimum

        else:
            raise Exception(self._width)

        self.sizing = self.initial_sizing
        self.width = self.initial_width

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    def width_with_padding(self, table_padding=None):
        padding = 0
        if self.padding is None and table_padding is not None:
            padding = table_padding
        return self.width + self.padding_left + self.padding_right

    @property
    def index(self):
        return self.table.visible_columns.index(self)

    @property
    def header(self):
        try:
            return self.table.header.cells[self.index]
        except ValueError:
            return None



class DataTableColumn(DataTableBaseColumn):

    def __init__(self, name,
                 label=None,
                 value=None,
                 align="left", wrap="space",
                 pack=False,
                 no_clip_header = False,
                 truncate=False,
                 format_fn=None,
                 decoration_fn=None,
                 format_record = None, # format_fn is passed full row data
                 sort_key = None, sort_reverse=False,
                 sort_icon = None,
                 footer_fn = None, footer_arg = "values", **kwargs):

        super().__init__(**kwargs)
        self.name = name
        self.label = label if label is not None else name
        if value:
            if isinstance(value, str):
                self.value_fn = make_value_function(value)
            elif callable(value):
                self.value_fn = value
        else:
            self.value_fn = None
        self.align = align
        self.pack = pack
        self.wrap = wrap
        self.no_clip_header = no_clip_header
        self.truncate = truncate
        self.format_fn = format_fn
        self.decoration_fn = decoration_fn
        self.format_record = format_record
        self.sort_key = sort_key
        self.sort_reverse = sort_reverse
        self.sort_icon = sort_icon
        self.footer_fn = footer_fn
        self.footer_arg = footer_arg
        logger.debug(f"column {self.name}, width: {self.sizing}, {self.width}")


    @property
    def contents_width(self):
        try:
            index = next(i for i, c
                         in enumerate(self.table.visible_columns)
                         if getattr(c, "name", None) == self.name)
        except StopIteration:
            raise Exception(self.name, [ c.name for c in self.table.visible_columns])
        # logger.info(f"len: {len(self.table.body)}")

        l = [
            (
             getattr(r.cells[index].value, "min_width", None)
             or
             len(str(r.cells[index].formatted_value))
            ) + self.padding*2
            for r in (self.table.body)
        ] + [self.table.header.cells[index].min_width or 0] + [self.min_width or 0]
        return max(l)

    @property
    def minimum_width(self):
        # if self.sizing == "pack":
        if self.pack:
            # logger.info(f"min: {self.name}, {self.contents_width}")
            return self.contents_width
        else:
            return self.min_width or len(self.label) + self.padding_left + self.padding_right + (1 if self.sort_icon else 0)


    def _format(self, v):

        # First, call the format function for the column, if there is one
        if self.format_fn:
            try:
                v = self.format_fn(v)
            except Exception as e:
                logger.error("%s format exception: %s" %(self.name, v))
                logger.exception(e)
                raise e
        return self.format(v)


    def format(self, v):

        # Do our best to make the value into something presentable
        if v is None:
            v = " "
        elif isinstance(v, int):
            v = "%d" %(v)
        elif isinstance(v, float):
            v = "%.03f" %(v)
        elif isinstance(v, datetime):
            v = v.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(v, datetype):
            v = v.strftime("%Y-%m-%d")
        return v


class DataTableDivider(DataTableBaseColumn):

    _width = 1

    def __init__(self, char=" ", in_header=False, in_footer=False, **kwargs):
        super().__init__(**kwargs)
        self.char = char
        self.in_header = in_header
        self.in_footer = in_footer

    @property
    def name(self):
        return "divider"

    @property
    def value(self):
        # FIXME: should use SolidFill for rows that span multiple screen rows
        w = urwid.Divider(self.char)
        return w

    @property
    def contents_width(self):
        return len(self.char)

    @property
    def pack(self):
        return False

    @property
    def align(self):
        return "left"
