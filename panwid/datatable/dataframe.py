import logging
logger = logging.getLogger("panwid.datatable")
import raccoon as rc
import collections

class DataTableDataFrame(rc.DataFrame):

    DATA_TABLE_COLUMNS = ["_dirty", "_focus_position", "_value_fn", "_cls", "_details", "_rendered_row"]

    def __init__(self, data=None, columns=None, index=None, index_name="index", sort=None):

        self.sidecar_columns = []
        if columns and not index_name in columns:
            columns.insert(0, index_name)
        columns += self.DATA_TABLE_COLUMNS
        super(DataTableDataFrame, self).__init__(
            data=data,
            columns=columns,
            index=index,
            index_name=index_name,
            sort=sort
        )
        # for c in self.DATA_TABLE_COLUMNS:
        #     self[c] = None

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

    @staticmethod
    def extract_keys(obj):
        return obj.keys() if hasattr(obj, "keys") else obj.__dict__.keys()

    @staticmethod
    def extract_value(obj, key):
        if isinstance(obj, collections.abc.MutableMapping):
            # raise Exception(obj)
            return obj.get(key, None)
        else:
            return getattr(obj, key, None)

    def transpose_data(self, rows, with_sidecar = False):

        # raise Exception([ r[self.index_name] for r, s in rows])

        if with_sidecar:
            data_columns, self.sidecar_columns = [
                list(set().union(*x))
                for x in zip(*[(
                        self.extract_keys(d),
                        self.extract_keys(s)
                )
                               for d, s in rows ])
            ]

        else:
            data_columns = list(
                set().union(*(list(d.keys()
                               if hasattr(d, "keys")
                               else d.__dict__.keys())
                          for d in rows))
            )

        data_columns += [
            c for c in self.columns
            if c not in data_columns
            and c not in self.sidecar_columns
            and c != self.index_name
            and c not in self.DATA_TABLE_COLUMNS
        ]
        data_columns += ["_cls"]

        data = dict(
                    list(zip((data_columns + self.sidecar_columns),
                        [ list(z) for z in zip(*[[
                            self.extract_value(d, k) if k in data_columns else self.extract_value(s, k)
                            for k in data_columns + self.sidecar_columns]
                            for d, s in (
                                rows
                                if with_sidecar
                                else [ (r, {})  for r in rows]
                            )
                        ])]
                    ))
                )

        return data


    def update_rows(self, rows, replace=False, with_sidecar = False):

        if not len(rows):
            return []

        data = self.transpose_data(rows, with_sidecar = with_sidecar)
        # data["_details"] = [{"open": False, "disabled": False}] * len(rows)
        data["_cls"] = [type(rows[0][0] if with_sidecar else rows[0])] * len(rows) # all rows assumed to have same class

        # raise Exception(data["_cls"])
        # if not "_details" in data:
        #     data["_details"] = [{"open": False, "disabled": False}] * len(rows)

        if replace:
            if len(rows):
                indexes = [x for x in self.index if x not in data.get(self.index_name, [])]
                if len(indexes):
                    self.delete_rows(indexes)
            else:
                self.delete_all_rows()

            # logger.info(f"update_rowGs: {self.index}, {data[self.index_name]}")

        if self.index_name not in data:
            index = list(range(len(self), len(self) + len(rows)))
            data[self.index_name] = index
        else:
            index = data[self.index_name]

        for c in data.keys():
            # try:
                # raise Exception(data[self.index_name], c, data[c])
                self.set(data[self.index_name], c, data[c])
            # except ValueError as e:
            #     logger.error(e)
            #     logger.info(f"update_rows: {self.index}, {data}")
            #
        for idx in data[self.index_name]:
            if not self.get(idx, "_details"):
                self.set(idx, "_details", {"open": False, "disabled": False})

        return data.get(self.index_name, [])

    def append_rows(self, rows):

        length = len(rows)
        if not length:
            return

        colnames = list(self.columns) + [c for c in self.DATA_TABLE_COLUMNS if c not in self.columns]

        # data_columns = list(set().union(*(list(d.keys()) for d in rows)))
        data = self.transpose_data(rows)
        colnames += [c for c in data.keys() if c not in colnames]

        for c in self.columns:
            if not c in data:
                data[c] = [None]*length

        for c in colnames:
            if not c in self.columns:
                self[c] = None

        kwargs = dict(
            columns =  colnames,
            data = data,
            sort=False,
            index=data[self.index_name],
            index_name = self.index_name,
        )

        try:
            newdata = DataTableDataFrame(**kwargs)
        except ValueError:
            raise Exception(kwargs)
        # newdata.log_dump()
        # self.log_dump(10, label="before")
        try:
            self.append(newdata)
        except ValueError:
            raise Exception(f"{self.index}, {newdata}")
        # self.log_dump(10, label="after")

    # def add_column(self, column, data=None):
    #     self[column] = data

    def clear(self):
        self.delete_all_rows()
        # self.delete_rows(self.index)
