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

    # Add created datetime
    tournaments["created"] = datetime.utcnow()

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


def q_update_tournament(tournament_dict):
    collection = get_tournament_collection()

    _id = tournament_dict["_id"]
    tournament_dict.pop("_id")

    # Add updated datetime
    tournament_dict["updated"] = datetime.utcnow()

    collection.find_one_and_update(
        {"_id": ObjectId(_id)},
        {"$set": tournament_dict}
    )


def q_create_tournament(tournament):
    collection = get_tournament_collection()

    # Add created datetime
    tournament["created"] = datetime.utcnow()

    result = collection.insert_one(tournament)

    return result.acknowledged
