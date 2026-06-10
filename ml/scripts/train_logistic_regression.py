"""Train the baseline tract-level logistic regression model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
except ImportError as exc:
    raise SystemExit(
        "Missing required ML dependency. Install pandas, numpy, scikit-learn, "
        "and joblib in the active environment, then rerun "
        "`python ml/scripts/train_logistic_regression.py`."
    ) from exc


INPUT_PATH = Path("ml/outputs/ml_tract_dataset.csv")
METRICS_PATH = Path("ml/outputs/logistic_regression_metrics.json")
COEFFICIENTS_PATH = Path("ml/outputs/logistic_regression_coefficients.csv")
PREDICTIONS_PATH = Path("ml/outputs/logistic_regression_predictions.csv")
MODEL_PATH = Path("ml/models/logistic_regression_model.joblib")
TARGET_COLUMN = "elevated_arrest_activity_flag"
RANDOM_STATE = 42
TEST_SIZE = 0.30

LEAKAGE_COLUMNS = {
    TARGET_COLUMN,
    "arrests_per_1000_population",
    "total_arrests",
    "arrests_density_per_sq_mi",
    "arrest_activity_share",
    "arrest_weekend_events",
    "arrest_evening_night_events",
    "arrest_night_events",
    "felony_arrests",
    "misdemeanor_arrests",
}

IDENTIFIER_TEXT_COLUMNS = {
    "tract_geoid",
    "tract_name",
    "GEOID",
    "NAME",
    "state",
    "county",
    "tract",
    "primary_neighborhood",
    "secondary_neighborhoods",
    "most_common_offense",
    "most_common_arrest_type",
}

RESPONSIBLE_MODEL_NOTE = (
    "This model classifies census tracts into elevated and non-elevated arrest "
    "activity groups based on tract-level contextual features. It is not an "
    "individual-level risk model and should not be interpreted as predicting "
    "criminal behavior."
)


def find_repo_root() -> Path:
    """Find the repository root from this script or the current working tree."""
    start_paths = [Path.cwd(), Path(__file__).resolve()]

    for start_path in start_paths:
        current = start_path if start_path.is_dir() else start_path.parent
        for path in (current, *current.parents):
            if (path / "README.md").exists() and (path / "ml").exists():
                return path

    raise RuntimeError(
        "Could not find the repository root. Run this script from inside the "
        "Durham Risk Intelligence Dashboard repository."
    )


def load_dataset(repo_root: Path) -> pd.DataFrame:
    """Load the tract-level ML dataset created by build_ml_dataset.py."""
    input_path = repo_root / INPUT_PATH
    if not input_path.exists():
        raise RuntimeError(
            f"Input dataset not found: {INPUT_PATH}. Run "
            "`python ml/scripts/build_ml_dataset.py` before training."
        )

    dataframe = pd.read_csv(input_path)
    if TARGET_COLUMN not in dataframe.columns:
        raise RuntimeError(f"Target column not found: {TARGET_COLUMN}")

    dataframe[TARGET_COLUMN] = pd.to_numeric(
        dataframe[TARGET_COLUMN], errors="coerce"
    )
    dataframe = dataframe.dropna(subset=[TARGET_COLUMN]).copy()
    dataframe[TARGET_COLUMN] = dataframe[TARGET_COLUMN].astype(int)

    return dataframe


def select_features(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str], list[str]]:
    """Select numeric tract-level features after excluding leakage and text fields."""
    excluded_columns = sorted(
        column
        for column in dataframe.columns
        if column in LEAKAGE_COLUMNS or column in IDENTIFIER_TEXT_COLUMNS
    )
    candidate_features = dataframe.drop(columns=excluded_columns, errors="ignore")
    numeric_features = candidate_features.select_dtypes(include=[np.number]).copy()

    entirely_missing = [
        column for column in numeric_features.columns if numeric_features[column].isna().all()
    ]
    if entirely_missing:
        numeric_features = numeric_features.drop(columns=entirely_missing)
        excluded_columns.extend(entirely_missing)

    feature_columns = list(numeric_features.columns)
    if not feature_columns:
        raise RuntimeError(
            "No numeric feature columns remain after exclusions. Review the ML "
            "dataset and feature exclusion rules."
        )

    y = dataframe[TARGET_COLUMN]
    return numeric_features, y, feature_columns, sorted(set(excluded_columns))


def train_model(
    x: pd.DataFrame, y: pd.Series
) -> tuple[Pipeline, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Train a scaled and imputed logistic regression baseline."""
    class_counts = y.value_counts().sort_index()
    if len(class_counts) < 2:
        raise RuntimeError(
            "Training requires at least two target classes, but the dataset has "
            f"only: {class_counts.to_dict()}"
        )

    min_class_count = int(class_counts.min())
    if min_class_count < 2:
        raise RuntimeError(
            "Too few rows for a stratified train/test split. Each target class "
            f"needs at least 2 rows; class counts are {class_counts.to_dict()}."
        )

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "logistic_regression",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    return model, x_train, x_test, y_train, y_test


def evaluate_model(
    model: Pipeline,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    """Evaluate the model on held-out tract rows."""
    predicted = model.predict(x_test)
    predicted_probability = model.predict_proba(x_test)[:, 1]

    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_test, predicted)),
        "precision": float(precision_score(y_test, predicted, zero_division=0)),
        "recall": float(recall_score(y_test, predicted, zero_division=0)),
        "f1": float(f1_score(y_test, predicted, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, predicted).tolist(),
    }

    if y_test.nunique() == 2:
        metrics["roc_auc"] = float(roc_auc_score(y_test, predicted_probability))
    else:
        metrics["roc_auc"] = None

    return metrics, predicted, predicted_probability


def export_outputs(
    repo_root: Path,
    dataframe: pd.DataFrame,
    model: Pipeline,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    predicted: np.ndarray,
    predicted_probability: np.ndarray,
    metrics: dict[str, Any],
    feature_columns: list[str],
    excluded_columns: list[str],
    train_rows: int,
) -> dict[str, Path]:
    """Write metrics, coefficients, predictions, and the model artifact."""
    output_paths = {
        "metrics": repo_root / METRICS_PATH,
        "coefficients": repo_root / COEFFICIENTS_PATH,
        "predictions": repo_root / PREDICTIONS_PATH,
        "model": repo_root / MODEL_PATH,
    }
    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    class_counts = dataframe[TARGET_COLUMN].value_counts().sort_index()
    metrics_payload = {
        "model_name": "logistic_regression_baseline",
        "target_column": TARGET_COLUMN,
        "input_path": str(INPUT_PATH),
        "n_rows": int(len(dataframe)),
        "n_features": int(len(feature_columns)),
        "feature_columns": feature_columns,
        "excluded_columns": excluded_columns,
        "class_counts": {str(key): int(value) for key, value in class_counts.items()},
        "train_rows": int(train_rows),
        "test_rows": int(len(y_test)),
        **metrics,
        "notes": RESPONSIBLE_MODEL_NOTE,
    }
    output_paths["metrics"].write_text(
        json.dumps(metrics_payload, indent=2), encoding="utf-8"
    )

    classifier = model.named_steps["logistic_regression"]
    coefficients = classifier.coef_[0]
    coefficient_frame = pd.DataFrame(
        {
            "feature": feature_columns,
            "coefficient": coefficients,
            "odds_ratio": np.exp(coefficients),
            "absolute_coefficient": np.abs(coefficients),
        }
    ).sort_values("absolute_coefficient", ascending=False)
    coefficient_frame.to_csv(output_paths["coefficients"], index=False)

    prediction_frame = pd.DataFrame(
        {
            "actual": y_test.to_numpy(),
            "predicted": predicted,
            "predicted_probability_elevated": predicted_probability,
        },
        index=y_test.index,
    )
    if "tract_geoid" in dataframe.columns:
        prediction_frame.insert(0, "tract_geoid", dataframe.loc[y_test.index, "tract_geoid"])
    prediction_frame.to_csv(output_paths["predictions"], index=False)

    joblib.dump(model, output_paths["model"])
    return output_paths


def main() -> None:
    repo_root = find_repo_root()
    dataframe = load_dataset(repo_root)
    x, y, feature_columns, excluded_columns = select_features(dataframe)
    model, x_train, x_test, y_train, y_test = train_model(x, y)
    metrics, predicted, predicted_probability = evaluate_model(model, x_test, y_test)
    output_paths = export_outputs(
        repo_root=repo_root,
        dataframe=dataframe,
        model=model,
        x_test=x_test,
        y_test=y_test,
        predicted=predicted,
        predicted_probability=predicted_probability,
        metrics=metrics,
        feature_columns=feature_columns,
        excluded_columns=excluded_columns,
        train_rows=len(y_train),
    )

    class_counts = y.value_counts().sort_index().to_dict()
    print("Trained baseline logistic regression for tract-level arrest activity.")
    print(f"Input path: {INPUT_PATH}")
    print(f"Rows used: {len(dataframe)}")
    print(f"Number of features: {len(feature_columns)}")
    print(f"Class counts: {class_counts}")
    print(f"Train/test size: {len(y_train)}/{len(y_test)}")
    print(f"Accuracy: {metrics['accuracy']:.6f}")
    print(f"Precision: {metrics['precision']:.6f}")
    print(f"Recall: {metrics['recall']:.6f}")
    print(f"F1: {metrics['f1']:.6f}")
    if metrics.get("roc_auc") is not None:
        print(f"ROC AUC: {metrics['roc_auc']:.6f}")
    print(f"Metrics output: {output_paths['metrics'].relative_to(repo_root)}")
    print(f"Coefficients output: {output_paths['coefficients'].relative_to(repo_root)}")
    print(f"Predictions output: {output_paths['predictions'].relative_to(repo_root)}")
    print(f"Model output: {output_paths['model'].relative_to(repo_root)}")


if __name__ == "__main__":
    main()
