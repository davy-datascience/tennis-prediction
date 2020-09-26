import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import _VectorizerMixin
from sklearn.feature_selection import SelectorMixin
import re
import numba

# column names from the dataset
long_col = ["id", "name", "hand", "ht", "ioc", "age", "rank", "rank_points"]
short_col = ["ace", "df", "svpt", "1stIn", "1stWon", "2ndWon", "SvGms", "bpSaved", "bpFaced"]


def inverse_half_dataset(dataset):
    """inverse 50% of the dataset - for option 2"""
    inv = dataset.copy()
    for col in dataset.columns:
        if col.startswith("p1") and col != "p1_wins":
            inv[col] = np.where(dataset.index % 2 == 0, dataset[col], dataset["p2" + col[2:]])
        elif col.startswith("p2"):
            inv[col] = np.where(dataset.index % 2 == 0, dataset[col], dataset["p1" + col[2:]])
            
    inv["p1_wins"] = np.where(dataset.index % 2 == 0, 1, 0)
    return inv 


def inverse_dataset(dataset):
    """inverse 50% of the dataset - for option 2"""
    inv = dataset.copy()
    for col in long_col + short_col:
        inv["p1_" + col] = dataset["p2_" + col]
        inv["p2_" + col] = dataset["p1_" + col]
   
    inv["p1_wins"] = ~dataset["p1_wins"]
    return inv       


def rename_column_names(dataset):
    columns = {}
    for col in long_col:
        columns["winner_" + col] = "p1_" + col
        columns["loser_" + col] = "p2_" + col
    
    for col in short_col:
        columns["w_" + col] = "p1_" + col
        columns["l_" + col] = "p2_" + col
        
    dataset.rename(columns=columns, inplace=True)
    return dataset


def get_feature_out(estimator, feature_in):
    if hasattr(estimator,'get_feature_names'):
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
        elif estimator=='passthrough':
            output_features.extend(ct._feature_names_in[features])
                
    return output_features


def extract_games(scores):
    games_won = []
    for score in scores: 
        sets = score.split()
        games5 = [(int(re.search("^([0-7])-([0-7]).*$", s).group(1)), int(re.search("^([0-7])-([0-7]).*$", s).group(2))) for s in sets if re.search("^[0-7]-[0-7].*$", s)]
        games_won.append((sum([game[0] for game in games5]), sum([game[1] for game in games5])))
    return games_won


def extract_scores(scores):
    p1_s1_gms = p1_s2_gms = p1_s3_gms = p1_s4_gms = p1_s5_gms = []
    p1_tb1_score = p1_tb2_score = p1_tb3_score = p1_tb4_score = p1_tb5_score = []
    p2_s1_gms = p2_s2_gms = p2_s3_gms = p2_s4_gms = p2_s5_gms = []
    p2_tb1_score = p2_tb2_score = p2_tb3_score = p2_tb4_score = p2_tb5_score = []
    
    import collections
    scores_dict = collections.defaultdict(list)

    score_detailsss = []
    for score in scores:
        sets = score.split()
        score_details = [extract_game(s) for s in sets]
        
        ret = False
        for set_number in range(1,6):
            if len(score_details) >= set_number:
                info = score_details[set_number-1]
                if info is not None:
                    scores_dict["p1_s{0}_gms".format(set_number)].append(info[0])
                    scores_dict["p1_tb{0}_score".format(set_number)].append(info[2])
                    scores_dict["p2_s{0}_gms".format(set_number)].append(info[1])
                    scores_dict["p2_tb{0}_score".format(set_number)].append(info[3])
                else:
                    scores_dict["p1_s{0}_gms".format(set_number)].append(None)
                    scores_dict["p1_tb{0}_score".format(set_number)].append(None)
                    scores_dict["p2_s{0}_gms".format(set_number)].append(None)
                    scores_dict["p2_tb{0}_score".format(set_number)].append(None)
                    ret = True
            else:
                scores_dict["p1_s{0}_gms".format(set_number)].append(None)
                scores_dict["p1_tb{0}_score".format(set_number)].append(None)
                scores_dict["p2_s{0}_gms".format(set_number)].append(None)
                scores_dict["p2_tb{0}_score".format(set_number)].append(None)
        
        scores_dict["ret"].append(ret)
        
    return scores_dict


def extract_game(s):
    set_regex = re.search("^([0-7])-([0-7])\(*(\d*)\)*$", s)
    if set_regex:
        p1_games = int(set_regex.group(1))
        p2_games = int(set_regex.group(2))
        p1_tb_score = None
        p2_tb_score = None
        if set_regex.group(3) != "":
            if p1_games == 7:
                p2_tb_score = int(set_regex.group(3))
                p1_tb_score = p2_tb_score + 2 if p2_tb_score + 2 >= 7 else 7
            else:
                p1_tb_score = int(set_regex.group(3))
                p2_tb_score = p1_tb_score + 2 if p1_tb_score + 2 >= 7 else 7
        return (int(p1_games), int(p2_games), int(p1_tb_score) if p1_tb_score is not None else None,
                int(p2_tb_score) if p2_tb_score is not None else None)
    else:
        return None


@numba.vectorize
def add_with_numba(a, b):
    return a + b


@numba.vectorize
def divide_with_numba(a, b):
    """ Divide one column by an other column of a dataframe with increased performance thanks to vectorization """
    return a / b


def get_bp_saved_ratio(bp_saved, bp_faced):
    """ Divide break point saved by break point faced, if no break point faced consider as 1: max ratio"""
    return 1 if bp_faced == 0 else (bp_saved/bp_faced)


def get_previous_results(player_results, index, p1_id, p2_id):
    results_p1 = player_results[p1_id]
    prev_res_p1 = pd.DataFrame([results_p1.loc[i] for i in results_p1.index if i < index])
    
    results_p2 = player_results[p2_id]
    prev_res_p2 = pd.DataFrame([results_p2.loc[i] for i in results_p2.index if i < index])
    
    (p1_ace_ratio_last3, p2_ace_ratio_last3, p1_df_ratio_last3, p2_df_ratio_last3, p1_1st_in_ratio_last3,
     p2_1st_in_ratio_last3, p1_1st_won_ratio_last3, p2_1st_won_ratio_last3, p1_2nd_won_ratio_last3,
     p2_2nd_won_ratio_last3, p1_bp_saved_ratio_last3, p2_bp_saved_ratio_last3, p1_bp_faced_ratio_last3,
     p2_bp_faced_ratio_last3) = (None, None, None, None, None, None, None, None, None, None, None, None, None, None)
    
    if len(prev_res_p1) > 0 :
        p1_ace_ratio_last3 = prev_res_p1["p1_ace_ratio"].tail(3).mean()
        p1_df_ratio_last3 = prev_res_p1["p1_df_ratio"].tail(3).mean()
        p1_1st_in_ratio_last3 = prev_res_p1["p1_1stIn_ratio"].tail(3).mean()
        p1_1st_won_ratio_last3 = prev_res_p1["p1_1stWon_ratio"].tail(3).mean()
        p1_2nd_won_ratio_last3 = prev_res_p1["p1_2ndWon_ratio"].tail(3).mean()
        p1_bp_saved_ratio_last3 = prev_res_p1["p1_bpSaved_ratio"].tail(3).mean()
        p1_bp_faced_ratio_last3 = prev_res_p1["p1_bpFaced"].tail(3).mean()
        
    if len(prev_res_p2) > 0 :
        p2_ace_ratio_last3 = prev_res_p2["p2_ace_ratio"].tail(3).mean()
        p2_df_ratio_last3 = prev_res_p2["p2_df_ratio"].tail(3).mean()
        p2_1st_in_ratio_last3 = prev_res_p2["p2_1stIn_ratio"].tail(3).mean()
        p2_1st_won_ratio_last3 = prev_res_p2["p2_1stWon_ratio"].tail(3).mean()
        p2_2nd_won_ratio_last3 = prev_res_p2["p2_2ndWon_ratio"].tail(3).mean()
        p2_bp_saved_ratio_last3 = prev_res_p2["p2_bpSaved_ratio"].tail(3).mean()
        p2_bp_faced_ratio_last3 = prev_res_p2["p2_bpFaced"].tail(3).mean()
    
    return (p1_ace_ratio_last3, p2_ace_ratio_last3, p1_df_ratio_last3, p2_df_ratio_last3, 
            p1_1st_in_ratio_last3, p2_1st_in_ratio_last3, p1_1st_won_ratio_last3, p2_1st_won_ratio_last3,
            p1_2nd_won_ratio_last3, p2_2nd_won_ratio_last3, p1_bp_saved_ratio_last3, p2_bp_saved_ratio_last3,
            p1_bp_faced_ratio_last3, p2_bp_faced_ratio_last3)
