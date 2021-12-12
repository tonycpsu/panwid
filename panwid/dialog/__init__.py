import logging
logger = logging.getLogger(__name__)

import urwid
import asyncio

class PopUpMixin(object):

    def open_popup(self, view, title=None, width=75, height=75):

        urwid.connect_signal(
            view, "close_popup", self.close_popup
        )

        popup = PopUpFrame(self, view, title=title)
        overlay = PopUpOverlay(
            self, popup, view,
            'center', ('relative', width),
            'middle', ('relative', height)
        )
        self._w.original_widget = overlay
        self.popup_visible = True

    def close_popup(self, source):
        self._w.original_widget = self.view
        self.popup_visible = False


class PopUpFrame(urwid.WidgetWrap):

    def __init__(self, parent, body, title = None):

        self.parent = parent
        self.line_box = urwid.LineBox(body)
        super(PopUpFrame, self).__init__(self.line_box)


class PopUpOverlay(urwid.Overlay):

    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        super(PopUpOverlay,self).__init__(*args, **kwargs)

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key in [ "esc", "q" ]:
            self.parent.close_popup()
        else:
            return key

class BasePopUp(urwid.WidgetWrap):

    signals = ["close_popup"]

    def selectable(self):
        return True

class ChoiceDialog(BasePopUp):

    choices = []
    signals = ["select"]

    def __init__(self, parent, prompt=None):
        self.parent = parent
        if prompt: self.prompt = prompt
        self.text = urwid.Text(
            self.prompt + " [%s]" %("".join(list(self.choices.keys()))), align="center"
        )
        super(ChoiceDialog, self).__init__(
            urwid.Filler(urwid.Padding(self.text))
        )

    @property
    def choices(self):
        raise NotImplementedError

    def keypress(self, size, key):
        if key in list(self.choices.keys()):
            self.choices[key]()
            self._emit("select", key)
        else:
            return key


class SquareButton(urwid.Button):

    button_left = urwid.Text("[")
    button_right = urwid.Text("]")

    def pack(self, size, focus=False):
        cols = sum(
            [ w.pack()[0] for w in [
                self.button_left,
                self._label,
                self.button_right
            ]]) + self._w.dividechars*2

        return ( cols, )

class OKCancelDialog(BasePopUp):

    focus = None

    def __init__(self, parent, focus=None, *args, **kwargs):

        self.parent = parent
        if focus is not None:
            self.focus = focus

        self.ok_button = SquareButton(("bold", "OK"))

        urwid.connect_signal(
            self.ok_button, "click",
            lambda s: self.confirm()
        )

        self.cancel_button = SquareButton(("bold", "Cancel"))

        urwid.connect_signal(
            self.cancel_button, "click",
            lambda s: self.cancel()
        )


        self.body = urwid.Pile([])
        for name, widget in self.widgets.items():
            setattr(self, name, widget)
            self.body.contents.append(
                (widget, self.body.options("weight", 1))
            )

        self.pile = urwid.Pile(
            [
                ("pack", self.body),
                ("weight", 1, urwid.Padding(
                    urwid.Columns([
                        ("weight", 1,
                         urwid.Padding(
                             self.ok_button, align="center", width=12)
                         ),
                        ("weight", 1,
                         urwid.Padding(
                             self.cancel_button, align="center", width=12)
                         )
                    ]),
                    align="center"
                )),
            ]
        )
        self.body_position = 0
        if self.title:
            self.pile.contents.insert(
                0,
                (urwid.Filler(
                    urwid.AttrMap(
                        urwid.Padding(
                            urwid.Text(self.title)
                        ),
                        "header"
                    )
                ), self.pile.options("given", 2))
            )
            self.body_position += 1

        self.pile.selectable = lambda: True
        self.pile.focus_position = self.body_position
        if self.focus:
            if self.focus == "ok":
                self.pile.set_focus_path(self.ok_focus_path)
            elif self.focus == "cancel":
                self.pile.set_focus_path(self.cancel_focus_path)
            elif isinstance(self.focus, int):
                return [self.body_position, self.focus]
            else:
                raise NotImplementedError

        super(OKCancelDialog, self).__init__(
            urwid.Filler(self.pile, valign="top")
        )

    @property
    def title(self):
        return None

    @property
    def widgets(self):
        raise RuntimeError("must set widgets property")

    def action(self):
        raise RuntimeError("must override action method")

    @property
    def ok_focus_path(self):
        return [self.body_position+1,0]

    @property
    def cancel_focus_path(self):
        return [self.body_position+1,1]

    @property
    def focus_paths(self):
        return [
            [self.body_position, i]
            for i in range(len(self.body.contents))
        ] + [
            self.ok_focus_path,
            self.cancel_focus_path
        ]

    def cycle_focus(self, step):
        path = self.pile.get_focus_path()[:2]
        logger.info(f"{path}, {self.focus_paths}")
        self.pile.set_focus_path(
            self.focus_paths[
                (self.focus_paths.index(path) + step) % len(self.focus_paths)
            ]
        )

    def confirm(self):
        rv = self.action()
        if asyncio.iscoroutine(rv):
            asyncio.get_event_loop().create_task(rv)

        self.close()

    def cancel(self):
        self.close()

    def close(self):
        self._emit("close_popup")

    def selectable(self):
        return True

    def keypress(self, size, key):
        if key == "meta enter":
            self.confirm()
            return
        key = super().keypress(size, key)
        if key == "enter":
            self.confirm()
            return
        if key in ["tab", "shift tab"]:
            self.cycle_focus(1 if key == "tab" else -1)
        else:
            return key



class ConfirmDialog(ChoiceDialog):

    def __init__(self, parent, *args, **kwargs):
        super(ConfirmDialog, self).__init__(parent, *args, **kwargs)

    def action(self, value):
        raise RuntimeError("must override action method")

    @property
    def prompt(self):
        return "Are you sure?"

    def confirm(self):
        self.action()
        self.close()

    def cancel(self):
        self.close()

    def close(self):
        self.parent.close_popup()

    @property
    def choices(self):
        return {
            "y": self.confirm,
            "n": self.cancel
        }

class BaseView(urwid.WidgetWrap):

    focus_widgets = []
    top_view = None

    def __init__(self, view):

        self.view = view
        self.placeholder = urwid.WidgetPlaceholder(urwid.Filler(urwid.Text("")))
        super(BaseView, self).__init__(self.placeholder)
        self.placeholder.original_widget = self.view

    def open_popup(self, view, title=None, width=("relative", 75), height=("relative", 75)):

        urwid.connect_signal(
            view, "close_popup", self.close_popup
        )

        popup = PopUpFrame(self, view, title=title)
        overlay = PopUpOverlay(
            self, popup, self.view,
            'center', width,
            'middle', height
        )
        self._w.original_widget = overlay
        self.popup_visible = True

    def close_popup(self, source=None):
        self._w.original_widget = self.view
        self.popup_visible = False

__all__ = [
    "BaseView",
    "BasePopUp",
    "ChoiceDialog",
    "SquareButton"
]
