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


def add_features(matches):
    add_simple_features(matches)
    add_elaborated_features(matches)


def get_categorical_cols():
    return ["surface", "tourney_level", "best_of", "round"] # , "p1_hand", "p1_backhand", "p2_hand", "p2_backhand"


def get_numerical_cols():
    return ["p1_ht", "p1_age", "p1_rank", "p2_ht", "p2_age", "p2_rank"]
