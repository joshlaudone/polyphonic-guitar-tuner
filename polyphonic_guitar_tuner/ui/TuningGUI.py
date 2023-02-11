from kivymd.app import MDApp
from kivymd.uix.widget import MDWidget
from kivy.config import ConfigParser
from kivy.lang import Builder
from kivy.properties import NumericProperty, BoundedNumericProperty, ColorProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingsWithSidebar

import os.path

import settings_io.SettingsJson as SettingsJson

class VerticalTuner(MDWidget):
    circle_radius = NumericProperty(20)
    circle_thickness = NumericProperty(20)
    inner_circle_radius = NumericProperty(16)
    tuner_color = ColorProperty([0.9, 0.9, 0.9, 1])
    cent_difference = BoundedNumericProperty(0, min=-100, max=100, 
                        errorhandler=lambda x: 100 if x > 100 else -100)
    cent_threshold = NumericProperty(5)
    note_name = StringProperty("E2")

class TunerWindow(Screen):
    pass

class WindowManager(ScreenManager):
    pass

kv_file = os.path.join("ui", "Tuner.kv")

class TuningGUI(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "LightBlue"
        self.theme_cls.accent_palette = "Red"
        self.use_kivy_settings = False
        self.settings_cls = SettingsWithSidebar
        return Builder.load_file(kv_file)

    def build_config(self, config):
        config.setdefaults('Tuning Settings', {
            'num_strings': 6,
            'tuning': 'Standard',
            'root_note': 'E',
            'root_note_octave': '2',
            'pitch_standard': 440})
        config_file = os.path.join("ui", "tuninggui.ini")
        config.read(config_file)
        

    def build_settings(self, settings):
        settings.add_json_panel('Tuning Settings',
                                self.config,
                                data=SettingsJson.get_settings())

    def on_config_change(self, config, section, key, value):
        print(section, key, value)