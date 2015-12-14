# NOTE: This is a WIP and DOES NOT work yet/is not complete.

import kivy

kivy.require('1.8.0')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.codeinput import CodeInput
from kivy.uix.textinput import TextInput


class TutorialApp(App):
    def build(self):
        self.f = BoxLayout(
            size=(640,480),
            orientation='vertical'
        )
        self.b = Button(
            text="Generate Schedules",
            # font_size=36,
            # size_hint=(.2, .2),
            # pos=(500,100)
            size_hint_y=None,
        )
        self.c = CodeInput(
            # size_hint=(.2, .2),
            size_hint_y=None
        )
        self.b.bind(on_press=self.button_pressed)
        self.f.add_widget(self.c)
        self.f.add_widget(self.b)
        return self.f


    def button_pressed(self, instance):
        self.c.text = "Hello"
        print("{} was pressed.".format(instance.text))
        print(dir(instance))

if __name__ == '__main__':
    TutorialApp().run()
