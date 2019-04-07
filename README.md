panwid
======

A collection of widgets for [Urwid](https://urwid.org/).

Currently consists of the following:

## Dropdown ##

Dropdown menu widget with autocomplete support.

[![asciicast](https://asciinema.org/a/m23L8xPJsTQRxzOCwvc1SuduN.png)](https://asciinema.org/a/m23L8xPJsTQRxzOCwvc1SuduN?autoplay=1)

## DataTable ##

Widget for displaying tabular data.

Features include:
* Flexible options for column formatting and sorting
* Progressive loading / "infinite scrolling" for paginating large datasets
* Scrollbar with indicator showing position within dataset

[![asciicast](https://asciinema.org/a/iRbvnuv7DERhZrdKKBfpGtXqw.png)](https://asciinema.org/a/iRbvnuv7DERhZrdKKBfpGtXqw?autoplay=1)

## ScrollingListbox ##

Listbox with an optional scrollbar.  Can signal to other widgets
(e.g. DataTable) when to fetch more data.  Used by both Dropdown and
DataTable, but can be used separately.

## TabView ##

A container widget that allows selection of content via tab handles.

**TODOs**:

* Documentation
* Make more 16-color and non-unicode friendly
* Add combo box functionality to dropdown
* Update datatable so that footer functions calculate based on the entire
  dataset, not just visible rows.

