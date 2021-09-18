import urwid
from panwid.dialog import *

class QuitDialog(ChoiceDialog):

    prompt = "Test Popup"

    @property
    def choices(self):
        return {
            '1': lambda: 1,
            '2': lambda: 2,
            '3': lambda: 3,
        }

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
        urwid.connect_signal(dialog, "select", self.on_select)
        self.open_popup(dialog, width=20, height=10)

    def on_select(self, source, n):
        self.text.set_text("You chose %s" %(n))

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
