import pandas as pd

from src.utils import get_mongo_client


def record_all_player_ranks(player_ranks):
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    collection = database["player_ranks"]

    # Remove previous ranks
    collection.remove()

    # Insert new ranks
    records = player_ranks.to_dict(orient='records')
    result = collection.insert_many(records)
    return result.acknowledged


def retrieve_all_player_ranks():
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    collection = database["player_ranks"]

    player_ranks = pd.DataFrame(list(collection.find({}, {'_id': False})))
    return player_ranks
