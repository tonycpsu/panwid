import unittest

from panwid.datatable import *
from orderedattrdict import AttrDict

class TestDataTableWithIndex(unittest.TestCase):

    def setUp(self):

        self.data = [
            dict(a=1, b=2.345, c="foo"),
            dict(a=2, b=4.817, c="bar"),
            dict(a=3, b=-3.19, c="baz")
        ]
        self.columns = [
            DataTableColumn("a"),
            DataTableColumn("b"),
            DataTableColumn("c")
        ]

    def test_create(self):

        dt = DataTable(self.columns, data=self.data, index="a")
        self.assertEqual(len(dt), 3)

    def test_create_without_index(self):

        dt = DataTable(self.columns, data=self.data)
        self.assertEqual(len(dt), 3)

    def test_add_row_with_index(self):

        dt = DataTable(self.columns, data=self.data, index="a")
        dt.add_row(dict(a=4, b=7.142, c="qux"))
        self.assertEqual(len(dt), 4)

    def test_add_row_without_index(self):

        dt = DataTable(self.columns, data=self.data)
        dt.add_row(dict(a=4, b=7.142, c="qux"))
        self.assertEqual(len(dt), 4)
