import pandas as pd

from datetime import datetime
from bson import ObjectId
from utils import get_mongo_client, PandasEncoder, get_dataframe_json
from bson.json_util import loads


def get_matches_collection():
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    return database["matches"]


def get_match_ordered_attributes(matches):

    all_attr = ["_id", "match_id", "datetime", "status", "tournament_id", "p1_id", "p2_id", "round", "minutes",
                "p1_wins", "created", "updated"]

    attributes = []

    for attribute in all_attr:
        if attribute in matches.columns.to_list():
            attributes.append(attribute)

    return attributes


def get_embedded_matches_json(matches):
    matches_copy = matches.copy()

    features_attr = [
        "time_since_last_match_p1", "time_since_last_match_p2", "time_played_2_days_p1", "time_played_7_days_p1",
        "time_played_14_days_p1", "time_played_30_days_p1", "time_played_2_days_p2", "time_played_7_days_p2",
        "time_played_14_days_p2", "time_played_30_days_p2", "h2h_p1_wins", "h2h_last3_p1_wins", "h2h_last7_p1_wins",
        "h2h_p2_wins", "h2h_last3_p2_wins", "h2h_last7_p2_wins", "h2h_diff", "h2h_last3_diff", "h2h_last7_diff",
        "p1_played_total", "p1_played_last5", "p1_played_last20", "p1_victories_total", "p1_victories_last5",
        "p1_victories_last20", "p2_played_total", "p2_played_last5", "p2_played_last20", "p2_victories_total",
        "p2_victories_last5", "p2_victories_last20", "p1_win_ratio", "p2_win_ratio", "p1_win_ratio_last5",
        "p1_win_ratio_last20", "p2_win_ratio_last5", "p2_win_ratio_last20", "p1_is_home", "p2_is_home"
    ]

    score_attr = [
        'p1_s1_gms', 'p2_s1_gms', 'p1_tb1_score', 'p2_tb1_score', 'p1_s2_gms', 'p2_s2_gms', 'p1_tb2_score',
        'p2_tb2_score', 'p1_s3_gms', 'p2_s3_gms', 'p1_tb3_score', 'p2_tb3_score', 'p1_s4_gms', 'p2_s4_gms',
        'p1_tb4_score', 'p2_tb4_score', 'p1_s5_gms', 'p2_s5_gms', 'p1_tb5_score', 'p2_tb5_score'
    ]

    stats_attr = [
        'p1_ace', 'p1_df', 'p1_svpt', 'p1_1st_in',
        'p1_1st_won', 'p1_2nd_won', 'p1_sv_gms', 'p1_bp_saved', 'p1_bp_faced', 'p2_ace', 'p2_df',
        'p2_svpt', 'p2_1st_in', 'p2_1st_won', 'p2_2nd_won', 'p2_sv_gms', 'p2_bp_saved',
        'p2_bp_faced', 'p1_2nd_pts', 'p2_2nd_pts', 'p1_svpt_won', 'p2_svpt_won',
        'p1_1st_serve_ratio', 'p2_1st_serve_ratio',
        'p1_svpt_ratio', 'p2_svpt_ratio', 'p1_1st_won_ratio', 'p2_1st_won_ratio',
        'p1_2nd_won_ratio',
        'p2_2nd_won_ratio', 'p1_sv_gms_won', 'p2_sv_gms_won', 'p1_sv_gms_won_ratio',
        'p2_sv_gms_won_ratio',
        'p1_bp_saved_ratio', 'p2_bp_saved_ratio']

    p1_attr = ['p1_hand', 'p1_backhand', 'p1_ht', 'p1_weight', 'p1_age', 'p1_rank', 'p1_rank_points',
               'p1_birth_country', 'p1_residence_country']

    p2_attr = ['p2_hand', 'p2_backhand', 'p2_ht', 'p2_weight', 'p2_age', 'p2_rank', 'p2_rank_points',
               'p2_birth_country', 'p2_residence_country']

    tour_attr = ["surface", "country", "best_of", "tourney_level", "draw_size", "tour_date"]

    prediction_attr = ["p1_proba", "p2_proba", "model"]

    matches_features = None
    has_features = features_attr[0] in matches.columns
    if has_features:
        matches_features = matches_copy[features_attr].copy()
        matches_copy.drop(columns=features_attr, inplace=True)

    matches_score = None
    has_score = score_attr[0] in matches.columns
    if has_score:
        matches_score = matches_copy[score_attr].copy()
        matches_copy.drop(columns=score_attr, inplace=True)

    matches_stats = None
    has_stats = stats_attr[0] in matches.columns
    if has_stats:
        matches_stats = matches_copy[stats_attr].copy()
        matches_copy.drop(columns=stats_attr, inplace=True)

    matches_p1 = None
    matches_p2 = None
    has_player_info = p1_attr[0] in matches.columns
    if has_player_info:
        matches_p1 = matches_copy[p1_attr]
        matches_copy.drop(columns=p1_attr, inplace=True)

        matches_p2 = matches_copy[p2_attr]
        matches_copy.drop(columns=p2_attr, inplace=True)

    matches_tournament = None
    has_tourn_info = tour_attr[0] in matches.columns
    if has_tourn_info:
        matches_tournament = matches_copy[tour_attr]
        matches_copy.drop(columns=tour_attr, inplace=True)

    matches_prediction = None
    has_pred = prediction_attr[0] in matches.columns
    if has_pred:
        matches_prediction = matches_copy[prediction_attr]
        matches_copy.drop(columns=prediction_attr, inplace=True)

    matches_copy = matches_copy[get_match_ordered_attributes(matches_copy)]

    matches_dict = matches_copy.to_dict('records')
    for i in range(len(matches_copy.index)):
        if has_player_info:
            matches_dict[i]["p1"] = matches_p1.iloc[i:i + 1].to_dict('records')[0]
            matches_dict[i]["p2"] = matches_p2.iloc[i:i + 1].to_dict('records')[0]
        if has_tourn_info:
            matches_dict[i]["tournament"] = matches_tournament.iloc[i:i + 1].to_dict('records')[0]
        if has_score:
            matches_dict[i]["score"] = matches_score.iloc[i:i + 1].to_dict('records')[0]
        if has_stats:
            matches_dict[i]["stats"] = matches_stats.iloc[i:i + 1].to_dict('records')[0]
        if has_features:
            matches_dict[i]["features"] = matches_features.iloc[i:i + 1].to_dict('records')[0]
        if has_pred:
            matches_dict[i]["prediction"] = matches_prediction.iloc[i:i + 1].to_dict('records')[0]

    matches_json = loads(PandasEncoder().encode(matches_dict))

    return matches_json


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
    matches_json = get_dataframe_json(matches)
    result = collection.insert_many(matches_json)

    return result.acknowledged


def normalize_matches(match_list):
    matches = pd.json_normalize(match_list)

    matches.columns = matches.columns.str.replace(r'^p1\.', '', regex=True)
    matches.columns = matches.columns.str.replace(r'^p2\.', '', regex=True)
    matches.columns = matches.columns.str.replace(r'^tournament\.', '', regex=True)
    matches.columns = matches.columns.str.replace(r'^score\.', '', regex=True)
    matches.columns = matches.columns.str.replace(r'^stats\.', '', regex=True)
    matches.columns = matches.columns.str.replace(r'^features\.', '', regex=True)
    matches.columns = matches.columns.str.replace(r'^prediction\.', '', regex=True)

    return matches


def retrieve_matches():
    collection = get_matches_collection()

    match_list = list(collection.find({}))

    return normalize_matches(match_list)


def q_get_past_matches():
    collection = get_matches_collection()

    match_list = list(collection.find({"status": {"$ne": "Scheduled"}}))

    return normalize_matches(match_list)


def q_get_unfeatured_matches():
    collection = get_matches_collection()

    match_list = list(collection.find({"features": {"$exists": False}}))

    return normalize_matches(match_list)


def q_get_unpredicted_matches():
    collection = get_matches_collection()

    match_list = list(collection.find({"status": "Scheduled", "prediction": {"$exists": False}}))

    return normalize_matches(match_list)


def get_matches_from_created_date(from_date):
    collection = get_matches_collection()

    match_list = list(collection.find({"created": {"$gt": from_date}}))

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

    # Add updated datetime
    match_dict["updated"] = datetime.utcnow()

    collection.find_one_and_update(
        {"_id": ObjectId(_id)},
        {"$set": match_dict}
    )


def q_delete_match(_id):
    collection = get_matches_collection()

    result = collection.delete_one({"_id": ObjectId(_id)})

    return result.deleted_count == 1
