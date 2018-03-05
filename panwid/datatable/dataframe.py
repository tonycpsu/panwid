import logging
logger = logging.getLogger("panwid.datatable")
import raccoon as rc
import collections

class DataTableDataFrame(rc.DataFrame):

    DATA_TABLE_COLUMNS = ["_dirty", "_focus_position", "_value_fn", "_rendered_row"]

    def __init__(self, data=None, columns=None, index=None, index_name="index", use_blist=False, sort=None):

        if columns and not index_name in columns:
            columns = [index_name] + columns
        super(DataTableDataFrame, self).__init__(
            data=data,
            columns=columns,
            index=index,
            index_name=index_name,
            use_blist=use_blist,
            sort=sort
        )
        for c in self.DATA_TABLE_COLUMNS:
            self[c] = None

    def _validate_index(self, indexes):
        try:
            return super(DataTableDataFrame, self)._validate_index(indexes)
        except ValueError:
            logger.error("duplicates in index: %s" %(
                [item for item, count
                 in list(collections.Counter(indexes).items()) if count > 1
                ]))
            raise


    def log_dump(self, n=5, columns=None, label=None):
        df = self
        if columns:
            if not isinstance(columns, list):
                columns = [columns]
            df = df[columns]
        logger.info("%slength: %d, index: %s [%s%s]\n%s" %(
            "%s, " %(label) if label else "",
            len(self),
            self.index_name,
            ",".join([str(x) for x in self.index[0:min(n, len(self.index))]]),
            "..." if len(self.index) > n else "",
            df.head(n)))


    def append_rows(self, rows):

        colnames =  list(self.columns)
        length = len(rows)

        try:
            columns = list(set().union(*(list(d.keys()) for d in rows)))
            data = dict(
                list(zip((columns),
                    [ list(z) for z in zip(*[[
                        d.get(k, None) for k in columns ] for d in rows])]
                ))
            )
            if self.index_name not in columns:
                index = list(range(len(self), len(self) + length))
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
            sort=False,
            index=index,
            index_name = self.index_name,
        )
        # self.log_dump(10, label="before")
        newdata = DataTableDataFrame(**kwargs)
        # newdata.log_dump()
        self.append(newdata)
        # self.log_dump(10, label="after")

    # def add_column(self, column, data=None):
    #     self[column] = data

    def clear(self):
        self.delete_all_rows()
        # self.delete_rows(self.index)
