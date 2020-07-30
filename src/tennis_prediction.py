import pandas as pd
import numpy as np
from data_preparation import inverseHalfDataset, inverseDataset, renameColumnNames, extractGames, divideWithNumba, getBpSavedRatio, getPreviousResults
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

# Read the data
list_datasets = []
for year in range(2018, 2021):
    dataset = pd.read_csv("https://raw.githubusercontent.com/davy-datascience/tennis-prediction/master/datasets/atp_matches_{}.csv".format(year))
    list_datasets.append(dataset)

dataset = pd.concat(list_datasets)
dataset.reset_index(drop=True, inplace=True)

dataset.drop(columns=["winner_seed", "winner_entry", "loser_seed", "loser_entry"], inplace=True)

#drop rows with null value
dataset.dropna(inplace=True)


dataset = renameColumnNames(dataset)

dataset["p1_wins"] = True

games = extractGames(dataset['score'])
dataset["p1_games_won"] = [game[0] for game in games]
dataset["p2_games_won"] = [game[1] for game in games]
# TODO CALCULATE GAME WON RATIO

dataset.drop(dataset[(dataset["p1_svpt"] == 0) | (dataset["p2_svpt"] == 0)].index, inplace=True) 

dataset["p1_ace_ratio"] = divideWithNumba(dataset["p1_ace"].to_numpy(), dataset["p1_svpt"].to_numpy())
dataset["p2_ace_ratio"] = divideWithNumba(dataset["p2_ace"].to_numpy(), dataset["p2_svpt"].to_numpy())
dataset["p1_df_ratio"] = divideWithNumba(dataset["p1_df"].to_numpy(), dataset["p1_svpt"].to_numpy())
dataset["p2_df_ratio"] = divideWithNumba(dataset["p2_df"].to_numpy(), dataset["p2_svpt"].to_numpy())
dataset["p1_1stIn_ratio"] = divideWithNumba(dataset["p1_1stIn"].to_numpy(), dataset["p1_svpt"].to_numpy())
dataset["p2_1stIn_ratio"] = divideWithNumba(dataset["p2_1stIn"].to_numpy(), dataset["p2_svpt"].to_numpy())
dataset["p1_1stWon_ratio"] = divideWithNumba(dataset["p1_1stWon"].to_numpy(), dataset["p1_svpt"].to_numpy())
dataset["p2_1stWon_ratio"] = divideWithNumba(dataset["p2_1stWon"].to_numpy(), dataset["p2_svpt"].to_numpy())
dataset["p1_2ndWon_ratio"] = divideWithNumba(dataset["p1_2ndWon"].to_numpy(), dataset["p1_svpt"].to_numpy())
dataset["p2_2ndWon_ratio"] = divideWithNumba(dataset["p2_2ndWon"].to_numpy(), dataset["p2_svpt"].to_numpy())

dataset["p1_bpFaced_ratio"] = divideWithNumba(dataset["p1_bpFaced"].to_numpy(), dataset["p1_svpt"].to_numpy()) # Break points Faced per return-game
dataset["p2_bpFaced_ratio"] = divideWithNumba(dataset["p2_bpFaced"].to_numpy(), dataset["p2_svpt"].to_numpy()) # Break points Faced per return-game
dataset["p1_bpSaved_ratio"] = [getBpSavedRatio(row[0], row[1]) for row in dataset[["p1_bpSaved", "p1_bpFaced"]].to_numpy()]       
dataset["p2_bpSaved_ratio"] = [getBpSavedRatio(row[0], row[1]) for row in dataset[["p2_bpSaved", "p2_bpFaced"]].to_numpy()]       
dataset['tourney_date'] = pd.to_datetime(dataset['tourney_date'], format="%Y%m%d")    


player_ids = np.unique(np.concatenate([dataset["p1_id"].unique(), dataset["p2_id"].unique()]))


import time

start_time = time.time()
player_results = {}

for pid in player_ids:
    '''idx = np.where((dataset["p1_id"] == pid) | (dataset["p2_id"] == pid))
    all_matchs = dataset.iloc[idx[0]]'''
    all_matchs = dataset.loc[(dataset["p1_id"] == pid) | (dataset["p2_id"] == pid)]
    all_wins = all_matchs[all_matchs["p1_id"] == pid]
    all_lost = all_matchs[all_matchs["p2_id"] == pid]
    
    player_results[pid]= pd.concat([all_wins, inverseDataset(all_lost)]).sort_index()

print("--- %s seconds ---" % (time.time() - start_time))


start_time = time.time()
results = [getPreviousResults(player_results, index, ids[0], ids[1]) for index, ids in dataset[["p1_id", "p2_id"]].iterrows()]
print("--- %s seconds ---" % (time.time() - start_time))

dataset["p1_ace_ratio_last3"] = [result[0] for result in results]
dataset["p2_ace_ratio_last3"] = [result[1] for result in results]
dataset["p1_df_ratio_last3"] = [result[2] for result in results]
dataset["p2_df_ratio_last3"] = [result[3] for result in results]
dataset["p1_1stIn_ratio_last3"] = [result[4] for result in results]
dataset["p2_1stIn_ratio_last3"] = [result[5] for result in results]
dataset["p1_1stWon_ratio_last3"] = [result[6] for result in results]
dataset["p2_1stWon_ratio_last3"] = [result[7] for result in results]
dataset["p1_2ndWon_ratio_last3"] = [result[8] for result in results]
dataset["p2_2ndWon_ratio_last3"] = [result[9] for result in results]
dataset["p1_bpSaved_ratio_last3"] = [result[10] for result in results]
dataset["p2_bpSaved_ratio_last3"] = [result[11] for result in results]
dataset["p1_bpFaced_ratio_last3"] = [result[12] for result in results]
dataset["p2_bpFaced_ratio_last3"] = [result[13] for result in results]


removed_cols = ["tourney_id", "score", "minutes", "p1_ace", "p1_df", "p1_svpt", "p1_1stIn", "p1_1stWon", "p1_2ndWon", "p1_SvGms",
                "p1_SvGms", "p1_bpSaved", "p1_bpFaced", "p2_ace", "p2_df", "p2_svpt", "p2_1stIn", "p2_1stWon", "p2_2ndWon", 
                "p2_SvGms", "p2_SvGms", "p2_bpSaved", "p2_bpFaced", "p1_games_won", "p2_games_won", "p1_ace_ratio", "p1_df_ratio", 
                "p1_1stIn_ratio", "p1_1stWon_ratio", "p1_2ndWon_ratio", "p1_bpSaved_ratio", "p2_ace_ratio", "p2_df_ratio", 
                "p2_1stIn_ratio", "p2_1stWon_ratio", "p2_2ndWon_ratio", "p2_bpSaved_ratio", "p1_bpFaced_ratio", "p2_bpFaced_ratio",
                "match_num", "p1_id", "p2_id", "p1_rank", "p2_rank",
                "tourney_date"]
dataset.drop(columns=removed_cols, inplace=True)

dataset = inverseHalfDataset(dataset)

X = dataset.drop('p1_wins', axis=1)
y = dataset["p1_wins"]

# Separate the dataset into a training set and a test set
X_train, X_test, y_train, y_test= train_test_split(X, y, test_size = 0.2, shuffle=False)


# Select categorical columns with relatively low cardinality (convenient but arbitrary)
categorical_cols = [cname for cname in X_train.columns if
                    X_train[cname].nunique() < 10 and 
                    X_train[cname].dtype == "object"]

# Select numerical columns
numerical_cols = [cname for cname in X_train.columns if 
                X_train[cname].dtype in ['int64', 'float64']]

# Keep selected columns only
my_cols = categorical_cols + numerical_cols
X_train = X_train[my_cols].copy()
X_test = X_test[my_cols].copy()

# Preprocessing for numerical data 
from sklearn.preprocessing import StandardScaler
numerical_transformer = Pipeline(steps=[
    ('simple', SimpleImputer(strategy='mean')), # Fill missing values
    ('normalizer', StandardScaler()), # Normalize data        
])

# Preprocessing for categorical data
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),   #Fill missing values
    ('onehot', OneHotEncoder(handle_unknown='ignore'))      #Create 1 column per value
])

# Bundle preprocessing for numerical and categorical data
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numerical_transformer, numerical_cols),
        ('cat', categorical_transformer, categorical_cols)
    ])

# Define model
my_model = LogisticRegression()

# Bundle preprocessing and modeling code in a pipeline
my_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                      ('model', my_model)
                     ])


# Preprocessing of training data, fit model 
my_pipeline.fit(X_train, y_train)

# Preprocessing of validation data, get predictions
y_pred = my_pipeline.predict(X_test)

accuracy = sum(y_pred == y_test.to_numpy()) / len(y_pred)

print(accuracy)

# Ideas : Nationality
#  matchups, "winner_id", "loser_id", 
