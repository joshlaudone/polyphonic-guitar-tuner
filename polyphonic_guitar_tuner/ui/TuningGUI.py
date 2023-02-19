from kivymd.app import MDApp
from kivymd.uix.widget import MDWidget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty, BoundedNumericProperty, ColorProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingsWithSidebar
from numpy import linspace

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

        Clock.schedule_interval(self.check_queue, 0.05)
        Window.bind(on_request_close=self.close_app)
    
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "LightBlue"
        self.theme_cls.accent_palette = "Red"
        self.use_kivy_settings = False
        self.settings_cls = SettingsWithSidebar

        built_file = Builder.load_file(kv_file)
        self.tuners = []
        self.tunerScreen = built_file.get_screen("Tuner")
        self.set_tuner_notes()
        self.build_tuner_screen()
        self.resume_tuning()

        return built_file

    def build_tuner_screen(self):
        num_strings = int(self.config.get("Tuner", "num_strings"))

        for tuner in self.tuners:
            self.tunerScreen.remove_widget(tuner)
        self.tuners = []

        tuner_pos_x = linspace(0.15,0.85,num=num_strings)

        for string_num in range(num_strings):
            self.tuners.append(VerticalTuner())
            self.tuners[string_num].pos_hint = {"center_x":float(tuner_pos_x[string_num]), "center_y":0.5}
            self.tuners[string_num].size_hint = 0.09, 0.7
            self.tuners[string_num].cent_difference = 0
            self.tuners[string_num].note_name = ""
            self.tunerScreen.add_widget(self.tuners[string_num])

    def build_config(self, config):
        config.setdefaults('Tuner', {
            'num_strings': '6',
            'tuning': 'Standard',
            'root_note': 'E',
            'root_note_octave': '2',
            'pitch_standard': 440})
        config_file = os.path.join("ui", "tuninggui.ini")
        config.read(config_file)

    def build_settings(self, settings):
        settings.add_json_panel('Tuner',
                                self.config,
                                data=SettingsJson.get_settings())

    def resume_tuning(self):
        message = MessageToTuner(MessageToTunerType.RESUME)
        self.outbound_queue.put(message)

    def on_config_change(self, config, section, key, value):
        print(section, key, value)

        match section:
            case "Tuner":
                self.update_tuner_settings(key, value)
            case _:
                print("no section match found")

    def update_tuner_settings(self, key, value):
        match key:
            case "num_strings" | "tuning" | "root_note" | "root_note_octave" | "pitch_standard":
                self.set_tuner_notes()
                self.build_tuner_screen()
            case _:
                print("no key match found")

    def set_tuner_notes(self):
        a4 = int(self.config.get("Tuner", "pitch_standard"))
        root_note = self.config.get("Tuner", "root_note")
        root_note_octave = int(self.config.get("Tuner", "root_note_octave"))
        tuning = self.config.get("Tuner", "tuning")
        num_strings = int(self.config.get("Tuner", "num_strings"))

        root_note_number = self.calc_note_number(root_note, root_note_octave)
        notes = [root_note_number]
        match tuning:
            case "Standard":
                # All fourths except for second to last string, which is a major third
                for string_num in range(1,num_strings):
                    if string_num != num_strings - 2:
                        notes.append(notes[-1] + 5)
                    else:
                        notes.append(notes[-1] + 4)
            case "Drop":
                # A fifth, then all fourths except for second to last string, which is a major third
                notes.append(notes[-1] + 7)
                for string_num in range(2,num_strings):
                    if string_num != num_strings - 2:
                        notes.append(notes[-1] + 5)
                    else:
                        notes.append(notes[-1] + 4)
            case _:
                print("unrecognized tuning type")
        message = MessageToTuner(MessageToTunerType.SET_NOTES, notes=notes, a4=a4)
        self.outbound_queue.put(message)

    def check_queue(self, dt):
        while self.inbound_queue.qsize() > 0:
            message = self.inbound_queue.get()
            match message.message_type:
                case MessageToGUIType.NOTE_DIFFS:
                    self.note_diffs = message.data
                    self.update_notes()
                case _:
                    print("Invalid Message")

    def update_notes(self):
        for idx, note_diff in enumerate(self.note_diffs):
            self.tuners[idx].cent_difference = round(note_diff[1], 1)
            self.tuners[idx].note_name = self.calc_note_name(note_diff[0])
        
    def calc_note_name(self, note_number: int):
        # notes are relative to middle C
        octave_number = floor(note_number/12) + 4
        if self.use_flats:
            note_name = self.flat_notes[note_number%12]
        else:
            note_name = self.sharp_notes[note_number%12]
        return note_name + str(octave_number)

    def calc_note_number(self, note_name: str, octave_number: int):
        # always use sharps for now because that's what the settings are hardcoded to use
        note_index = self.sharp_notes.index(note_name)
        return note_index + (octave_number-4)*12

    def close_app(self, instance):
        quit_message = MessageToTuner(MessageToTunerType.QUIT)
        self.outbound_queue.put(quit_message)
        self.stop()
        Window.close()