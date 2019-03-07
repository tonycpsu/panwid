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
            rows_total = table.query_result_count()
        )

    return inner

class DataTableColumn(object):

    def __init__(self, name,
                 label=None,
                 value=None,
                 width=('weight', 1),
                 min_width=None,
                 align="left", wrap="space",
                 padding = DEFAULT_CELL_PADDING, #margin=1,
                 truncate=False,
                 hide=False,
                 format_fn=None,
                 decoration_fn=None,
                 format_record = None, # format_fn is passed full row data
                 attr = None,
                 sort_key = None, sort_reverse=False,
                 sort_icon = None,
                 footer_fn = None, footer_arg = "values"):

        self.name = name
        self.label = label if label is not None else name
        if value:
            if isinstance(value, str):
                self.value_fn = make_value_function(value)
            elif callable(value):
                self.value_fn = value
        else:
            self.value_fn = None
        self.width = width
        self.min_width = min_width
        self.align = align
        self.wrap = wrap
        self.padding = padding
        self.truncate = truncate
        self.hide = hide
        self.format_fn = format_fn
        self.decoration_fn = decoration_fn
        self.format_record = format_record
        self.attr = attr
        self.sort_key = sort_key
        self.sort_reverse = sort_reverse
        self.sort_icon = sort_icon
        self.footer_fn = footer_fn
        self.footer_arg = footer_arg

        if isinstance(self.width, tuple):
            if self.width[0] != "weight":
                raise Exception(
                    "Column width %s not supported" %(col.width[0])
                )
            self.sizing, self.width = self.width
        elif isinstance(width, int):
            self.sizing = "given"
        else:
            self.sizing = width


    def width_with_padding(self, table_padding=None):
        padding = 0
        if self.padding is None and table_padding is not None:
            padding = table_padding
        return self.width + 2*padding


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
            v = ""
        elif isinstance(v, int):
            v = "%d" %(v)
        elif isinstance(v, float):
            v = "%.03f" %(v)
        elif isinstance(v, datetime):
            v = v.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(v, datetype):
            v = v.strftime("%Y-%m-%d")
        return v
