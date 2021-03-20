panwid
======

A collection of widgets for [Urwid](https://urwid.org/).

Currently consists of the following sub-modules:

## autocomplete ##

Adds autocomplete functionality to a container widget.  See `Dropdown`
implementation for how it works until there's proper documentation.

## datatable ##

Widget for displaying tabular data.

Features include:
* Flexible options for column formatting and sorting
* Progressive loading / "infinite scrolling" for paginating large datasets
* Scrollbar with indicator showing position within dataset

[![asciicast](https://asciinema.org/a/iRbvnuv7DERhZrdKKBfpGtXqw.png)](https://asciinema.org/a/iRbvnuv7DERhZrdKKBfpGtXqw?autoplay=1)

## dialog ##

A set of simple classes for implementing pop-up dialogs.

## dropdown ##

Dropdown menu widget with autocomplete support.

[![asciicast](https://asciinema.org/a/m23L8xPJsTQRxzOCwvc1SuduN.png)](https://asciinema.org/a/m23L8xPJsTQRxzOCwvc1SuduN?autoplay=1)

## highlightable ##

Adds the ability for text widgets (or any widget with text in them) to have
strings highlighted in them.  See `Dropdown` implementation until there's proper
documentation.

## keymap ##

Adds ability to define keyboard mappings across multiple widgets in your
application without having to write Urwid `keypress`` methods. See `Dropdown`
implementation until there's proper documentation.

## progressbar ##

A configurable horizontal progress bar that uses unicode box drawing characters
for sub-character-width resolution.

## scroll ##

Makes any fixed or flow widget vertically scrollable.  Copied with permission
from `rndusr/stig`.

## sparkwidgets ##

A set of sparkline-ish widgets for displaying data visually using a small number
of screen characters.

## tabview ##

A container widget that allows selection of content via tab handles.

**TODOs**:

* Documentation
* Make more 16-color and non-unicode friendly
* Add combo box functionality to dropdown
* Update datatable so that footer functions calculate based on the entire
  dataset, not just visible rows.

