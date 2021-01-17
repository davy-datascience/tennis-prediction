import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.managers.match_manager import retrieve_matches
from src.model_deployment.feature_engineering import *
from src.utils import get_mongo_client


def main():
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    collection = database["matches"]

    if collection.count_documents({"prediction": None, "status": "Scheduled"}) == 0:
        # No new match to predict
        return

    matches = retrieve_matches()

    add_features(matches)

    # matches = matches.replace({np.nan: None})

    X = matches.drop('p1_wins', axis=1)
    y = matches["p1_wins"]

    # Separate the dataset into a training set and a test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # Select categorical columns with relatively low cardinality (convenient but arbitrary)
    categorical_cols = get_categorical_cols()

    # Select numerical columns
    numerical_cols = get_numerical_cols()

    # Keep selected columns only
    my_cols = categorical_cols + numerical_cols
    X_train = X_train[my_cols].copy()
    X_test = X_test[my_cols].copy()

    # Preprocessing for numerical data
    from sklearn.preprocessing import StandardScaler
    numerical_transformer = Pipeline(steps=[
        ('simple', SimpleImputer(strategy='mean')),  # Fill missing values
        ('normalizer', StandardScaler()),  # Normalize data
    ])

    # Preprocessing for categorical data
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),  # Fill missing values
        ('onehot', OneHotEncoder(handle_unknown='ignore'))  # Create 1 column per value
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
    dump(my_pipeline, filename="../tennis_prediction.joblib")

    # Ideas : Nationality
    #  matchups, "winner_id", "loser_id",
