import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import _VectorizerMixin
from sklearn.feature_selection import SelectorMixin

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


def add_features(match, matches):
    previous_p1 = get_player_previous_matches(match["p1_id"], match["datetime"], matches)
    previous_p2 = get_player_previous_matches(match["p2_id"], match["datetime"], matches)

    time_since_last_match_p1 = (match["datetime"] - previous_p1.iloc[-1]["datetime"]).seconds

    time_played_2_days_p1 = get_time_played_last_x_days(2, match["datetime"], previous_p1)
    time_played_7_days_p1 = get_time_played_last_x_days(7, match["datetime"], previous_p1)
    time_played_14_days_p1 = get_time_played_last_x_days(14, match["datetime"], previous_p1)
    time_played_30_days_p1 = get_time_played_last_x_days(30, match["datetime"], previous_p1)

    time_played_2_days_p2 = get_time_played_last_x_days(2, match["datetime"], previous_p2)
    time_played_7_days_p2 = get_time_played_last_x_days(7, match["datetime"], previous_p2)
    time_played_14_days_p2 = get_time_played_last_x_days(14, match["datetime"], previous_p2)
    time_played_30_days_p2 = get_time_played_last_x_days(30, match["datetime"], previous_p2)

    h2h = previous_p1[previous_p1["p2_id"] == match["p2_id"]]

    h2h_p1_wins = len(h2h[h2h["p1_wins"] == 1].index)
    h2h_p2_wins = len(h2h.index) - h2h_p1_wins

    h2h_diff = h2h_p1_wins - h2h_p2_wins

    h2h_last3 = None
    if len(h2h.index) >= 3:
        h2h_last3 = h2h.iloc[-3:]
    else:
        h2h_last3 = h2h.iloc[-len(h2h.index):]

    h2h_last3_p1_wins = len(h2h_last3[h2h_last3["p1_wins"] == 1].index)
    h2h_last3_p2_wins = len(h2h_last3.index) - h2h_last3_p1_wins
    h2h_last3_diff = h2h_last3_p1_wins - h2h_last3_p2_wins

    p1_win_ratio = get_player_win_ratio(previous_p1, True)
    p2_win_ratio = get_player_win_ratio(previous_p2, True)

    p1_win_ratio_last5 = get_player_win_ratio_last_x(5, previous_p1)
    p1_win_ratio_last20 = get_player_win_ratio_last_x(20, previous_p1)

    p2_win_ratio_last5 = get_player_win_ratio_last_x(5, previous_p2)
    p2_win_ratio_last20 = get_player_win_ratio_last_x(20, previous_p2)

    return time_since_last_match_p1, time_played_2_days_p1, time_played_7_days_p1, time_played_14_days_p1, \
           time_played_30_days_p1, time_played_2_days_p2, time_played_7_days_p2, time_played_14_days_p2, \
           time_played_30_days_p2, h2h_diff, h2h_last3_diff, p1_win_ratio, p2_win_ratio, p1_win_ratio_last5, \
           p1_win_ratio_last20, p2_win_ratio_last5, p2_win_ratio_last20

    # add_simple_features(matches)
    # add_elaborated_features(matches)


def get_categorical_cols():
    return ["surface", "tourney_level", "best_of", "round", "p1_hand", "p1_backhand", "p2_hand", "p2_backhand",
            "p1_is_home", "p2_is_home"]


def get_numerical_cols():
    return ["p1_ht", "p1_age", "p1_rank", "p2_ht", "p2_age", "p2_rank"]


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
