panwid
======

A collection of widgets for [urwid](https://urwid.org/).

Currently consists of the following:

## Datatable ##

Widget for displaying tabular data.

Features include:
* Flexible options for column formatting and sorting
* Progressive loading / "infinite scrolling" for paginating large datasets
* Scrollbar with indicator showing position within dataset

## ScrollingListbox ##

Listbox with an optional scrollbar.  Can signal to other widgets
(e.g. DataTable) when to fetch more data.

## Dropdown ##

Dropdown menu widget with autocomplete support.

TODOs:
* Documentation
* Make more 16-color and non-unicode friendly
* Add combo box functionality to dropdown
* Update datatable so that footer functions calculate based on the entire
  dataset, not just visible rows.


[![asciicast](https://asciinema.org/a/iRbvnuv7DERhZrdKKBfpGtXqw.png)](https://asciinema.org/a/iRbvnuv7DERhZrdKKBfpGtXqw?t=9&autoplay=1)
