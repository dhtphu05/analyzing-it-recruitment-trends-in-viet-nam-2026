from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def train_model(df: pd.DataFrame) -> dict:
    df = df.dropna(subset=["salary_avg"]).copy()

    feature_columns = [
        column
        for column in ["location", "company_type", "level", "experience_years"]
        if column in df.columns
    ]
    X = df[feature_columns]
    y = df["salary_avg"]

    categorical_cols = [col for col in feature_columns if X[col].dtype == "object"]
    numeric_cols = [col for col in feature_columns if col not in categorical_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            ),
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                numeric_cols,
            ),
        ]
    )

    model = Pipeline(steps=[("preprocessor", preprocessor), ("regressor", LinearRegression())])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    return {
        "mae": float(mean_absolute_error(y_test, predictions)),
        "r2": float(r2_score(y_test, predictions)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train baseline salary regression model.")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    metrics = train_model(df)
    print(metrics)


if __name__ == "__main__":
    main()
