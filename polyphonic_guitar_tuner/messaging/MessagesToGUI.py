from enum import Enum
from typing import List, Tuple

class MessageToGUIType(Enum):
    NOTE_DIFFS = 1
    
class MessageToGUI:
    def __init__(self, message: MessageToGUIType.NOTE_DIFFS, note_info: List[Tuple[int, float]]):
        self.message_type = MessageToGUIType.NOTE_DIFFS
        self.data = note_info