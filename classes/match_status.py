from enum import Enum


class MatchStatus(Enum):
    Finished = 1
    Scheduled = 2
    Live = 3
    Retired = 4
    Walkover = 5
    Cancelled = 6
