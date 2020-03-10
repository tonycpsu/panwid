import logging
logger = logging.getLogger("panwid.tabview")

import urwid
from urwid_utils.palette import *

# Based on the tabview widget from github/@ountainstorm
# https://github.com/mountainstorm/mt_urwid/

class TabHandle(urwid.WidgetWrap):

    LABEL_CHARS_UNLOCKED = u"\u24e7 "
    LABEL_CHARS_LOCKED = u"\u25cb "

    def __init__(self, tab_view, title, locked=False, padding = 3,
                 attr_inactive = {}, attr_active = {}):
        self.tab_view = tab_view
        self.title = title
        self.locked = locked
        if locked:
            self.label = self.LABEL_CHARS_LOCKED + title
        else:
            self.label = self.LABEL_CHARS_UNLOCKED + title

        self.label = ' '*padding + self.label + ' '*padding

        self.text = urwid.SelectableIcon(self.label)
        # self.padding = urwid.Padding(self.text, align="left", width=20, left=3, right=3)
        self.attr = urwid.AttrMap(self.text, attr_inactive, "tabview_active")
        super(TabHandle, self).__init__(self.attr)

    def set_text_attr(self, attr):
        self.text.set_text((attr, self.label))


    def selectable(self):
        return True

    def keypress(self, size, key):

        if key == "enter":
            self.tab_view._set_active_by_tab(self)
        elif key == 'tab':
            self.tab_view.set_active_next()
        elif key == 'shift tab':
            self.tab_view.set_active_prev()
        else:
            return key

    def mouse_event(self, size, event, button, col, row, focus):
        if button == 1:
            if not self.locked:
                tab_width = self._w.pack(size)[0]
                if col <= 2:
                    # close this tab
                    self.tab_view._close_by_tab(self)
                    return
            # make this tab active
            self.tab_view._set_active_by_tab(self)
            #raise AttributeError("b: %s - c: %u, r: %u - ev: %s" % (button, col, row, event))


class TabHeader(urwid.WidgetWrap):

    def __init__(self, attr_inactive={}, attr_active={}, divider = True):

        self.columns = urwid.Columns([], 1)

        contents = [ ('weight', 1, x) for x in [self.columns] ]
        # contents = [ ('pack', self.attr)  ]
        if divider:
            contents += [ ('pack', urwid.Divider('-')) ]
        self.pile = urwid.Pile(contents)
        # self.pile.selectable = lambda: True
        super(TabHeader, self).__init__(self.pile)

    @property
    def contents(self):
        return self.columns.contents

    def set_focus(self, idx):

        self.columns.focus_position = idx

    def options(self, s):
        return self.columns.options(s)


class Tab(object):

    HOTKEYS = dict()

    def __init__(self, label, content, hotkey=None, locked=False):

        self.label = label
        self.content = content
        if hotkey:
            Tab.HOTKEYS["meta %s" %(hotkey)] = self
        else:
            hotkey = "meta %s" %(self.label[0].lower())
            if not hotkey in Tab.HOTKEYS:
                Tab.HOTKEYS[hotkey] = self
            else:
                hotkey = None
        self.hotkey = hotkey
        self.locked = locked

    # yuck
    def __getitem__(self, idx):
        if idx == "0":
            return self.label
        elif idx == 1:
            return self.content



class TabView(urwid.WidgetWrap):

    signals = ["activate"]

    def __init__(self, tabs,
                 attr_inactive={None: "tabview_inactive"},
                 attr_active={None: "tabview_active"},
                 selected = 0, tab_bar_initial_focus = False):
        self.attr_inactive = attr_inactive
        self.attr_active = attr_active
        self._contents = []
        self.tab_bar = TabHeader(attr_inactive, attr_active)
        self.body = urwid.AttrMap(urwid.SolidFill(' '), attr_active)
        display_widget = urwid.Pile(
            ( ('pack', self.tab_bar), ('weight', 1, self.body) )
        )
        # display_widget.selectable = lambda: True
        super(TabView, self).__init__(display_widget)

        if not tab_bar_initial_focus:
            display_widget.focus_position = 1

        # now add all the tabs
        for tab in tabs:
            self.add_tab(tab)
        if selected is not None:
            self.set_active_tab(selected)

    @property
    def active_tab(self):
        return self._contents[self.active_tab_idx]

    @classmethod
    def get_palette_entries(cls):
        return {
            "tabview_inactive": PaletteEntry(
                foreground = "light gray",
                background = "black"
            ),
            "tabview_active": PaletteEntry(
                foreground = "white",
                background = "dark blue",
                foreground_high = "white",
                background_high = "#009",
            ),
        }

    def add_tab(self, tab):
        label = tab.label
        content = tab.content
        hokey = tab.hotkey
        locked = tab.locked

        self.tab_bar.contents.append(
            (
                TabHandle(
                    self,
                    label,
                    locked,
                    attr_active = self.attr_active,
                    attr_inactive = self.attr_inactive,

                ),
                self.tab_bar.options('pack')
            )
        )
        self._contents.append(tab)
        self.set_active_tab(len(self._contents)-1)

    def set_active_tab(self, idx):

        if idx < 0 or idx > len(self._contents) - 1:
            return

        self.tab_bar.set_focus(idx)

        for i, tab in enumerate(self.tab_bar.contents):
            if i == idx:
                tab[0].set_text_attr(self.attr_active[None])
            else:
                tab[0].set_text_attr(self.attr_inactive[None])

        self._w.contents[1] = (
            urwid.AttrMap(
                self._contents[idx].content,
                self.attr_inactive
            ),
            self._w.contents[1][1]
        )
        self.active_tab_idx = idx
        urwid.signals.emit_signal(self, "activate", self, self._contents[idx])

    def get_tab_by_label(self, label):

        for tab in self._contents:
            if tab.label == label:
                return tab.content
        return None

    def get_tab_index_by_label(self, label):

        for i, tab in enumerate(self._contents):
            if tab.label == label:
                return i
        return None


    def set_active_next(self):
        if self.active_tab_idx < (len(self._contents)-1):
            self.set_active_tab(self.active_tab_idx+1)
        else:
            self.set_active_tab(0)

    def set_active_prev(self):
        if self.active_tab_idx > 0:
            self.set_active_tab(self.active_tab_idx-1)
        else:
            self.set_active_tab(len(self._contents)-1)

    def close_active_tab(self):
        if not self.tab_bar.contents[self.active_tab_idx][0].locked:
            del self.tab_bar.contents[self.active_tab_idx]
            new_idx = self.active_tab_idx
            if len(self._contents) <= self.active_tab_idx:
                new_idx -= 1
            del self._contents[self.active_tab_idx]
            self.set_active_tab(new_idx)

    def _set_active_by_tab(self, tab):
        for idx, t in enumerate(self.tab_bar.contents):
            if t[0] is tab:
                self.set_active_tab(idx)
                break

    def _close_by_tab(self, tab):
        for idx, t in enumerate(self.tab_bar.contents):
            if t[0] is tab:
                self.set_active_tab(idx)
                self.close_active_tab()
                break

    def keypress(self, size, key):

        if key in Tab.HOTKEYS:
            idx = self.get_tab_index_by_label(Tab.HOTKEYS[key].label)
            self.set_active_tab(idx)
        else:
            return super(TabView, self).keypress(size, key)

__all__ = ["TabView", "Tab"]
