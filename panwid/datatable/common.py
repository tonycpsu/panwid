import urwid

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
