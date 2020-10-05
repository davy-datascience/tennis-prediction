import json
from json import JSONEncoder
from bson.json_util import loads
from datetime import datetime, date
from dateutil.tz import UTC
import pandas as pd


class Player:
    def __init__(self, atptour_id, flashscore_id, flashscore_url, first_name, last_name, birth_date, turned_pro, weight,
                 height, flag_code, birth_city,
                 birth_country, residence_city, residence_country, handedness, back_hand):
        self.atptour_id = atptour_id
        self.flashscore_id = flashscore_id
        self.flashscore_url = flashscore_url
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

    def to_dict(self):
        return {
            "atptour_id": self.atptour_id,
            "last_name": self.last_name
        }


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


def get_player_from_series(player_series):
    atptour_id = player_series["player_id"]
    flashscore_id = player_series["flashscore_id"]
    flashscore_url = player_series["flashscore_url"]
    first_name = player_series["first_name"]
    last_name = player_series["last_name"]
    birth_date = player_series["birth_date"].to_pydatetime()
    turned_pro = player_series["turned_pro"]
    weight = player_series["weight"]
    height = player_series["height"]
    flag_code = player_series["flag_code"]
    birth_city = player_series["birth_city"]
    birth_country = player_series["birth_country"]
    residence_city = player_series["residence_city"]
    residence_country = player_series["residence_country"]
    handedness = player_series["handedness"]
    back_hand = player_series["back_hand"]

    player = Player(atptour_id, flashscore_id, flashscore_url, first_name, last_name, birth_date, turned_pro, weight,
                    height, flag_code, birth_city, birth_country, residence_city, residence_country, handedness,
                    back_hand)

    return player


def format_player(player):
    residence = player["residence"]
    birth_place = player["birthplace"]
    birth_year = player["birth_year"]
    birth_month = player["birth_month"]
    birth_day = player["birth_day"]

    residence_city = residence_country = None
    try:
        residence_splitted = residence.split(", ")
        if len(residence_splitted) > 1:
            residence_city = residence_splitted[0]
            residence_country = residence_splitted[-1]
    except AttributeError:
        pass

    birth_city = birth_country = None
    try:
        birth_place_splitted = birth_place.split(", ")
        if len(birth_place_splitted) > 1:
            birth_city = birth_place_splitted[0]
            birth_country = birth_place_splitted[-1]
    except AttributeError:
        pass

    birth_date = None
    try:
        birth_date = datetime(int(birth_year), int(birth_month), int(birth_day), tzinfo=UTC)
    except ValueError:
        pass

    player["residence_city"] = residence_city
    player["residence_country"] = residence_country
    player["birth_city"] = birth_city
    player["birth_country"] = birth_country
    player["birth_date"] = birth_date
    return player


def get_players_from_csv_dataframe(players_dataframe):
    players_formatted = players_dataframe.apply(lambda row: format_player(row), axis=1)
    players_formatted.drop(columns=["first_initial", "full_name", "player_url", "birthdate", "weight_kg", "height_ft",
                                    "height_inches", "residence", "birthplace", "birth_year", "birth_month",
                                    "birth_day"],
                           inplace=True)
    players = [(Player(row["player_id"], None, None, row["first_name"], row["last_name"],
                       row["birth_date"].to_pydatetime(),
                       row["turned_pro"], row["weight_lbs"], row["height_cm"], row["flag_code"],
                       row["birth_city"], row["birth_country"], row["residence_city"],
                       row["residence_country"],
                       row["handedness"], row["backhand"])) for index, row in players_formatted.iterrows()]

    return players
