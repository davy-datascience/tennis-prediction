from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier

from src.queries.match_queries import retrieve_matches
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

    # add_features(matches)

    # matches = matches.replace({np.nan: None})

    matches_part = matches.iloc[500:505].copy()

    features = pd.DataFrame()

    (
        features["time_since_last_match_p1"], features["time_played_2_days_p1"], features["time_played_7_days_p1"],
        features["time_played_14_days_p1"], features["time_played_30_days_p1"], features["time_played_2_days_p2"],
        features["time_played_7_days_p2"], features["time_played_14_days_p2"], features["time_played_30_days_p2"],
        features["h2h_diff"], features["h2h_last3_diff"], features["p1_win_ratio"], features["p2_win_ratio"],
        features["p1_win_ratio_last5"], features["p1_win_ratio_last20"], features["p2_win_ratio_last5"],
        features["p2_win_ratio_last20"]
    ) = zip(*matches_part.apply(add_features, args=(matches,), axis=1))

    matches = matches[get_categorical_cols() + get_numerical_cols() + ["p1_wins"]]

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

    importances = my_model.feature_importances_

    std = np.std([tree.feature_importances_ for tree in my_model.estimators_],
                 axis=0)
    indices = np.argsort(importances)[::-1]

    # Print the feature ranking
    print("Feature ranking:")

    for f in range(X_test.shape[1]):
        print("%d. feature %d (%f)" % (f + 1, indices[f], importances[indices[f]]))

    test = my_pipeline.named_steps['preprocessor'].transformers_[1][1].named_steps['onehot'] \
        .get_feature_names(categorical_cols)

    # import joblib
    from joblib import dump

    # dump the pipeline model
    dump(my_pipeline, filename="../tennis_prediction.joblib")

    # Ideas : Nationality
    #  matchups, "winner_id", "loser_id",
