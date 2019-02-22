import urwid

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
        if key in [ "esc", "q" ]:
            self.parent.close_popup()
        else:
            return super(PopUpOverlay, self).keypress(size, key)

class BasePopUp(urwid.WidgetWrap):

    signals = ["close_popup"]

    def selectable(self):
        return True

class BaseDialog(BasePopUp):

    choices = []
    signals = ["select"]

    def __init__(self, parent, prompt=None):
        self.parent = parent
        if prompt: self.prompt = prompt
        self.text = urwid.Text(
            self.prompt + "[%s]" %("".join(list(self.choices.keys()))), align="center"
        )
        super(BaseDialog, self).__init__(
            urwid.Filler(urwid.Padding(self.text))
        )

    # def selectable(self):
    #     return True

    def keypress(self, size, key):
        if key in list(self.choices.keys()):
            self.choices[key]()
        else:
            return key

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
    "BaseDialog",
]
