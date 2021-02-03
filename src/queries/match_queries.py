import pandas as pd
import numpy as np

from datetime import datetime
from json import JSONEncoder

from bson import ObjectId
from bson.json_util import loads

from src.utils import get_mongo_client


class MatchEncoder(JSONEncoder):
    def default(self, obj):
        # print(type(obj))
        if pd.isna(obj):
            return None
        elif isinstance(obj, datetime):
            return {"$date": obj.timestamp() * 1000}
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.object):
            return str(obj)
        else:
            return obj.__dict__


def get_matches_json(matches):
    return loads(MatchEncoder().encode(matches.to_dict('records')))


def get_matches_collection():
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    return database["matches"]


def record_matches(matches):
    collection = get_matches_collection()

    # Remove previous matches
    collection.remove()

    # Add created datetime
    matches["created"] = datetime.utcnow()

    # Insert new matches
    matches_json = get_matches_json(matches)
    result = collection.insert_many(matches_json)

    return result.acknowledged


def retrieve_matches():
    collection = get_matches_collection()

    matches = pd.DataFrame(list(collection.find({}, {'_id': False})))

    return matches


def q_find_match_by_id(match_id):
    collection = get_matches_collection()
    match_dict = collection.find_one({"match_id": match_id})
    return pd.Series(match_dict) if match_dict else None


def q_create_match(match):
    collection = get_matches_collection()

    # Add created datetime
    match["created"] = datetime.utcnow()

    result = collection.insert_one(match)

    return result.acknowledged


def q_update_match(match):
    collection = get_matches_collection()

    _id = match["_id"]
    match_dict = match.drop(labels=["_id"]).to_dict()

    print("updating match '{0}'".format(_id))

    # Add updated datetime
    match_dict["updated"] = datetime.utcnow()

    match_json = loads(MatchEncoder().encode(match_dict))

    collection.find_one_and_update(
        {"_id": ObjectId(_id)},
        {"$set": match_json}
    )


def q_delete_match(_id):
    collection = get_matches_collection()

    result = collection.delete_one({"_id": ObjectId(_id)})

    return result.deleted_count == 1
