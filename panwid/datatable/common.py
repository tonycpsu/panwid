import urwid

DEFAULT_CELL_PADDING = 0
DEFAULT_TABLE_BORDER_WIDTH = 1
DEFAULT_TABLE_BORDER_CHAR = " "
DEFAULT_TABLE_BORDER_ATTR = None

DEFAULT_TABLE_BORDER = (
    DEFAULT_TABLE_BORDER_WIDTH,
    DEFAULT_TABLE_BORDER_CHAR,
)

class DataTableText(urwid.Text):

    DEFAULT_END_CHAR = u"\N{HORIZONTAL ELLIPSIS}"

    def truncate(self, width, end_char=None):
        # raise Exception(width)
        text = self.get_text()[0]
        max_width = width
        if end_char:
            if end_char is True:
                end_char = self.DEFAULT_END_CHAR
            max_width -= len(end_char)
        else:
            end_char=""
        # raise Exception(len(text), max_width)
        if len(text) > max_width:
            self.set_text(text[:max_width]+end_char)

    def __len__(self):
        return len(self.get_text()[0])
