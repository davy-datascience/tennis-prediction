import pandas as pd

from datetime import datetime
from bson import ObjectId
from src.managers.match_manager import get_matches_json
from src.utils import get_mongo_client


def get_matches_collection():
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    return database["matches"]


@DeprecationWarning
def record_matches(matches):
    collection = get_matches_collection()

    # Remove previous matches
    collection.remove()

    # Add created and updated datetime
    now = datetime.utcnow().replace(microsecond=0)
    matches["created"] = now
    matches["updated"] = now

    # Insert new matches
    matches_json = get_matches_json(matches)
    result = collection.insert_many(matches_json)

    return result.acknowledged


def normalize_matches(match_list):
    matches = pd.json_normalize(match_list)

    '''for embedded in ["p1", "p2", "tournament", "score", "stats", "features", "prediction"]:
        matches.columns = matches.columns.str.replace(rf'^{embedded}\.', '') '''

    matches.columns = matches.columns.str.replace(r'^p1\.', '')
    matches.columns = matches.columns.str.replace(r'^p2\.', '')
    matches.columns = matches.columns.str.replace(r'^tournament\.', '')
    matches.columns = matches.columns.str.replace(r'^score\.', '')
    matches.columns = matches.columns.str.replace(r'^stats\.', '')
    matches.columns = matches.columns.str.replace(r'^features\.', '')
    matches.columns = matches.columns.str.replace(r'^prediction\.', '')

    return matches


def retrieve_matches():
    collection = get_matches_collection()

    match_list = list(collection.find({}))

    return normalize_matches(match_list)


def q_get_past_matches():
    collection = get_matches_collection()

    match_list = list(collection.find({"status": {"$ne": "Scheduled"}}))

    return normalize_matches(match_list)


def q_get_scheduled_matches():
    collection = get_matches_collection()

    match_list = list(collection.find({"status": "Scheduled"}))

    return normalize_matches(match_list)


def q_find_match_by_id(match_id):
    collection = get_matches_collection()
    match_list = list(collection.find({"match_id": match_id}))

    if len(match_list) == 0:
        return None

    test = normalize_matches(match_list)

    return test.iloc[0]


def q_create_match(match_dict):
    collection = get_matches_collection()

    # Add created datetime
    match_dict["created"] = datetime.utcnow()

    result = collection.insert_one(match_dict)

    return result.acknowledged


def q_update_match(match_dict):
    collection = get_matches_collection()

    _id = match_dict["_id"]
    match_dict.pop("_id")

    print("updating match '{0}'".format(_id))

    # Add updated datetime
    match_dict["updated"] = datetime.utcnow()

    collection.find_one_and_update(
        {"_id": ObjectId(_id)},
        {"$set": match_dict}
    )


'''def q_update_match_datetime(match):
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
    )'''


def q_delete_match(_id):
    collection = get_matches_collection()

    result = collection.delete_one({"_id": ObjectId(_id)})

    return result.deleted_count == 1
