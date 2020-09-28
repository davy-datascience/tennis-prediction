from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from src.data_preparation import *
from src.scrap_atptour_tournaments import *
from src.match_player_ids import *

config = configparser.ConfigParser()
config.read("src/config.ini")
MONGO_CLIENT = config['mongo']['client']


# Read the data
list_datasets = []
for year in range(1990, 2021):
    dataset = pd.read_csv("https://raw.githubusercontent.com/davy-datascience/tennis-prediction/master/datasets"
                          "/atp_matches/atp_matches_{}.csv".format(year))
    list_datasets.append(dataset)

dataset = pd.concat(list_datasets)
dataset.reset_index(drop=True, inplace=True)

dataset.drop(columns=["tourney_id", "surface", "draw_size", "tourney_level", "match_num",
                      "winner_seed", "winner_entry", "winner_hand", "winner_ht",
                      "winner_ioc", "winner_age", "winner_rank", "winner_rank_points",
                      "loser_seed", "loser_entry", "loser_hand", "loser_ht", "loser_ioc",
                      "loser_age", "loser_rank", "loser_rank_points"], inplace=True)

# drop rows with null value
dataset.dropna(inplace=True)

# drop Davis Cup
indexes_davis_cup = dataset[dataset["tourney_name"].str.startswith("Davis Cup")].index
dataset.drop(indexes_davis_cup, inplace=True)

extracted_scores = extract_scores(dataset['score'])
dataset["p1_s1_gms"] = extracted_scores["p1_s1_gms"]
dataset["p2_s1_gms"] = extracted_scores["p2_s1_gms"]
dataset["p1_tb1_score"] = extracted_scores["p1_tb1_score"]
dataset["p2_tb1_score"] = extracted_scores["p2_tb1_score"]

dataset["p1_s2_gms"] = extracted_scores["p1_s2_gms"]
dataset["p2_s2_gms"] = extracted_scores["p2_s2_gms"]
dataset["p1_tb2_score"] = extracted_scores["p1_tb2_score"]
dataset["p2_tb2_score"] = extracted_scores["p2_tb2_score"]

dataset["p1_s3_gms"] = extracted_scores["p1_s3_gms"]
dataset["p2_s3_gms"] = extracted_scores["p2_s3_gms"]
dataset["p1_tb3_score"] = extracted_scores["p1_tb3_score"]
dataset["p2_tb3_score"] = extracted_scores["p2_tb3_score"]

dataset["p1_s4_gms"] = extracted_scores["p1_s4_gms"]
dataset["p2_s4_gms"] = extracted_scores["p2_s4_gms"]
dataset["p1_tb4_score"] = extracted_scores["p1_tb4_score"]
dataset["p2_tb4_score"] = extracted_scores["p2_tb4_score"]

dataset["p1_s5_gms"] = extracted_scores["p1_s5_gms"]
dataset["p2_s5_gms"] = extracted_scores["p2_s5_gms"]
dataset["p1_tb5_score"] = extracted_scores["p1_tb5_score"]
dataset["p2_tb5_score"] = extracted_scores["p2_tb5_score"]

dataset["ret"] = extracted_scores["ret"]

# Find players corresponding ids (csv file + scrapping)
dataset["p1_id"], dataset["p2_id"], new_players_to_scrap_ids = \
    get_player_ids(dataset[["winner_id", "winner_name", "loser_id", "loser_name"]])

# Retrieve ids of players that couldn't be found
p1_ids_notFound = dataset[(dataset["p1_id"].str.startswith('NO MATCH'))
                          | (dataset["p1_id"].str.startswith('MULTIPLE MATCH'))]
p2_ids_notFound = dataset[(dataset["p2_id"].str.startswith('NO MATCH'))
                          | (dataset["p2_id"].str.startswith('MULTIPLE MATCH'))]

p_ids_notFound = pd.Series([*p1_ids_notFound["winner_id"], *p2_ids_notFound["loser_id"]]).unique()

dataset["p1_id"], dataset["p2_id"], manual_collect_player_ids = retrieve_missing_ids(dataset)

new_players_to_scrap_ids += manual_collect_player_ids.T.iloc[0].to_list()

players = scrap_players(new_players_to_scrap_ids)

if not (record_players(players)):
    print("Error while saving scrapped players in database")

#

# Find tournaments corresponding ids (csv file + scrapping)
dataset["year"] = [int(str(row)[:4]) for row in dataset["tourney_date"].to_numpy()]
dataset["tournament_id"], new_tournaments_to_scrap = get_tournaments_ids(dataset[["tourney_name", "year"]])
tournament_names_notFound = pd.Series(dataset[dataset["tournament_id"] == -1]["tourney_name"]).unique()

dataset["tournament_id"], manual_collect_tournament_ids = retrieve_missing_tournament_ids(dataset)

new_tournaments_to_scrap += manual_collect_tournament_ids

#

tournaments = scrap_tournaments(new_tournaments_to_scrap)
if not (record_tournaments(tournaments)):
    print("Error while saving scrapped tournaments in database")

# Remove columns useless
dataset.drop(columns=["tourney_name", "winner_id", "winner_name", "loser_id", "loser_name", "score"], inplace=True)

dataset = rename_column_names(dataset)

dataset["p1_wins"] = True

records = json.loads(dataset.T.to_json()).values()
myclient = pymongo.MongoClient(MONGO_CLIENT)
mydb = myclient["tennis"]
mycol = mydb["matches"]
mycol.insert_many(records)


games = extract_games(dataset["score"])

dataset["p1_games_won"] = [game[0] for game in games]
dataset["p2_games_won"] = [game[1] for game in games]
# TODO CALCULATE GAME WON RATIO

dataset.drop(dataset[(dataset["p1_SvGms"] == 0) | (dataset["p2_SvGms"] == 0)].index, inplace=True)

dataset["p1_ace_ratio"] = divide_with_numba(dataset["p1_ace"].to_numpy(), dataset["p1_svpt"].to_numpy())
dataset["p2_ace_ratio"] = divide_with_numba(dataset["p2_ace"].to_numpy(), dataset["p2_svpt"].to_numpy())
dataset["p1_df_ratio"] = divide_with_numba(dataset["p1_df"].to_numpy(), dataset["p1_svpt"].to_numpy())
dataset["p2_df_ratio"] = divide_with_numba(dataset["p2_df"].to_numpy(), dataset["p2_svpt"].to_numpy())
dataset["p1_1stIn_ratio"] = divide_with_numba(dataset["p1_1stIn"].to_numpy(), dataset["p1_svpt"].to_numpy())
dataset["p2_1stIn_ratio"] = divide_with_numba(dataset["p2_1stIn"].to_numpy(), dataset["p2_svpt"].to_numpy())
dataset["p1_1stWon_ratio"] = divide_with_numba(dataset["p1_1stWon"].to_numpy(), dataset["p1_svpt"].to_numpy())
dataset["p2_1stWon_ratio"] = divide_with_numba(dataset["p2_1stWon"].to_numpy(), dataset["p2_svpt"].to_numpy())
dataset["p1_2ndWon_ratio"] = divide_with_numba(dataset["p1_2ndWon"].to_numpy(), dataset["p1_svpt"].to_numpy())
dataset["p2_2ndWon_ratio"] = divide_with_numba(dataset["p2_2ndWon"].to_numpy(), dataset["p2_svpt"].to_numpy())
# Break points Faced per return-game
dataset["p1_bpFaced_ratio"] = divide_with_numba(dataset["p1_bpFaced"].to_numpy(), dataset["p1_SvGms"].to_numpy())
dataset["p2_bpFaced_ratio"] = divide_with_numba(dataset["p2_bpFaced"].to_numpy(), dataset["p2_SvGms"].to_numpy())
dataset["p1_bpSaved_ratio"] = [get_bp_saved_ratio(row[0], row[1]) for row in dataset[["p1_bpSaved", "p1_bpFaced"]].to_numpy()]
dataset["p2_bpSaved_ratio"] = [get_bp_saved_ratio(row[0], row[1]) for row in dataset[["p2_bpSaved", "p2_bpFaced"]].to_numpy()]
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

    player_results[pid]= pd.concat([all_wins, inverse_dataset(all_lost)]).sort_index()

print("--- %s seconds ---" % (time.time() - start_time))


start_time = time.time()
results = [get_previous_results(player_results, index, ids[0], ids[1])
           for index, ids in dataset[["p1_id", "p2_id"]].iterrows()]
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

removed_cols = ["tourney_id", "score", "minutes", "p1_ace", "p1_df", "p1_svpt", "p1_1stIn", "p1_1stWon", "p1_2ndWon",
                "p1_SvGms", "p1_SvGms", "p1_bpSaved", "p1_bpFaced", "p2_ace", "p2_df", "p2_svpt", "p2_1stIn",
                "p2_1stWon", "p2_2ndWon", "p2_SvGms", "p2_SvGms", "p2_bpSaved", "p2_bpFaced", "p1_games_won",
                "p2_games_won", "p1_ace_ratio", "p1_df_ratio", "p1_1stIn_ratio", "p1_1stWon_ratio", "p1_2ndWon_ratio",
                "p1_bpSaved_ratio", "p2_ace_ratio", "p2_df_ratio", "p2_1stIn_ratio", "p2_1stWon_ratio",
                "p2_2ndWon_ratio", "p2_bpSaved_ratio", "p1_bpFaced_ratio", "p2_bpFaced_ratio","match_num", "p1_id",
                "p2_id", "p1_rank", "p2_rank", "tourney_date"]
dataset.drop(columns=removed_cols, inplace=True)

dataset = inverse_half_dataset(dataset)

X = dataset.drop('p1_wins', axis=1)
y = dataset["p1_wins"]

# Separate the dataset into a training set and a test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)


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
    ('imputer', SimpleImputer(strategy='most_frequent')),   # Fill missing values
    ('onehot', OneHotEncoder(handle_unknown='ignore'))      # Create 1 column per value
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


# import joblib
from joblib import dump

# dump the pipeline model
dump(my_pipeline, filename="tennis_prediction.joblib")


# Ideas : Nationality
#  matchups, "winner_id", "loser_id",
