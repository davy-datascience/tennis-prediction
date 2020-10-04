from json import JSONEncoder
from bson.json_util import loads
from datetime import datetime, date
from dateutil.tz import UTC
import pandas as pd


class Match:
    def __init__(self, p1_atptour_id, p2_atptour_id, p1_flashscore_id, p2_flashscore_id, tournament_atptour_id,
                 tournament_flashscore_id, best_of, m_round, duration, p1_aces, p2_aces, p1_df, p2_df, p1_svpt, p2_svpt,
                 p1_1st_in, p2_1st_in, p1_1st_won, p2_1st_won, p1_2nd_pts, p2_2nd_pts, p1_2nd_won, p2_2nd_won,
                 p1_sv_gms, p2_sv_gms, p1_bp_saved, p2_bp_saved, p1_bp_faced, p2_bp_faced, p1_s1_gms, p2_s1_gms,
                 p1_tb1_score, p2_tb1_score, p1_s2_gms, p2_s2_gms, p1_tb2_score, p2_tb2_score, p1_s3_gms, p2_s3_gms,
                 p1_tb3_score, p2_tb3_score, p1_s4_gms, p2_s4_gms, p1_tb4_score, p2_tb4_score, p1_s5_gms, p2_s5_gms,
                 p1_tb5_score, p2_tb5_score, surrender, year):
        self.p1_atptour_id = p1_atptour_id
        self.p2_atptour_id = p2_atptour_id
        self.p1_flashscore_id = p1_flashscore_id
        self.p2_flashscore_id = p2_flashscore_id
        self.tournament_atptour_id = tournament_atptour_id
        self.tournament_flashscore_id = tournament_flashscore_id
        self.best_of = best_of
        self.m_round = m_round
        self.duration = duration
        self.p1_aces = p1_aces
        self.p2_aces = p2_aces
        self.p1_df = p1_df
        self.p2_df = p2_df
        self.p1_svpt = p1_svpt
        self.p2_svpt = p2_svpt
        self.p1_1st_in = p1_1st_in
        self.p2_1st_in = p2_1st_in
        self.p1_1st_won = p1_1st_won
        self.p2_1st_won = p2_1st_won
        self.p1_2nd_pts = p1_2nd_pts
        self.p2_2nd_pts = p2_2nd_pts
        self.p1_2nd_won = p1_2nd_won
        self.p2_2nd_won = p2_2nd_won
        self.p1_sv_gms = p1_sv_gms
        self.p2_sv_gms = p2_sv_gms
        self.p1_bp_saved = p1_bp_saved
        self.p2_bp_saved = p2_bp_saved
        self.p1_bp_faced = p1_bp_faced
        self.p2_bp_faced = p2_bp_faced
        self.p1_s1_gms = p1_s1_gms
        self.p2_s1_gms = p2_s1_gms
        self.p1_tb1_score = p1_tb1_score
        self.p2_tb1_score = p2_tb1_score
        self.p1_s2_gms = p1_s2_gms
        self.p2_s2_gms = p2_s2_gms
        self.p1_tb2_score = p1_tb2_score
        self.p2_tb2_score = p2_tb2_score
        self.p1_s3_gms = p1_s3_gms
        self.p2_s3_gms = p2_s3_gms
        self.p1_tb3_score = p1_tb3_score
        self.p2_tb3_score = p2_tb3_score
        self.p1_s4_gms = p1_s4_gms
        self.p2_s4_gms = p2_s4_gms
        self.p1_tb4_score = p1_tb4_score
        self.p2_tb4_score = p2_tb4_score
        self.p1_s5_gms = p1_s5_gms
        self.p2_s5_gms = p2_s5_gms
        self.p1_tb5_score = p1_tb5_score
        self.p2_tb5_score = p2_tb5_score
        self.surrender = surrender
        self.year = year


class MatchEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            if pd.isna(obj):
                return None
            return {"$date": datetime(int(obj.year), int(obj.month), int(obj.day), tzinfo=UTC).timestamp() * 1000}
        elif isinstance(obj, datetime):
            return {"$date": obj.timestamp() * 1000}
        else:
            return obj.__dict__


def get_matches_json(matches):
    return loads(MatchEncoder().encode(matches))


def get_match_from_series(match_series):
    p1_id = match_series["p1_id"]
    p2_id = match_series["p2_id"]
    tournament_id = match_series["tournament_id"]
    best_of = match_series["best_of"]
    m_round = match_series["round"]
    duration = match_series["minutes"]
    p1_aces = match_series["p1_ace"]
    p2_aces = match_series["p2_ace"]
    p1_df = match_series["p1_df"]
    p2_df = match_series["p2_df"]
    p1_svpt = match_series["p1_svpt"]
    p2_svpt = match_series["p2_svpt"]
    p1_1st_in = match_series["p1_1stIn"]
    p2_1st_in = match_series["p2_1stIn"]
    p1_1st_won = match_series["p1_1stWon"]
    p2_1st_won = match_series["p2_1stWon"]
    p1_2nd_pts = match_series["p1_2nd_pts"]
    p2_2nd_pts = match_series["p2_2nd_pts"]
    p1_2nd_won = match_series["p1_2ndWon"]
    p2_2nd_won = match_series["p2_2ndWon"]
    p1_sv_gms = match_series["p1_SvGms"]
    p2_sv_gms = match_series["p2_SvGms"]
    p1_bp_saved = match_series["p1_bpSaved"]
    p2_bp_saved = match_series["p2_bpSaved"]
    p1_bp_faced = match_series["p1_bpFaced"]
    p2_bp_faced = match_series["p2_bpFaced"]
    p1_s1_gms = match_series["p1_s1_gms"]
    p2_s1_gms = match_series["p2_s1_gms"]
    p1_tb1_score = match_series["p1_tb1_score"]
    p2_tb1_score = match_series["p2_tb1_score"]
    p1_s2_gms = match_series["p1_s2_gms"]
    p2_s2_gms = match_series["p2_s2_gms"]
    p1_tb2_score = match_series["p1_tb2_score"]
    p2_tb2_score = match_series["p2_tb2_score"]
    p1_s3_gms = match_series["p1_s3_gms"]
    p2_s3_gms = match_series["p2_s3_gms"]
    p1_tb3_score = match_series["p1_tb3_score"]
    p2_tb3_score = match_series["p2_tb3_score"]
    p1_s4_gms = match_series["p1_s4_gms"]
    p2_s4_gms = match_series["p2_s4_gms"]
    p1_tb4_score = match_series["p1_tb4_score"]
    p2_tb4_score = match_series["p2_tb4_score"]
    p1_s5_gms = match_series["p1_s5_gms"]
    p2_s5_gms = match_series["p2_s5_gms"]
    p1_tb5_score = match_series["p1_tb5_score"]
    p2_tb5_score = match_series["p2_tb5_score"]
    surrender = match_series["ret"]
    year = match_series["year"]

    return Match(p1_id, p2_id, tournament_id, best_of, m_round, duration, p1_aces, p2_aces, p1_df, p2_df, p1_svpt, p2_svpt,
                 p1_1st_in, p2_1st_in, p1_1st_won, p2_1st_won, p1_2nd_pts, p2_2nd_pts, p1_2nd_won, p2_2nd_won,
                 p1_sv_gms, p2_sv_gms, p1_bp_saved, p2_bp_saved, p1_bp_faced, p2_bp_faced, p1_s1_gms, p2_s1_gms,
                 p1_tb1_score, p2_tb1_score, p1_s2_gms, p2_s2_gms, p1_tb2_score, p2_tb2_score, p1_s3_gms, p2_s3_gms,
                 p1_tb3_score, p2_tb3_score, p1_s4_gms, p2_s4_gms, p1_tb4_score, p2_tb4_score, p1_s5_gms, p2_s5_gms,
                 p1_tb5_score, p2_tb5_score, surrender, year)
