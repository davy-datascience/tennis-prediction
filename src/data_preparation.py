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

def inverseHalfDataset(dataset):
    '''inverse 50% of the dataset - for option 2'''
    inv = dataset.copy()
    for col in dataset.columns:
        if col.startswith("p1") and col != "p1_wins":
            inv[col] = np.where(dataset.index % 2 == 0, dataset[col] , dataset["p2" + col[2:]])
        elif col.startswith("p2"):
            inv[col] = np.where(dataset.index % 2 == 0, dataset[col] , dataset["p1" + col[2:]])
            
    inv["p1_wins"] = np.where(dataset.index % 2 == 0, 1, 0)
    return inv 

def inverseDataset(dataset):
    '''inverse 50% of the dataset - for option 2'''
    inv = dataset.copy()
    for col in long_col + short_col:
        inv["p1_" + col] = dataset["p2_" + col]
        inv["p2_" + col] = dataset["p1_" + col]
   
    inv["p1_wins"] = ~dataset["p1_wins"]
    return inv       

def renameColumnNames(dataset):
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
        if name!='remainder':
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


def extractGames(scores):
    gamesWon = []
    for score in scores: 
        sets = score.split()
        games5 = [(int(re.search("^([0-7])-([0-7]).*$", s).group(1)), int(re.search("^([0-7])-([0-7]).*$", s).group(2))) for s in sets if re.search("^[0-7]-[0-7].*$", s)]
        gamesWon.append((sum([game[0] for game in games5]), sum([game[1] for game in games5])))
    return gamesWon


@numba.vectorize
def addWithNumba(a, b):
    return a + b

@numba.vectorize
def divideWithNumba(a, b):
    ''' Divide one column by an other column of a dataframe with increased performance thanks to vectorization '''
    return a / b

def getBpSavedRatio(bp_saved, bp_faced):
    ''' Divide break point saved by break point faced, if no break point faced consider as 1: max ratio'''
    return 1 if bp_faced == 0 else (bp_saved/bp_faced)

def getPreviousResults(player_results, index, p1_id, p2_id):
    results_p1 = player_results[p1_id]
    prev_res_p1 = pd.DataFrame([results_p1.loc[i] for i in results_p1.index if i < index])
    
    results_p2 = player_results[p2_id]
    prev_res_p2 = pd.DataFrame([results_p2.loc[i] for i in results_p2.index if i < index])
    
    (
     p1_ace_ratio_last3, p2_ace_ratio_last3, p1_df_ratio_last3, p2_df_ratio_last3, p1_1stIn_ratio_last3, 
     p2_1stIn_ratio_last3, p1_1stWon_ratio_last3, p2_1stWon_ratio_last3, p1_2ndWon_ratio_last3, p2_2ndWon_ratio_last3,
     p1_bpSaved_ratio_last3, p2_bpSaved_ratio_last3, p1_bpFaced_ratio_last3, p2_bpFaced_ratio_last3
     ) = (None, None, None, None, None, None, None, None, None, None, None, None, None, None)
    
    if len(prev_res_p1) > 0 :
        p1_ace_ratio_last3 = prev_res_p1["p1_ace_ratio"].tail(3).mean()
        p1_df_ratio_last3 = prev_res_p1["p1_df_ratio"].tail(3).mean()
        p1_1stIn_ratio_last3 = prev_res_p1["p1_1stIn_ratio"].tail(3).mean()
        p1_1stWon_ratio_last3 = prev_res_p1["p1_1stWon_ratio"].tail(3).mean()
        p1_2ndWon_ratio_last3 = prev_res_p1["p1_2ndWon_ratio"].tail(3).mean()
        p1_bpSaved_ratio_last3 = prev_res_p1["p1_bpSaved_ratio"].tail(3).mean()        
        p1_bpFaced_ratio_last3 = prev_res_p1["p1_bpFaced"].tail(3).mean()  
        
    if len(prev_res_p2) > 0 :
        p2_ace_ratio_last3 = prev_res_p2["p2_ace_ratio"].tail(3).mean()
        p2_df_ratio_last3 = prev_res_p2["p2_df_ratio"].tail(3).mean()
        p2_1stIn_ratio_last3 = prev_res_p2["p2_1stIn_ratio"].tail(3).mean()
        p2_1stWon_ratio_last3 = prev_res_p2["p2_1stWon_ratio"].tail(3).mean()
        p2_2ndWon_ratio_last3 = prev_res_p2["p2_2ndWon_ratio"].tail(3).mean()
        p2_bpSaved_ratio_last3 = prev_res_p2["p2_bpSaved_ratio"].tail(3).mean()
        p2_bpFaced_ratio_last3 = prev_res_p2["p2_bpFaced"].tail(3).mean()  
    
    return (p1_ace_ratio_last3, p2_ace_ratio_last3, p1_df_ratio_last3, p2_df_ratio_last3, 
            p1_1stIn_ratio_last3, p2_1stIn_ratio_last3, p1_1stWon_ratio_last3, p2_1stWon_ratio_last3, 
            p1_2ndWon_ratio_last3, p2_2ndWon_ratio_last3, p1_bpSaved_ratio_last3, p2_bpSaved_ratio_last3,
            p1_bpFaced_ratio_last3, p2_bpFaced_ratio_last3)