from kivymd.app import MDApp
from kivymd.uix.widget import MDWidget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty, BoundedNumericProperty, ColorProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingsWithSidebar

from math import floor
import os.path
from queue import Queue

import settings_io.SettingsJson as SettingsJson
from messaging.MessagesToTuner import MessageToTuner, MessageToTunerType
from messaging.MessagesToGUI import MessageToGUI, MessageToGUIType

class VerticalTuner(MDWidget):
    circle_radius = NumericProperty(20)
    circle_thickness = NumericProperty(20)
    inner_circle_radius = NumericProperty(16)
    tuner_color = ColorProperty([0.9, 0.9, 0.9, 1])
    cent_threshold = NumericProperty(5)
    cent_difference = BoundedNumericProperty(0, min=-50, max=50, 
                        errorhandler=lambda x: 50 if x > 50 else -50)
    note_name = StringProperty("E2")

class TunerWindow(Screen):
    pass

class WindowManager(ScreenManager):
    pass

kv_file = os.path.join("ui", "TuningGUI.kv")

class TuningGUI(MDApp):

    def __init__(self, inbound_queue: Queue, outbound_queue: Queue, **kwargs):
        super().__init__(**kwargs)

        self.outbound_queue = outbound_queue
        self.inbound_queue = inbound_queue

        self.use_flats = False 
        self.note_diffs = []
        self.sharp_notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.flat_notes  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

        Clock.schedule_interval(self.update_tuners, 0.05)
        Window.bind(on_request_close=self.close_app)
    
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

    def update_tuners(self, dt):
        self.check_queue()
#        self.set_cent_diffs()

    def check_queue(self):
        while self.inbound_queue.qsize() > 0:
            message = self.inbound_queue.get()
            match message.message_type:
                case MessageToGUIType.NOTE_DIFFS:
                    self.note_diffs = message.data
                    self.update_notes()
                case _:
                    print("Invalid Message")
        #print(self.note_diffs)

    def update_notes(self):
        if len(self.note_diffs) == 0:
           return 
        note_diff = self.note_diffs[0]
        self.root.current_screen.ids["middleTuner"].cent_difference = round(note_diff[1], 1)
        self.root.current_screen.ids["middleTuner"].note_name = self.calc_note_name(note_diff[0])
        print(note_diff[0])
        
    def calc_note_name(self, note_number: int):
        # notes are relative to middle C
        octave_number = floor(note_number/12) + 4
        if self.use_flats:
            note_name = self.flat_notes[note_number%12]
        else:
            note_name = self.sharp_notes[note_number%12]
        return note_name + str(octave_number)

    def close_app(self, instance):
        quit_message = MessageToTuner(MessageToTunerType.QUIT)
        self.outbound_queue.put(quit_message)
        self.stop()
        Window.close()