from json import JSONEncoder
from bson.json_util import loads
from datetime import datetime, date
from dateutil.tz import UTC
import pandas as pd


class Match:
    def __init__(self, p1_id, p2_id, tournament_id, m_round, length, p1_aces, p2_aces, p1_df, p2_df, p1_svpt, p2_svpt,
                 p1_1st_in, p2_1st_in, p1_1st_won, p2_1st_won, p1_2nd_pts, p2_2nd_pts, p1_2nd_won, p2_2nd_won,
                 p1_sv_gms, p2_sv_gms, p1_bp_saved, p2_bp_saved, p1_bp_faced, p2_bp_faced, p1_s1_gms, p2_s1_gms,
                 p1_tb1_score, p2_tb1_score, p1_s2_gms, p2_s2_gms, p1_tb2_score, p2_tb2_score, p1_s3_gms, p2_s3_gms,
                 p1_tb3_score, p2_tb3_score, p1_s4_gms, p2_s4_gms, p1_tb4_score, p2_tb4_score, p1_s5_gms, p2_s5_gms,
                 p1_tb5_score, p2_tb5_score):
        self.p2_tb5_score = p2_tb5_score
        self.p1_tb5_score = p1_tb5_score
        self.p2_s5_gms = p2_s5_gms
        self.p1_s5_gms = p1_s5_gms
        self.p2_tb4_score = p2_tb4_score
        self.p1_tb4_score = p1_tb4_score
        self.p2_s4_gms = p2_s4_gms
        self.p1_s4_gms = p1_s4_gms
        self.p2_tb3_score = p2_tb3_score
        self.p1_tb3_score = p1_tb3_score
        self.p2_s3_gms = p2_s3_gms
        self.p1_s3_gms = p1_s3_gms
        self.p2_tb2_score = p2_tb2_score
        self.p1_tb2_score = p1_tb2_score
        self.p2_s2_gms = p2_s2_gms
        self.p1_s2_gms = p1_s2_gms
        self.p2_tb1_score = p2_tb1_score
        self.p1_tb1_score = p1_tb1_score
        self.p2_s1_gms = p2_s1_gms
        self.p1_s1_gms = p1_s1_gms
        self.p2_bp_faced = p2_bp_faced
        self.p1_bp_faced = p1_bp_faced
        self.p2_bp_saved = p2_bp_saved
        self.p1_bp_saved = p1_bp_saved
        self.p2_sv_gms = p2_sv_gms
        self.p1_sv_gms = p1_sv_gms
        self.p2_2nd_won = p2_2nd_won
        self.p1_2nd_won = p1_2nd_won
        self.p2_2nd_pts = p2_2nd_pts
        self.p1_2nd_pts = p1_2nd_pts
        self.p2_1st_won = p2_1st_won
        self.p1_1st_won = p1_1st_won
        self.p2_1st_in = p2_1st_in
        self.p1_1st_in = p1_1st_in
        self.p2_svpt = p2_svpt
        self.p1_svpt = p1_svpt
        self.p2_df = p2_df
        self.p1_df = p1_df
        self.p2_aces = p2_aces
        self.p1_aces = p1_aces
        self.length = length
        self.m_round = m_round
        self.tournament_id = tournament_id
        self.p2_id = p2_id
        self.p1_id = p1_id


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
