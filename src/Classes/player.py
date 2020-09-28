import json
from json import JSONEncoder
from bson.json_util import loads
from datetime import datetime, date
from dateutil.tz import UTC
import pandas as pd


class Player:
    def __init__(self, player_id, first_name, last_name, birth_date, turned_pro, weight, height, flag_code, birth_city,
                 birth_country, residence_city, residence_country, handedness, back_hand):
        self.player_id = player_id
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.turned_pro = turned_pro
        self.weight = weight
        self.height = height
        self.flag_code = flag_code
        self.birth_city = birth_city
        self.birth_country = birth_country
        self.residence_city = residence_city
        self.residence_country = residence_country
        self.handedness = handedness
        self.back_hand = back_hand


class PlayerEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            if pd.isna(obj):
                return None
            return {"$date": datetime(int(obj.year), int(obj.month), int(obj.day), tzinfo=UTC).timestamp() * 1000}
        elif isinstance(obj, datetime):
            return {"$date": obj.timestamp() * 1000}
        else:
            return obj.__dict__


def get_players_json(players):
    return loads(PlayerEncoder().encode(players))
