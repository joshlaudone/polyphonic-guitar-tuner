from enum import Enum
from typing import List

class MessageToTunerType(Enum):
    SET_NOTES = 1
    SET_MONOPHONIC = 2
    SET_POLYPHONIC = 3
    PAUSE = 4
    RESUME = 5
    QUIT = 6
    
class MessageToTuner:
    def __init__(self, message: MessageToTunerType, notes: List[float] = None, a4: int = 440):
        self.message_type = message
        if self.message_type == MessageToTunerType.SET_NOTES:
            self.notes = notes
            self.a4 = a4