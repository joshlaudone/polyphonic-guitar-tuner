import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.settings import SettingsWithSidebar

from settings_io.SettingsJson import settings_json

class TunerWindow(Screen):
    pass

class SettingsWindow(Screen):
    pass

class WindowManager(ScreenManager):
    pass

kv = Builder.load_file("Tuner.kv")

class TuningGUI(App):
    def build(self):
        self.use_kivy_settings = False
        self.settings_cls = SettingsWithSidebar
        return kv

    def build_config(self, config):
        config.setdefaults('Tuning Settings', {
            'num_strings': 7,
            'tuning': 'Drop',
            'root_note': 'A',
            'root_note_octave': '1',
            'pitch_standard': 440})

    def build_settings(self, settings):
        settings.add_json_panel('Tuning Settings',
                                self.config,
                                data=settings_json)

    def on_config_change(self, config, section, key, value):
        print(section, key, value)

if __name__ == "__main__":
    gui = TuningGUI()
    gui.run()