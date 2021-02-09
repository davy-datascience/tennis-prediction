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


def get_embedded_matches_json(matches):
    matches_score = matches[
        ['p1_s1_gms', 'p2_s1_gms', 'p1_tb1_score', 'p2_tb1_score', 'p1_s2_gms', 'p2_s2_gms', 'p1_tb2_score',
         'p2_tb2_score', 'p1_s3_gms', 'p2_s3_gms', 'p1_tb3_score', 'p2_tb3_score', 'p1_s4_gms', 'p2_s4_gms',
         'p1_tb4_score', 'p2_tb4_score', 'p1_s5_gms', 'p2_s5_gms', 'p1_tb5_score', 'p2_tb5_score'
         ]].copy()

    matches.drop(
        columns=
        [
            'p1_s1_gms', 'p2_s1_gms', 'p1_tb1_score', 'p2_tb1_score', 'p1_s2_gms', 'p2_s2_gms', 'p1_tb2_score',
            'p2_tb2_score', 'p1_s3_gms', 'p2_s3_gms', 'p1_tb3_score', 'p2_tb3_score', 'p1_s4_gms', 'p2_s4_gms',
            'p1_tb4_score', 'p2_tb4_score', 'p1_s5_gms', 'p2_s5_gms', 'p1_tb5_score', 'p2_tb5_score'
        ],
        inplace=True)

    matches_stats = matches[['p1_ace', 'p1_df', 'p1_svpt', 'p1_1st_in',
                             'p1_1st_won', 'p1_2nd_won', 'p1_sv_gms', 'p1_bp_saved', 'p1_bp_faced', 'p2_ace', 'p2_df',
                             'p2_svpt', 'p2_1st_in', 'p2_1st_won', 'p2_2nd_won', 'p2_sv_gms', 'p2_bp_saved',
                             'p2_bp_faced', 'p1_2nd_pts', 'p2_2nd_pts', 'p1_svpt_won', 'p2_svpt_won',
                             'p1_1st_serve_ratio', 'p2_1st_serve_ratio',
                             'p1_svpt_ratio', 'p2_svpt_ratio', 'p1_1st_won_ratio', 'p2_1st_won_ratio',
                             'p1_2nd_won_ratio',
                             'p2_2nd_won_ratio', 'p1_sv_gms_won', 'p2_sv_gms_won', 'p1_sv_gms_won_ratio',
                             'p2_sv_gms_won_ratio',
                             'p1_bp_saved_ratio', 'p2_bp_saved_ratio']].copy()

    matches.drop(columns=['p1_ace', 'p1_df', 'p1_svpt', 'p1_1st_in',
                          'p1_1st_won', 'p1_2nd_won', 'p1_sv_gms', 'p1_bp_saved', 'p1_bp_faced', 'p2_ace', 'p2_df',
                          'p2_svpt', 'p2_1st_in', 'p2_1st_won', 'p2_2nd_won', 'p2_sv_gms', 'p2_bp_saved',
                          'p2_bp_faced', 'p1_2nd_pts', 'p2_2nd_pts', 'p1_svpt_won', 'p2_svpt_won', 'p1_1st_serve_ratio',
                          'p2_1st_serve_ratio',
                          'p1_svpt_ratio', 'p2_svpt_ratio', 'p1_1st_won_ratio', 'p2_1st_won_ratio', 'p1_2nd_won_ratio',
                          'p2_2nd_won_ratio', 'p1_sv_gms_won', 'p2_sv_gms_won', 'p1_sv_gms_won_ratio',
                          'p2_sv_gms_won_ratio',
                          'p1_bp_saved_ratio', 'p2_bp_saved_ratio'], inplace=True)

    matches_p1 = matches[['p1_hand', 'p1_backhand', 'p1_ht', 'p1_weight', 'p1_age', 'p1_rank', 'p1_rank_points',
                          'p1_birth_country', 'p1_residence_country']]

    matches.drop(columns=['p1_hand', 'p1_backhand', 'p1_ht', 'p1_weight', 'p1_age', 'p1_rank', 'p1_rank_points',
                          'p1_birth_country', 'p1_residence_country'], inplace=True)

    matches_p2 = matches[['p2_hand', 'p2_backhand', 'p2_ht', 'p2_weight', 'p2_age', 'p2_rank', 'p2_rank_points',
                          'p2_birth_country', 'p2_residence_country']]

    matches.drop(columns=['p2_hand', 'p2_backhand', 'p2_ht', 'p2_weight', 'p2_age', 'p2_rank', 'p2_rank_points',
                          'p2_birth_country', 'p2_residence_country'], inplace=True)

    matches["created"] = datetime.utcnow().replace(microsecond=0)
    matches_dict = matches.to_dict('records')
    for i in range(len(matches.index)):
        matches_dict[i]["p1"] = matches_p1.iloc[i:i + 1].to_dict('records')[0]
        matches_dict[i]["p2"] = matches_p2.iloc[i:i + 1].to_dict('records')[0]
        matches_dict[i]["score"] = matches_score.iloc[i:i + 1].to_dict('records')[0]
        matches_dict[i]["stats"] = matches_stats.iloc[i:i + 1].to_dict('records')[0]

    matches_json = loads(MatchEncoder().encode(matches_dict))

    return matches_json


def get_matches_collection():
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    return database["matches"]


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


def retrieve_matches():
    collection = get_matches_collection()

    matches = pd.DataFrame(list(collection.find({}, {'_id': False})))

    return matches


def q_get_finished_matches():
    collection = get_matches_collection()

    match_list = list(collection.find({"status": "Finished"}, {'_id': False}))

    matches = pd.json_normalize(match_list)
    matches.columns = matches.columns.str.replace(r'^features.', '')

    return matches


def q_get_past_matches():
    collection = get_matches_collection()

    match_list = list(collection.find({"status": {"$ne": "Scheduled"}}, {'_id': False}))

    matches = pd.json_normalize(match_list)
    matches.columns = matches.columns.str.replace(r'^features.', '')

    return matches


def q_get_scheduled_matches():
    collection = get_matches_collection()

    matches = pd.DataFrame(list(collection.find({"status": "Scheduled"})))

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
