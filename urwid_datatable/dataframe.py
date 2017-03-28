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

        # logger.info("df.append_rows: %s" %(rows))
        # columns = [self.index_name] + self.DATA_TABLE_COLUMNS + list(self.columns)
        # raise Exception(self.columns)
        colnames =  list(self.columns)
        # colnames = [ c for c in list(self.columns) if c != self.index_name ]
        # data = dict(
        #     zip((r for r in rows[0] if r in colnames),
        #         [ list(z) for z in zip(*[[ v for k, v in d.items() if k in colnames] for d in rows])]
        #     )
        # )


        try:
            columns = list(set().union(*(d.keys() for d in rows)))
            data = dict(
                # zip((colnames),
                zip((columns),
                    [ list(z) for z in zip(*[[
                        d.get(k, None) for k in columns ] for d in rows])]
                )
            )
            # raise Exception(data)
            if self.index_name not in columns:
                # logger.debug("making new index")
                index = range(len(self), len(data.values()[0]))
                data[self.index_name] = index
            else:
                index = data[self.index_name]
        except IndexError:
            columns = list(self.columns)
            data = { k: [] for k in colnames }
            index = None
        # else:
        #     index = None
        # logger.info(sorted(data.keys()))
        # logger.info(sorted(colnames))
        # columns = [c for c in self.columns if not c.startswith("_")]
        # print "newdata: %s" %(columns)
        # logger.debug("df.append_rows data: %s" %(data))
        kwargs = dict(
            # columns = list(self.columns),
            columns = columns,
            data = data,
            use_blist=True,
            sorted=False,
            index=index,
            index_name = self.index_name,
        )
        self.log_dump()
        # if self.index_name in data.keys():
        #     kwargs["index"] = data[self.index_name]# if self.index_name in data.keys() else None,
        # else:
        #     kwargs["index"] = range(len(self), len(data.values()[0]))
        # raise Exception(kwargs["index"])
        newdata = DataTableDataFrame(**kwargs)
        newdata.log_dump()
        self.append(newdata)

    def add_column(self, column):
        # self.columns.append(column)
        self[column] = None
        logger.debug(self.columns)


    def clear(self):
        self.delete_rows(self.index)
