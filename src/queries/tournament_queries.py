from datetime import datetime

import pandas as pd
from bson import ObjectId

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
    tournament_dict = collection.find_one({"flash_name": name})
    return pd.Series(tournament_dict) if tournament_dict else None


def find_tournament_by_id(tour_id):
    collection = get_tournament_collection()
    tournament_dict = collection.find_one({"flash_id": tour_id})
    return pd.Series(tournament_dict) if tournament_dict else None


def q_update_tournament(_id, tournament):
    collection = get_tournament_collection()

    # Add updated datetime
    tournament["updated"] = datetime.utcnow()

    collection.find_one_and_update(
        {"_id": ObjectId(_id)},
        {"$set": tournament}
    )


def q_create_tournament(tournament):
    collection = get_tournament_collection()

    # Add created datetime
    tournament["created"] = datetime.utcnow()

    result = collection.insert_one(tournament)

    return result.acknowledged
