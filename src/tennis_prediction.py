import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# Read the data
list_datasets = []
for year in range(2000, 2010):
    dataset = pd.read_csv("https://raw.githubusercontent.com/davy-datascience/tennis-prediction/master/datasets/atp_matches_{}.csv".format(year))
    list_datasets.append(dataset)

full_dataset = pd.concat(list_datasets)


features = ["winner_rank_points", "loser_rank_points", "surface"]

dataset = full_dataset[features]

dataset = dataset.rename(columns={'winner_rank_points': 'player_1_points', 'loser_rank_points': 'player_2_points'})
dataset["p1Wins"] = 1

# Separate the dataset into a training set and a test set
train, test = train_test_split(dataset, test_size = 0.2)

def inverseDataset(dataset_input):
    inversed_dataset = pd.DataFrame()
    inversed_dataset["player_1_points"] = dataset_input["player_2_points"]
    inversed_dataset["player_2_points"] = dataset_input["player_1_points"]
    inversed_dataset["surface"] = dataset_input["surface"]
    inversed_dataset["p1Wins"] = 0
    return inversed_dataset

inversed_train = inverseDataset(train)
train = pd.concat([train, inversed_train])
inversed_test = inverseDataset(test)
test = pd.concat([test, inversed_test])


from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

columnTransformer = ColumnTransformer([('encoder', OneHotEncoder(drop="first"), ["surface"])], remainder='passthrough')
#remainder='passthrough' : keep other columns (default:'drop')

dataset = np.array(columnTransformer.fit_transform(dataset))



# Predict the test set with the sklearn algorithm
from sklearn.linear_model import LinearRegression
regressor = LinearRegression()
regressor.fit(X_train, y_train)
y_pred2 = regressor.predict(X_test)
print("MAE for the algorithm of the sklearn module: {}".format(mean_absolute_error(y_pred2, y_test)))







# Ideas : Nationality
#  matchups, "winner_id", "loser_id", 


'''
criteria1 = dataset["winner_id"] == 104755
criteria2 = dataset["loser_id"] == 104755
test = dataset[(criteria1 | criteria2 )]

unique = np.unique(np.concatenate([dataset["winner_id"].unique(), dataset["loser_id"].unique()]))
'''