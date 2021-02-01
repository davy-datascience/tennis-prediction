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


def find_player_by_id(player_id):
    collection = get_player_collection()
    player_dict = collection.find_one({"flash_id": player_id})
    return pd.Series(player_dict) if player_dict else None


def q_create_player(player):
    collection = get_player_collection()

    # Insert new player
    player_df = pd.DataFrame(player).T
    player_dict = player_df.to_dict(orient='records')
    result = collection.insert_many(player_dict)
    return result.acknowledged
