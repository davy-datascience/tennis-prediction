import json
from json import JSONEncoder


class Tournament:
    def __init__(self, atptour_id, flashscore_id, name, formatted_name, city, country, surface, number_of_competitors,
                 level, is_itf):
        self.atptour_id = atptour_id
        self.flashscore_id = flashscore_id
        self.name = name
        self.formatted_name = formatted_name
        self.city = city
        self.country = country
        self.surface = surface
        self.number_of_competitors = number_of_competitors
        self.level = level
        self.is_itf = is_itf


class TournamentEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def get_tournaments_json(tournaments):
    return json.loads(TournamentEncoder().encode(tournaments))
