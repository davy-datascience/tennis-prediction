import pandas as pd
import numpy as np

from datetime import datetime
from json import JSONEncoder
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
            print("is_np_obj")
            return str(obj)
        else:
            print("is_else")
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

    # Insert new matches
    matches_json = get_matches_json(matches)
    result = collection.insert_many(matches_json)

    return result.acknowledged


def retrieve_matches():
    collection = get_matches_collection()

    matches = pd.DataFrame(list(collection.find({}, {'_id': False})))

    return matches
