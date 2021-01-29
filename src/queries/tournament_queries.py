import pandas as pd

from src.utils import get_mongo_client


def get_tournament_collection():
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    return database["tournaments"]


def record_tournaments(tournaments):
    collection = get_tournament_collection()

    # Remove previous tournaments
    collection.remove()

    # Insert new tournaments
    records = tournaments.to_dict(orient='records')
    result = collection.insert_many(records)
    return result.acknowledged


def retrieve_tournaments():
    collection = get_tournament_collection()

    tournaments = pd.DataFrame(list(collection.find({}, {'_id': False})))
    return tournaments


def find_tournament_by_name(name):
    collection = get_tournament_collection()
    test = collection.find_one({"flash_name": name})