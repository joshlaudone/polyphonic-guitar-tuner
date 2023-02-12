from ui.TuningGUI import TuningGUI
from tuner.tuner import Tuner

import threading
from queue import Queue
import time # debug, delete later

message_queue = Queue()
tuner = Tuner(message_queue)
gui = TuningGUI(message_queue)

def run_tuner():
    end_flag = False
    while not end_flag:
        print("Tuning thread is running")
        time.sleep(1)
        if message_queue.qsize() == 0:
            print("Queue is empty")
            continue
        message = message_queue.get()
        if message == "end":
            end_flag = True

thread = threading.Thread(target=run_tuner)
thread.start()

gui.run()

print("test")