#!/usr/bin/env python3

import urwid

from .sparkwidgets import *

class ProgressBar(urwid.WidgetWrap):

    def __init__(self, width, maximum, value=0,
                 progress_color=None, remaining_color=None):
        self.width = width
        self.maximum = maximum
        self.value = value
        self.progress_color = progress_color or DEFAULT_BAR_COLOR
        self.remaining_color = remaining_color or DEFAULT_LABEL_COLOR
        self.placeholder = urwid.WidgetPlaceholder(urwid.Text(""))
        self.update()
        super().__init__(self.placeholder)

    def pack(self, size, focus=False):
        return (self.width, 1)

    @property
    def value_label(self):
        label_text = str(self.value)
        bar_len = self.spark_bar.bar_width(0)
        attr1 = f"{DEFAULT_LABEL_COLOR}:{self.progress_color}"
        content = [(attr1, label_text[:bar_len])]
        if len(label_text) > bar_len-1:
            attr2 = f"{DEFAULT_LABEL_COLOR}:{self.remaining_color}"
            content.append((attr2, label_text[bar_len:]))
        return urwid.Text(content)

    @property
    def maximum_label(self):
        label_text = str(self.maximum)
        bar_len = self.spark_bar.bar_width(1)
        attr1 = f"{DEFAULT_LABEL_COLOR}:{self.remaining_color}"
        content = []
        if bar_len:
            content.append((attr1, label_text[-bar_len:]))
        if len(label_text) > bar_len:
            attr2 = f"{DEFAULT_LABEL_COLOR}:{self.progress_color}"
            content.insert(0, (attr2, label_text[:-bar_len or None]))
        return urwid.Text(content)

    def update(self):
        value_label = None
        maximum_label = None

        self.spark_bar = SparkBarWidget(
            [
                SparkBarItem(self.value, bcolor=self.progress_color),
                SparkBarItem(self.maximum-self.value, bcolor=self.remaining_color),
            ], width=self.width
        )
        overlay1 = urwid.Overlay(
            urwid.Filler(self.value_label),
            urwid.Filler(self.spark_bar),
            "left",
            len(self.value_label.get_text()[0]),
            "top",
            1
        )
        label_len = len(self.maximum_label.get_text()[0])
        overlay2 =  urwid.Overlay(
            urwid.Filler(self.maximum_label),
            overlay1,
            "left",
            label_len,
            "top",
            1,
            left=self.width - label_len
        )
        self.placeholder.original_widget = urwid.BoxAdapter(overlay2, 1)

    def set_value(self, value):
        self.value = value
        self.update()

    @property
    def items(self):
        return self.spark_bar.items

__all__ = ["ProgressBar"]
