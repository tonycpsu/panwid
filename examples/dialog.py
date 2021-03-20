import urwid
from panwid.dialog import *

class QuitDialog(BaseDialog):

    signals = ["message"]

    prompt = "Test Popup"

    def __init__(self, *args, **kwargs):

        def test(n):
            self._emit("message", n)
            self.parent.close_popup()

        self.choices = {
            '1': lambda: test(1),
            '2': lambda: test(2),
            '3': lambda: test(3),
        }
        super(QuitDialog, self).__init__(*args, **kwargs)

class MainView(BaseView):

    def __init__(self):

        self.title = urwid.Text("Press 'o' to open popup.")
        self.text = urwid.Text("")
        self.pile = urwid.Pile([
            ('pack', self.title),
            ('weight', 1, urwid.Filler(self.text))
        ])
        super(MainView, self).__init__(self.pile)

    def selectable(self):
        return True

    def open_popup_dialog(self):
        dialog = QuitDialog(self)
        urwid.connect_signal(dialog, "message", self.on_message)
        self.open_popup(dialog, width=20, height=10)

    def on_message(self, source, n):
        self.text.set_text("You chose %d" %(n))

    def keypress(self, size, key):
        if key == "o":
            self.open_popup_dialog()

        return super(MainView, self).keypress(size, key)

def main():

    main_view = MainView()

    def global_input(key):
        if key in ["q", "Q"]:
            raise urwid.ExitMainLoop()
        return

    screen = urwid.raw_display.Screen()
    screen.set_terminal_properties(16)

    loop = urwid.MainLoop(
        main_view,
        screen=screen,
        pop_ups=True,
        unhandled_input=global_input
    )
    loop.run()

if __name__ == "__main__":
    main()
