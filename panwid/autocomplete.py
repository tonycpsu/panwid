import logging
logger = logging.getLogger(__name__)
import itertools

import urwid

from .highlightable import HighlightableTextMixin
from .keymap import *
from  urwid_readline import ReadlineEdit

@keymapped()
class AutoCompleteEdit(ReadlineEdit):

    signals = ["select", "close", "complete_next", "complete_prev"]

    KEYMAP = {
        "enter": "confirm",
        "esc": "cancel"
    }

    def clear(self):
        self.set_edit_text("")

    def confirm(self):
        self._emit("select")
        self._emit("close")

    def cancel(self):
        self._emit("close")

    def complete_next(self):
        self._emit("complete_next")

    def complete_prev(self):
        self._emit("complete_prev")

    def keypress(self, size, key):
        return super().keypress(size, key)

@keymapped()
class AutoCompleteBar(urwid.WidgetWrap):

    signals = ["change", "complete_prev", "complete_next", "select", "close"]

    prompt_attr = "dropdown_prompt"

    def __init__(self, prompt_attr=None, complete_fn=None):

        self.prompt_attr = prompt_attr or self.prompt_attr
        self.prompt = urwid.Text((self.prompt_attr, "> "))
        self.text = AutoCompleteEdit("")
        if complete_fn:
            self.text.enable_autocomplete(complete_fn)

        # self.text.selectable = lambda x: False
        self.cols = urwid.Columns([
            (2, self.prompt),
            ("weight", 1, self.text)
        ], dividechars=0)
        self.cols.focus_position = 1
        self.filler = urwid.Filler(self.cols, valign="bottom")
        urwid.connect_signal(self.text, "postchange", self.text_changed)
        urwid.connect_signal(self.text, "complete_prev", lambda source: self._emit("complete_prev"))
        urwid.connect_signal(self.text, "complete_next", lambda source: self._emit("complete_next"))
        urwid.connect_signal(self.text, "select", lambda source: self._emit("select"))
        urwid.connect_signal(self.text, "close", lambda source: self._emit("close"))
        super(AutoCompleteBar, self).__init__(self.filler)

    def set_prompt(self, text):

        self.prompt.set_text((self.prompt_attr, text))

    def set_text(self, text):

        self.text.set_edit_text(text)

    def text_changed(self, source, text):
        self._emit("change", text)

    def confirm(self):
        self._emit("select")
        self._emit("close")

    def cancel(self):
        self._emit("close")

    def __len__(self):
        return len(self.body)

    def keypress(self, size, key):
        return super().keypress(size, key)

@keymapped()
class AutoCompleteMixin(object):

    auto_complete = None
    prompt_attr = "dropdown_prompt"

    def __init__(self, auto_complete, prompt_attr=None, *args, **kwargs):
        super().__init__(self.complete_container, *args, **kwargs)
        if auto_complete is not None: self.auto_complete = auto_complete
        if prompt_attr is not None:
            self.prompt_attr = prompt_attr
        self.auto_complete_bar = None
        self.completing = False
        self.complete_anywhere = False
        self.case_sensitive = False
        self.last_complete_pos = None
        self.complete_string_location = None
        self.last_filter_text = None

        if self.auto_complete:
            self.auto_complete_bar = AutoCompleteBar(
                prompt_attr=self.prompt_attr,
                complete_fn=self.complete_fn
            )

            urwid.connect_signal(
                self.auto_complete_bar, "change",
                lambda source, text: self.complete()
            )
            urwid.connect_signal(
                self.auto_complete_bar, "complete_prev",
                lambda source: self.complete_prev()
            )
            urwid.connect_signal(
                self.auto_complete_bar, "complete_next",
                lambda source: self.complete_next()
            )

            urwid.connect_signal(
                self.auto_complete_bar, "select", self.on_complete_select
            )
            urwid.connect_signal(
                self.auto_complete_bar, "close", self.on_complete_close
            )

    def keypress(self, size, key):
        return super().keypress(size, key)
        # key = super().keypress(size, key)
        # if self.completing and key == "enter":
        #     self.on_complete_select(self)
        # else:
        #     return key

    @property
    def complete_container(self):
        raise NotImplementedError

    @property
    def complete_container_position(self):
        return 1

    @property
    def complete_body_position(self):
        return 0

    @property
    def complete_body(self):
        raise NotImplementedError

    @property
    def complete_items(self):
        raise NotImplementedError

    def complete_fn(self, text, state):
        tmp = [
            c for c in self.complete_items
            if c and text in c
        ] if text else self.complete_items
        try:
            return str(tmp[state])
        except (IndexError, TypeError):
            return None

    def complete_widget_at_pos(self, pos):
        return self.complete_body[pos]

    def complete_set_focus(self, pos):
        self.focus_position = pos

    @keymap_command()
    def complete_prefix(self):
        self.complete_on()

    @keymap_command()
    def complete_substring(self):
        self.complete_on(anywhere=True)

    def complete_prev(self):
        self.complete(step=-1)

    def complete_next(self):
        self.complete(step=1)

    def complete_on(self, anywhere=False, case_sensitive=False):

        if self.completing:
            return
        self.completing = True
        self.show_bar()
        if anywhere:
            self.complete_anywhere = True
        else:
            self.complete_anywhere = False

        if case_sensitive:
            self.case_sensitive = True
        else:
            self.case_sensitive = False

    def complete_compare_substring(self, search, candidate):
        try:
            return candidate.index(search)
        except ValueError:
            return None

    def complete_compare_fn(self, search, candidate):

        if self.case_sensitive:
            f = lambda x: str(x)
        else:
            f = lambda x: str(x.lower())

        if self.complete_anywhere:
            return self.complete_compare_substring(f(search), f(candidate))
        else:
            return 0 if self.complete_compare_substring(f(search), f(candidate))==0 else None
        # return f(candidate)


    @keymap_command()
    def complete_off(self):

        if not self.completing:
            return
        self.filter_text = ""

        self.hide_bar()
        self.completing = False

    @keymap_command
    def complete(self, step=None, no_wrap=False):

        if not self.filter_text:
            return

        # if not step and self.filter_text == self.last_filter_text:
        #     return

        # logger.info(f"complete: {self.filter_text}")

        if self.last_complete_pos:
            widget = self.complete_widget_at_pos(self.last_complete_pos)
            if isinstance(widget, HighlightableTextMixin):
                widget.unhighlight()

        self.initial_pos = self.complete_body.get_focus()[1]
        positions = itertools.cycle(
            self.complete_body.positions(reverse=(step and step < 0))
        )
        pos = next(positions)
        # logger.info(pos.get_value())
        # import ipdb; ipdb.set_trace()
        while pos != self.initial_pos:
            # logger.info(pos.get_value())
            pos = next(positions)
        for i in range(abs(step or 0)):
            # logger.info(pos.get_value())
            pos = next(positions)

        while True:
            widget = self.complete_widget_at_pos(pos)
            complete_index = self.complete_compare_fn(self.filter_text, str(widget))
            if complete_index is not None:
                self.last_complete_pos = pos
                if isinstance(widget, HighlightableTextMixin):
                    widget.highlight(complete_index, complete_index+len(self.filter_text))
                self.complete_set_focus(pos)
                break
            pos = next(positions)
            if pos == self.initial_pos:
                break

        # logger.info("done")
        self.last_filter_text = self.filter_text

    @keymap_command()
    def cancel(self):
        logger.debug("cancel")
        self.complete_container.focus_position = self.selected_button
        self.close()

    def close(self):
        self._emit("close")

    def show_bar(self):
        pos = self.complete_container_pos
        self.complete_container.contents[pos:pos+1] += [(
            self.auto_complete_bar,
            self.complete_container.options("given", 1)
        )]
        # self.box.height -= 1
        self.complete_container.focus_position = pos

    def hide_bar(self):
        pos = self.complete_container_pos
        widget = self.complete_widget_at_pos(self.complete_body.get_focus()[1])
        if isinstance(widget, HighlightableTextMixin):
            widget.unhighlight()
        self.complete_container.focus_position = self.complete_body_position
        del self.complete_container.contents[pos]
        # self.box.height += 1

    @property
    def filter_text(self):
        return self.auto_complete_bar.text.get_text()[0]

    @filter_text.setter
    def filter_text(self, value):
        return self.auto_complete_bar.set_text(value)

    def on_complete_select(self, source):
        widget = self.complete_widget_at_pos(self.complete_body.get_focus()[1])
        self.complete_off()
        self._emit("select", self.last_complete_pos, widget)
        self._emit("close")

    def on_complete_close(self, source):
        self.complete_off()

__all__ = ["AutoCompleteMixin"]
