import logging
logger = logging.getLogger("urwid_datatable")
import raccoon as rc

class DataTableDataFrame(rc.DataFrame):

    DATA_TABLE_COLUMNS = ["_dirty", "_focus_position", "_rendered_row"]

    def __init__(self, data=None, columns=None, index=None, index_name="index", use_blist=False, sorted=None):
        if not index_name in columns:
            columns = [index_name] + columns
        super(DataTableDataFrame, self).__init__(
            data=data,
            columns=columns,
            index=index,
            index_name=index_name,
            use_blist=use_blist,
            sorted=sorted
        )
        for c in self.DATA_TABLE_COLUMNS:
            self[c] = None


    def log_dump(self, n=5):
        logger.debug("index: %s [%s%s]\n%s" %(
            self.index_name,
            ",".join([str(x) for x in self.index[0:min(n, len(self.index))]]),
            "..." if len(self.index) > n else "",
            self.head(n)))


    def append_rows(self, rows):

        colnames =  list(self.columns)

        try:
            columns = list(set().union(*(d.keys() for d in rows)))
            data = dict(
                zip((columns),
                    [ list(z) for z in zip(*[[
                        d.get(k, None) for k in columns ] for d in rows])]
                )
            )
            if self.index_name not in columns:
                index = range(len(self), len(data.values()[0]))
                data[self.index_name] = index
            else:
                index = data[self.index_name]
        except IndexError:
            columns = list(self.columns)
            data = { k: [] for k in colnames }
            index = None
        kwargs = dict(
            columns = columns,
            data = data,
            use_blist=True,
            sorted=False,
            index=index,
            index_name = self.index_name,
        )
        self.log_dump()
        newdata = DataTableDataFrame(**kwargs)
        newdata.log_dump()
        self.append(newdata)

    def add_column(self, column, data=None):
        self.log_dump()
        self[column] = data
        self.log_dump()

    def clear(self):
        self.delete_rows(self.index)
