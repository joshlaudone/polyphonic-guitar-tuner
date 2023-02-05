import kivy
from kivy.app import App
from kivy.config import ConfigParser
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingsWithSidebar

import os.path

from settings_io.SettingsJson import settings_json

class TunerWindow(Screen):
    pass

class SettingsWindow(Screen):
    pass

class WindowManager(ScreenManager):
    pass

kv_file = os.path.join("ui", "Tuner.kv")
kv = Builder.load_file(kv_file)

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
        config_file = os.path.join("ui", "tuninggui.ini")
        if os.path.isfile(config_file):
            config.read(config_file)

    def build_settings(self, settings):
        settings.add_json_panel('Tuning Settings',
                                self.config,
                                data=settings_json)

    def on_config_change(self, config, section, key, value):
        print(section, key, value)