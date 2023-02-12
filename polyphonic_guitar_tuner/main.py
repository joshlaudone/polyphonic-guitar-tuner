from ui.TuningGUI import TuningGUI
from tuner.Tuner import Tuner

import threading
from queue import Queue

message_to_tuner_queue = Queue()
message_to_gui_queue = Queue()
tuner = Tuner(message_to_tuner_queue, message_to_gui_queue)
gui = TuningGUI(message_to_gui_queue, message_to_tuner_queue)

thread = threading.Thread(target=tuner.tune)
thread.start()

gui.run()

print("test")