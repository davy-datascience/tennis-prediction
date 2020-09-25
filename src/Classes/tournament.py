import json
from json import JSONEncoder

class Tournament:
    def __init__(self, id, name, formatted_name, city, country, surface, number_of_competitors, level):
        self.id = id
        self.name = name
        self.formatted_name = formatted_name
        self.city = city
        self.country = country
        self.surface = surface
        self.number_of_competitors = number_of_competitors
        self.level = level
        
class TournamentEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__
        
def getTournamentsJSON(tournaments):
    return json.loads(TournamentEncoder().encode(tournaments))
