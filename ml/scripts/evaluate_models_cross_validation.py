"""Evaluate baseline tract-level models with repeated stratified CV."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import make_scorer, precision_score, recall_score, f1_score
    from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
except ImportError as exc:
    raise SystemExit(
        "Missing required ML dependency. Install pandas, numpy, and scikit-learn "
        "in the active environment, then rerun "
        "`python ml/scripts/evaluate_models_cross_validation.py`."
    ) from exc


INPUT_PATH = Path("ml/outputs/ml_tract_dataset.csv")
RESULTS_PATH = Path("ml/outputs/model_cross_validation_results.csv")
SUMMARY_PATH = Path("ml/outputs/model_cross_validation_summary.json")
TARGET_COLUMN = "elevated_arrest_activity_flag"
RANDOM_STATE = 42
N_SPLITS = 5
N_REPEATS = 10

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

RESPONSIBLE_NOTE = (
    "This cross-validation evaluation compares tract-level models for elevated "
    "arrest activity classification. It is not an individual-level risk model "
    "and should not be interpreted as predicting criminal behavior."
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
    """Load the tract-level ML dataset."""
    input_path = repo_root / INPUT_PATH
    if not input_path.exists():
        raise RuntimeError(
            f"Input dataset not found: {INPUT_PATH}. Run "
            "`python ml/scripts/build_ml_dataset.py` before evaluation."
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


def select_features(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, list[str], list[str]]:
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
    class_counts = y.value_counts().sort_index()
    if len(class_counts) < 2:
        raise RuntimeError(
            "Cross-validation requires at least two target classes, but the "
            f"dataset has only: {class_counts.to_dict()}."
        )
    if int(class_counts.min()) < N_SPLITS:
        raise RuntimeError(
            f"Cross-validation requires at least {N_SPLITS} rows in each class. "
            f"Class counts are {class_counts.to_dict()}."
        )

    return numeric_features, y, feature_columns, sorted(set(excluded_columns))


def build_models() -> dict[str, Pipeline]:
    """Build model pipelines for repeated stratified cross-validation."""
    return {
        "logistic_regression": Pipeline(
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
        ),
        "random_forest": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "random_forest",
                    RandomForestClassifier(
                        n_estimators=300,
                        max_depth=4,
                        min_samples_leaf=3,
                        random_state=RANDOM_STATE,
                        class_weight="balanced",
                    ),
                ),
            ]
        ),
    }


def run_cross_validation(
    models: dict[str, Pipeline], x: pd.DataFrame, y: pd.Series
) -> pd.DataFrame:
    """Run repeated stratified cross-validation and return fold-level results."""
    cv = RepeatedStratifiedKFold(
        n_splits=N_SPLITS,
        n_repeats=N_REPEATS,
        random_state=RANDOM_STATE,
    )
    scoring = {
        "accuracy": "accuracy",
        "precision": make_scorer(precision_score, zero_division=0),
        "recall": make_scorer(recall_score, zero_division=0),
        "f1": make_scorer(f1_score, zero_division=0),
        "roc_auc": "roc_auc",
    }

    result_frames: list[pd.DataFrame] = []
    for model_name, model in models.items():
        cv_results = cross_validate(
            model,
            x,
            y,
            cv=cv,
            scoring=scoring,
            error_score=np.nan,
            n_jobs=None,
        )
        frame = pd.DataFrame(
            {
                "model_name": model_name,
                "fold_index": np.arange(1, len(cv_results["test_accuracy"]) + 1),
                "accuracy": cv_results["test_accuracy"],
                "precision": cv_results["test_precision"],
                "recall": cv_results["test_recall"],
                "f1": cv_results["test_f1"],
                "roc_auc": cv_results["test_roc_auc"],
            }
        )
        result_frames.append(frame)

    return pd.concat(result_frames, ignore_index=True)


def _metric_summary(results: pd.DataFrame) -> dict[str, dict[str, dict[str, float | None]]]:
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    summary: dict[str, dict[str, dict[str, float | None]]] = {}

    for model_name, group in results.groupby("model_name"):
        summary[model_name] = {}
        for metric in metrics:
            values = group[metric].dropna()
            if values.empty:
                summary[model_name][metric] = {
                    "mean": None,
                    "std": None,
                    "min": None,
                    "max": None,
                }
            else:
                summary[model_name][metric] = {
                    "mean": float(values.mean()),
                    "std": float(values.std(ddof=1)),
                    "min": float(values.min()),
                    "max": float(values.max()),
                }

    return summary


def export_outputs(
    repo_root: Path,
    dataframe: pd.DataFrame,
    y: pd.Series,
    feature_columns: list[str],
    excluded_columns: list[str],
    results: pd.DataFrame,
) -> dict[str, Path]:
    """Write cross-validation fold results and summary JSON."""
    output_paths = {
        "results": repo_root / RESULTS_PATH,
        "summary": repo_root / SUMMARY_PATH,
    }
    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    results.to_csv(output_paths["results"], index=False)

    class_counts = y.value_counts().sort_index()
    summary_payload: dict[str, Any] = {
        "input_path": str(INPUT_PATH),
        "target_column": TARGET_COLUMN,
        "n_rows": int(len(dataframe)),
        "n_features": int(len(feature_columns)),
        "class_counts": {str(key): int(value) for key, value in class_counts.items()},
        "cv_method": "RepeatedStratifiedKFold",
        "n_splits": N_SPLITS,
        "n_repeats": N_REPEATS,
        "metrics_by_model": _metric_summary(results),
        "feature_columns": feature_columns,
        "excluded_columns": excluded_columns,
        "notes": RESPONSIBLE_NOTE,
    }
    output_paths["summary"].write_text(
        json.dumps(summary_payload, indent=2), encoding="utf-8"
    )

    return output_paths


def main() -> None:
    repo_root = find_repo_root()
    dataframe = load_dataset(repo_root)
    x, y, feature_columns, excluded_columns = select_features(dataframe)
    models = build_models()
    results = run_cross_validation(models, x, y)
    output_paths = export_outputs(
        repo_root=repo_root,
        dataframe=dataframe,
        y=y,
        feature_columns=feature_columns,
        excluded_columns=excluded_columns,
        results=results,
    )

    class_counts = y.value_counts().sort_index().to_dict()
    print("Evaluated baseline models with repeated stratified cross-validation.")
    print(f"Input path: {INPUT_PATH}")
    print(f"Rows used: {len(dataframe)}")
    print(f"Features used: {len(feature_columns)}")
    print(f"Class counts: {class_counts}")
    print(f"CV method: RepeatedStratifiedKFold ({N_SPLITS} splits, {N_REPEATS} repeats)")
    print(f"Model names: {', '.join(models.keys())}")

    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    for model_name, group in results.groupby("model_name"):
        print(f"{model_name}:")
        for metric in metrics:
            values = group[metric].dropna()
            if values.empty:
                print(f"  {metric}: mean=nan std=nan")
            else:
                print(f"  {metric}: mean={values.mean():.6f} std={values.std(ddof=1):.6f}")

    print(f"Results output: {output_paths['results'].relative_to(repo_root)}")
    print(f"Summary output: {output_paths['summary'].relative_to(repo_root)}")


if __name__ == "__main__":
    main()
