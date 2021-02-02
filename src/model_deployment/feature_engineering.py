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
    matches["p1_bp_faced_quotient"] = divide_with_numba(matches["p1_bp_faced"].to_numpy(), matches["p1_sv_gms"].to_numpy())
    matches["p2_bp_faced_quotient"] = divide_with_numba(matches["p2_bp_faced"].to_numpy(), matches["p2_sv_gms"].to_numpy())


def add_elaborated_features(matches):
    pass


def add_features(match, matches):
    previous_wins_p1 = matches[(matches["p1_id"] == match["p1_id"]) & (matches["datetime"] < match["datetime"])]
    previous_lost_p1 = matches[(matches["p2_id"] == match["p2_id"]) & (matches["datetime"] < match["datetime"])]
    previous_p1 = pd.concat([previous_wins_p1, inverse_dataset(previous_lost_p1)]).sort_index()

    if len(previous_p1.index) > 0:
        time_since_last_match_p1 = (match["datetime"] - previous_p1.iloc[-1]["datetime"]).seconds

        matches_last_14_days = \
            previous_p1[previous_p1["datetime"] > match["datetime"] - pd.to_timedelta(14.5, unit='d')]

        time_played_14_days_p1 = matches_last_14_days["minutes"].sum()

        matches_last_30_days = \
            previous_p1[previous_p1["datetime"] > match["datetime"] - pd.to_timedelta(30.5, unit='d')]

        time_played_30_days_p1 = matches_last_30_days["minutes"].sum()

        return time_since_last_match_p1, time_played_14_days_p1, time_played_30_days_p1

    #add_simple_features(matches)
    #add_elaborated_features(matches)


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