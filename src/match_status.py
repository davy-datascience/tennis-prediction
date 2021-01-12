from enum import Enum

class MatchStatus(Enum):
    FINISHED = 1
    SCHEDULED = 2
    LIVE = 3
    WALKOVER = 4