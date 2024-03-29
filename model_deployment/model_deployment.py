import configparser
from datetime import datetime, timedelta

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from joblib import dump, load

from log import log_to_file, get_file_log
from managers.match_manager import get_match_dtypes
from queries.match_queries import q_get_past_matches, q_update_match, get_embedded_matches_json, \
    get_matches_collection, get_matches_from_created_date, q_get_unfeatured_matches, q_get_unpredicted_matches
from model_deployment.feature_engineering import get_categorical_cols, get_numerical_cols, add_features

PREDICT_LOGS = get_file_log("predict_matches")


def build_model():
    # past_matches: all previous matches including when one player retired
    past_matches = q_get_past_matches()
    past_matches = past_matches.astype(get_match_dtypes(past_matches))

    # finished_matches: matches that were played entirely
    finished_matches = past_matches[past_matches["status"] == "Finished"].copy()

    # matches = matches.replace({np.nan: None})

    finished_matches = finished_matches[get_categorical_cols() + get_numerical_cols() + ["p1_wins"]]

    X = finished_matches.drop('p1_wins', axis=1)
    y = finished_matches["p1_wins"]

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
        ('imputer', SimpleImputer(missing_values=None, strategy='most_frequent')),  # Fill missing values
        ('onehot', OneHotEncoder(handle_unknown='ignore'))  # Create 1 column per value
    ])

    # Bundle preprocessing for numerical and categorical data
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_cols),
            ('cat', categorical_transformer, categorical_cols)
        ],
        remainder='passthrough')

    # transformed_data = preprocessor.fit_transform(X_train, y_train)
    # test = pd.DataFrame(transformed_data, columns=get_ct_feature_names(preprocessor))

    # Define model
    my_model = RandomForestClassifier(n_estimators=100)

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

    my_pipeline.fit(X, y)

    dump(my_pipeline, filename="tennis_prediction.joblib")


def feature_engineer():
    collection = get_matches_collection()

    if collection.count_documents({"features": {"$exists": False}}) == 0:
        # No new match to build features
        log_to_file("No new match to build features", PREDICT_LOGS)
        return

    unfeatured_matches = q_get_unfeatured_matches()
    unfeatured_matches = unfeatured_matches.astype(get_match_dtypes(unfeatured_matches))

    past_matches = q_get_past_matches()
    past_matches = past_matches.astype(get_match_dtypes(past_matches))

    features = add_features(unfeatured_matches, past_matches)

    matches = pd.concat([unfeatured_matches[["_id"]], features], axis=1)

    matches_json = get_embedded_matches_json(matches)

    for match_json in matches_json:
        q_update_match(match_json)


def get_predictions(scheduled_matches, pipeline):
    config = configparser.ConfigParser()
    config.read("config.ini")
    model = config['model']['version']

    X = scheduled_matches[get_categorical_cols() + get_numerical_cols()]
    scheduled_pred = pipeline.predict_proba(X)
    predictions = pd.DataFrame(scheduled_pred, columns=["p2_proba", "p1_proba"])
    predictions["model"] = model

    return predictions


def build_predictions():
    collection = get_matches_collection()

    if collection.count_documents({"status": "Scheduled", "prediction": {"$exists": False}}) == 0:
        # No new match to predict
        log_to_file("No new match to predict", PREDICT_LOGS)
        return

    my_pipeline = load("tennis_prediction.joblib")

    matches_to_predict = q_get_unpredicted_matches()
    matches_to_predict = matches_to_predict.astype(get_match_dtypes(matches_to_predict))

    predictions = get_predictions(matches_to_predict, my_pipeline)

    matches = pd.concat([matches_to_predict, predictions], axis=1)

    matches_json = get_embedded_matches_json(matches)

    for match_json in matches_json:
        q_update_match(match_json)


def resolve_date():
    from_date = datetime(2021, 8, 15)
    matches = get_matches_from_created_date(from_date)

    matches["datetime"] = matches.apply(lambda match: match["datetime"] - timedelta(hours=2), axis=1)

    matches_json = get_embedded_matches_json(matches)

    for match_json in matches_json:
        q_update_match(match_json)
