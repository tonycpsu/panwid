import urwid
import itertools

DEFAULT_CELL_PADDING = 0

def partition(pred, iterable):
    'Use a predicate to partition entries into false entries and true entries'
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = itertools.tee(iterable)
    return itertools.filterfalse(pred, t1), filter(pred, t2)

intersperse = lambda e,l: sum([[x, e] for x in l],[])[:-1]

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
