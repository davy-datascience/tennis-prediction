from json import JSONEncoder
from bson.json_util import loads
from datetime import datetime, date
from dateutil.tz import UTC
import pandas as pd

class Match:
    def __init__(self, abc, cde, gds, qsd):
        self.gds = gds
        self.cde = cde
        self.abc = abc