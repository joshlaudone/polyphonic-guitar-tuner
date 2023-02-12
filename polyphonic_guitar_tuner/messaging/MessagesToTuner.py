from enum import Enum
from typing import List

class MessageToTunerType(Enum):
    SET_FREQS = 1
    SET_MONOPHONIC = 2
    SET_POLYPHONIC = 3
    PAUSE = 4
    RESUME = 5
    QUIT = 6
    
class MessageToTuner:
    def __init__(self, message: MessageToTunerType, freqs: List[float] = None):
        self.message_type = message
        if self.message_type == MessageToTunerType.SET_FREQS:
            self.data = freqs