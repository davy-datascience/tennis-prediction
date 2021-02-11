import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import _VectorizerMixin
from sklearn.feature_selection import SelectorMixin
from datetime import datetime

from src.data_collection.data_preparation import inverse_dataset
from src.utils import *


def add_simple_features(matches):
    # matches["p1_games_won"] = add_with_numba(...)
    # matches["p2_games_won"] = add_with_numba(...)
    # TODO CALCULATE GAME WON RATIO

    matches["p1_ace_quotient"] = divide_with_numba(matches["p1_ace"].to_numpy(), matches["p1_svpt"].to_numpy())
    matches["p2_ace_quotient"] = divide_with_numba(matches["p2_ace"].to_numpy(), matches["p2_svpt"].to_numpy())
    matches["p1_df_quotient"] = divide_with_numba(matches["p1_df"].to_numpy(), matches["p1_svpt"].to_numpy())
    matches["p2_df_quotient"] = divide_with_numba(matches["p2_df"].to_numpy(), matches["p2_svpt"].to_numpy())

    # Break points Faced per service-game
    matches["p1_bp_faced_quotient"] = divide_with_numba(matches["p1_bp_faced"].to_numpy(),
                                                        matches["p1_sv_gms"].to_numpy())
    matches["p2_bp_faced_quotient"] = divide_with_numba(matches["p2_bp_faced"].to_numpy(),
                                                        matches["p2_sv_gms"].to_numpy())


def add_elaborated_features(matches):
    pass


def get_player_previous_matches(p_id, match_dt, matches):
    previous_wins = matches[(matches["p1_id"] == p_id) & (matches["datetime"] < match_dt)]
    previous_lost = matches[(matches["p2_id"] == p_id) & (matches["datetime"] < match_dt)]
    previous_matches = pd.concat([previous_wins, inverse_dataset(previous_lost)]).sort_values(
        by=["datetime"])  # .sort_index()
    return previous_matches


def get_time_played_last_x_days(nb_days, match_dt, prev_matches):
    matches_last_x_days = prev_matches[prev_matches["datetime"] > match_dt - pd.to_timedelta(nb_days + 0.5, unit='d')]
    return matches_last_x_days["minutes"].sum()


def get_player_win_ratio(prev_matches, is_all_time):
    player_win_ratio = None
    player_total_played = len(prev_matches.index)
    if player_total_played > 0:
        player_total_wins = len(prev_matches[prev_matches["p1_wins"] == 1].index)
        # If player has only played less than 10 matches in total, and won those matches don't set win ratio to maximum
        if not (is_all_time and (player_total_wins == player_total_played and player_total_played < 10)):
            player_win_ratio = player_total_wins / player_total_played

    return player_win_ratio


def get_player_win_ratio_last_x(nb_matches, prev_matches):
    player_win_ratio_last_x = None
    prev_matches_size = len(prev_matches.index)
    if prev_matches_size > 0:
        player_win_ratio_last_x = get_player_win_ratio(prev_matches[-nb_matches:] if prev_matches_size >= 5
                                                       else prev_matches[-prev_matches_size:], False)
    return player_win_ratio_last_x


def get_player_last_matches(prev_matches, nb_matches=None):
    if nb_matches is None:
        return prev_matches
    else:
        return prev_matches.iloc[-nb_matches:] if len(prev_matches.index) >= nb_matches else prev_matches


def get_player_nb_matches(prev_matches, nb_matches=None):
    matches = get_player_last_matches(prev_matches, nb_matches)
    return len(matches.index)


def get_player_nb_victories(prev_matches, nb_matches=None):
    matches = get_player_last_matches(prev_matches, nb_matches)
    return len(matches[matches["p1_wins"] == 1].index)


def add_features_p1(match, matches):
    previous_p1 = get_player_previous_matches(match["p1_id"], match["datetime"], matches)
    previous_p2 = get_player_previous_matches(match["p2_id"], match["datetime"], matches)

    if len(previous_p1) == 0 or len(previous_p2) == 0:
        '''Set to number of values to unpack'''
        return (None,) * 37

    time_since_last_match_p1 = (match["datetime"] - previous_p1.iloc[-1]["datetime"]).total_seconds() / 60
    time_since_last_match_p2 = (match["datetime"] - previous_p2.iloc[-1]["datetime"]).total_seconds() / 60

    time_played_2_days_p1 = get_time_played_last_x_days(2, match["datetime"], previous_p1)
    time_played_7_days_p1 = get_time_played_last_x_days(7, match["datetime"], previous_p1)
    time_played_14_days_p1 = get_time_played_last_x_days(14, match["datetime"], previous_p1)
    time_played_30_days_p1 = get_time_played_last_x_days(30, match["datetime"], previous_p1)

    time_played_2_days_p2 = get_time_played_last_x_days(2, match["datetime"], previous_p2)
    time_played_7_days_p2 = get_time_played_last_x_days(7, match["datetime"], previous_p2)
    time_played_14_days_p2 = get_time_played_last_x_days(14, match["datetime"], previous_p2)
    time_played_30_days_p2 = get_time_played_last_x_days(30, match["datetime"], previous_p2)

    h2h = previous_p1[previous_p1["p2_id"] == match["p2_id"]]

    h2h_p1_wins = get_player_nb_victories(h2h)
    h2h_p2_wins = get_player_nb_matches(h2h) - h2h_p1_wins
    h2h_diff = h2h_p1_wins - h2h_p2_wins

    h2h_last3_p1_wins = get_player_nb_victories(h2h, 3)    
    h2h_last3_p2_wins = get_player_nb_matches(h2h, 3) - h2h_last3_p1_wins
    h2h_last3_diff = h2h_last3_p1_wins - h2h_last3_p2_wins

    h2h_last7_p1_wins = get_player_nb_victories(h2h, 7)
    h2h_last7_p2_wins = get_player_nb_matches(h2h, 7) - h2h_last3_p1_wins
    h2h_last7_diff = h2h_last7_p1_wins - h2h_last7_p2_wins

    p1_win_ratio = get_player_win_ratio(previous_p1, True)
    p2_win_ratio = get_player_win_ratio(previous_p2, True)

    p1_win_ratio_last5 = get_player_win_ratio_last_x(5, previous_p1)
    p1_win_ratio_last20 = get_player_win_ratio_last_x(20, previous_p1)

    p2_win_ratio_last5 = get_player_win_ratio_last_x(5, previous_p2)
    p2_win_ratio_last20 = get_player_win_ratio_last_x(20, previous_p2)

    p1_played_total = get_player_nb_matches(previous_p1)
    p1_played_last5 = get_player_nb_matches(previous_p1, 5)
    p1_played_last20 = get_player_nb_matches(previous_p1, 20)
    
    p1_victories_total = get_player_nb_victories(previous_p1)
    p1_victories_last5 = get_player_nb_victories(previous_p1, 5)
    p1_victories_last20 = get_player_nb_victories(previous_p1, 20)

    p2_played_total = get_player_nb_matches(previous_p2)
    p2_played_last5 = get_player_nb_matches(previous_p2, 5)
    p2_played_last20 = get_player_nb_matches(previous_p2, 20)

    p2_victories_total = get_player_nb_victories(previous_p2)
    p2_victories_last5 = get_player_nb_victories(previous_p2, 5)
    p2_victories_last20 = get_player_nb_victories(previous_p2, 20)

    return (
        time_since_last_match_p1, time_since_last_match_p2, time_played_2_days_p1, time_played_7_days_p1,
        time_played_14_days_p1, time_played_30_days_p1, time_played_2_days_p2, time_played_7_days_p2,
        time_played_14_days_p2, time_played_30_days_p2, h2h_p1_wins, h2h_last3_p1_wins, h2h_last7_p1_wins, h2h_p2_wins,
        h2h_last3_p2_wins, h2h_last7_p2_wins, h2h_diff, h2h_last3_diff, h2h_last7_diff, p1_played_total,
        p1_played_last5, p1_played_last20, p1_victories_total, p1_victories_last5, p1_victories_last20, p2_played_total,
        p2_played_last5, p2_played_last20, p2_victories_total, p2_victories_last5, p2_victories_last20, p1_win_ratio,
        p2_win_ratio, p1_win_ratio_last5, p1_win_ratio_last20, p2_win_ratio_last5, p2_win_ratio_last20
    )


'''CAREFULL CHECK NB VALUES TO UNPACK IN add_features_p1 '''
def add_features(scheduled_matches, past_matches):
    features = pd.DataFrame()
    (
        features["time_since_last_match_p1"], features["time_since_last_match_p2"], features["time_played_2_days_p1"],
        features["time_played_7_days_p1"], features["time_played_14_days_p1"], features["time_played_30_days_p1"],
        features["time_played_2_days_p2"], features["time_played_7_days_p2"], features["time_played_14_days_p2"],
        features["time_played_30_days_p2"], features["h2h_p1_wins"], features["h2h_last3_p1_wins"],
        features["h2h_last7_p1_wins"], features["h2h_p2_wins"], features["h2h_last3_p2_wins"],
        features["h2h_last7_p2_wins"], features["h2h_diff"], features["h2h_last3_diff"], features["h2h_last7_diff"], features["p1_played_total"], features["p1_played_last5"],
        features["p1_played_last20"], features["p1_victories_total"], features["p1_victories_last5"],
        features["p1_victories_last20"], features["p2_played_total"], features["p2_played_last5"],
        features["p2_played_last20"], features["p2_victories_total"], features["p2_victories_last5"],
        features["p2_victories_last20"], features["p1_win_ratio"],
        features["p2_win_ratio"], features["p1_win_ratio_last5"], features["p1_win_ratio_last20"],
        features["p2_win_ratio_last5"], features["p2_win_ratio_last20"]

    ) = zip(*scheduled_matches[["datetime", "p1_id", "p2_id"]]
            .apply(add_features_p1, args=(past_matches,), axis=1))

    features["p1_is_home"] = scheduled_matches.apply(lambda match: match["p1_birth_country"] == match["country"],
                                                     axis=1)
    features["p2_is_home"] = scheduled_matches.apply(lambda match: match["p2_birth_country"] == match["country"],
                                                     axis=1)

    return features


def get_categorical_cols():
    return ["surface", "tourney_level", "best_of", "round", "p1_hand", "p1_backhand", "p2_hand", "p2_backhand",
            "p1_is_home", "p2_is_home"]


def get_numerical_cols():
    return ["p1_ht", "p1_age", "p1_rank", "p2_ht", "p2_age", "p2_rank", "time_since_last_match_p1",
            "time_since_last_match_p2", "time_played_2_days_p1", "time_played_7_days_p1", "time_played_14_days_p1",
            "time_played_30_days_p1", "time_played_2_days_p2", "time_played_7_days_p2", "time_played_14_days_p2",
            "time_played_30_days_p2", "h2h_diff", "h2h_last3_diff", "h2h_last7_diff", "p1_win_ratio", "p2_win_ratio",
            "p1_win_ratio_last5", "p1_win_ratio_last20", "p2_win_ratio_last5", "p2_win_ratio_last20"]


def get_feature_out(estimator, feature_in):
    if hasattr(estimator, 'get_feature_names'):
        if isinstance(estimator, _VectorizerMixin):
            # handling all vectorizers
            return [f'vec_{f}' \
                    for f in estimator.get_feature_names()]
        else:
            return estimator.get_feature_names(feature_in)
    elif isinstance(estimator, SelectorMixin):
        return np.array(feature_in)[estimator.get_support()]
    else:
        return feature_in


def get_ct_feature_names(ct):
    # handles all estimators, pipelines inside ColumnTransfomer
    # doesn't work when remainder =='passthrough'
    # which requires the input column names.
    output_features = []

    for name, estimator, features in ct.transformers_:
        if name != 'remainder':
            if isinstance(estimator, Pipeline):
                current_features = features
                for step in estimator:
                    current_features = get_feature_out(step, current_features)
                features_out = current_features
            else:
                features_out = get_feature_out(estimator, features)
            output_features.extend(features_out)
        elif estimator == 'passthrough':
            output_features.extend(ct._feature_names_in[features])

    return output_features
