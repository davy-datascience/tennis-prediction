import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import mean_absolute_error

def inverseHalfDataset(dataset_input):
    '''inverse 50% of the dataset - for option 2'''
    inversed_dataset = pd.DataFrame()
    inversed_dataset["player_1_points"] = np.where(dataset_input.index % 2 == 0, dataset_input["player_1_points"] , dataset_input["player_2_points"])
    inversed_dataset["player_2_points"] = np.where(dataset_input.index % 2 == 0, dataset_input["player_2_points"] , dataset_input["player_1_points"])
    inversed_dataset["player_1_wins"] = np.where(dataset_input.index % 2 == 0, 1, 0)
    return inversed_dataset    

# Read the data
list_datasets = []
for year in range(2010, 2020):
    dataset = pd.read_csv("https://raw.githubusercontent.com/davy-datascience/tennis-prediction/master/datasets/atp_matches_{}.csv".format(year))
    list_datasets.append(dataset)

full_dataset = pd.concat(list_datasets)

features = ["winner_rank_points", "loser_rank_points"]

dataset = full_dataset[features]

#drop rows with null value
dataset = dataset.dropna()

dataset = dataset.rename(columns={'winner_rank_points': 'player_1_points', 'loser_rank_points': 'player_2_points'})
dataset["player_1_wins"] = 1

# Separate the dataset into a training set and a test set
train, test = train_test_split(dataset, test_size = 0.2)
train = inverseHalfDataset(train)

X_train = train[["player_1_points", "player_2_points"]]
y_train = train.player_1_wins
X_test = test[["player_1_points", "player_2_points"]]
y_test = test.player_1_wins


my_model = RandomForestClassifier(n_estimators=100, random_state=0)
my_model.fit(X_train, y_train)

# Predict
y_pred = pd.Series(classifier.predict(X_test), index = y_test.index)
mae = mean_absolute_error(y_pred, y_test)
print("MAE using option 2: {}".format(mae))


# Ideas : Nationality
#  matchups, "winner_id", "loser_id", 


'''
criteria1 = dataset["winner_id"] == 104755
criteria2 = dataset["loser_id"] == 104755
test = dataset[(criteria1 | criteria2 )]

unique = np.unique(np.concatenate([dataset["winner_id"].unique(), dataset["loser_id"].unique()]))
'''

from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

columnTransformer = ColumnTransformer([('encoder', OneHotEncoder(drop="first"), ["surface"])], remainder='passthrough')
#remainder='passthrough' : keep other columns (default:'drop')

dataset = np.array(columnTransformer.fit_transform(dataset))