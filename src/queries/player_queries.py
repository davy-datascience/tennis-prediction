import pandas as pd

from src.utils import get_mongo_client


def get_player_collection():
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    return database["players"]


def record_players(players):
    collection = get_player_collection()

    # Remove previous players
    collection.remove()

    # Insert new players
    records = players.to_dict(orient='records')
    result = collection.insert_many(records)
    return result.acknowledged


def retrieve_players():
    collection = get_player_collection()

    players = pd.DataFrame(list(collection.find({}, {'_id': False})))
    return players
