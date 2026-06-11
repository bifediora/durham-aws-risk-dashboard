"""Evaluate PCA-compressed logistic regression for tract-level arrest activity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.decomposition import PCA
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import f1_score, make_scorer, precision_score, recall_score
    from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
except ImportError as exc:
    raise SystemExit(
        "Missing required ML dependency. Install pandas, numpy, scikit-learn, "
        "and joblib in the active environment, then rerun "
        "`python ml/scripts/train_pca_logistic_regression.py`."
    ) from exc


INPUT_PATH = Path("ml/outputs/ml_tract_dataset.csv")
CV_RESULTS_PATH = Path("ml/outputs/pca_logistic_regression_cv_results.csv")
CV_SUMMARY_PATH = Path("ml/outputs/pca_logistic_regression_cv_summary.json")
LOADINGS_PATH = Path("ml/outputs/pca_component_loadings.csv")
MODEL_PATH = Path("ml/models/pca_logistic_regression_model.joblib")
TARGET_COLUMN = "elevated_arrest_activity_flag"
RANDOM_STATE = 42
N_SPLITS = 5
N_REPEATS = 10
TESTED_COMPONENTS = [5, 6, 7, 8]
F1_TIE_TOLERANCE = 0.02

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
    "This PCA-compressed logistic regression model evaluates whether correlated "
    "tract-level contextual indicators can be represented as lower-dimensional "
    "components for elevated arrest activity classification. It is not an "
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
    """Load the tract-level ML dataset."""
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

    if max(TESTED_COMPONENTS) > len(feature_columns):
        raise RuntimeError(
            "The requested PCA component count exceeds the available feature "
            f"count. Features: {len(feature_columns)}, requested max: "
            f"{max(TESTED_COMPONENTS)}."
        )

    y = dataframe[TARGET_COLUMN]
    class_counts = y.value_counts().sort_index()
    if len(class_counts) < 2:
        raise RuntimeError(
            "PCA logistic regression requires at least two target classes, but "
            f"the dataset has only: {class_counts.to_dict()}."
        )
    if int(class_counts.min()) < N_SPLITS:
        raise RuntimeError(
            f"Repeated stratified cross-validation requires at least {N_SPLITS} "
            f"rows in each class. Class counts are {class_counts.to_dict()}."
        )

    return numeric_features, y, feature_columns, sorted(set(excluded_columns))


def build_pca_model(n_components: int) -> Pipeline:
    """Build a PCA-compressed logistic regression pipeline."""
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=n_components, random_state=RANDOM_STATE)),
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


def evaluate_component_range(x: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Evaluate each PCA component count with repeated stratified CV."""
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
    for n_components in TESTED_COMPONENTS:
        model = build_pca_model(n_components)
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
                "model_name": "pca_logistic_regression",
                "n_components": n_components,
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

    for n_components, group in results.groupby("n_components"):
        component_key = str(int(n_components))
        summary[component_key] = {}
        for metric in metrics:
            values = group[metric].dropna()
            if values.empty:
                summary[component_key][metric] = {
                    "mean": None,
                    "std": None,
                    "min": None,
                    "max": None,
                }
            else:
                summary[component_key][metric] = {
                    "mean": float(values.mean()),
                    "std": float(values.std(ddof=1)),
                    "min": float(values.min()),
                    "max": float(values.max()),
                }

    return summary


def _select_component_count(results: pd.DataFrame) -> tuple[int, str]:
    f1_summary = (
        results.groupby("n_components")["f1"]
        .mean()
        .dropna()
        .sort_index()
    )
    if f1_summary.empty:
        raise RuntimeError("All PCA logistic regression F1 scores are missing.")

    best_f1 = float(f1_summary.max())
    eligible = f1_summary[f1_summary >= best_f1 - F1_TIE_TOLERANCE]
    selected_n_components = int(eligible.index.min())

    if len(eligible) > 1:
        rationale = (
            f"Highest mean F1 was {best_f1:.4f}. Component counts within "
            f"{F1_TIE_TOLERANCE:.2f} of that value were "
            f"{[int(value) for value in eligible.index]}; selected the smaller "
            f"component count ({selected_n_components}) for parsimony."
        )
    else:
        rationale = (
            f"Selected {selected_n_components} components because it had the "
            f"highest mean F1 ({best_f1:.4f})."
        )

    return selected_n_components, rationale


def train_final_model(
    x: pd.DataFrame, y: pd.Series, selected_n_components: int
) -> Pipeline:
    """Train the final PCA logistic regression model on the full dataset."""
    model = build_pca_model(selected_n_components)
    model.fit(x, y)
    return model


def _build_loadings_frame(model: Pipeline, feature_columns: list[str]) -> pd.DataFrame:
    pca = model.named_steps["pca"]
    rows: list[dict[str, Any]] = []

    for component_index, component_loadings in enumerate(pca.components_, start=1):
        for feature, loading in zip(feature_columns, component_loadings):
            rows.append(
                {
                    "component": f"PC{component_index}",
                    "feature": feature,
                    "loading": float(loading),
                    "absolute_loading": float(abs(loading)),
                }
            )

    return pd.DataFrame(rows).sort_values(
        ["component", "absolute_loading"], ascending=[True, False]
    )


def export_outputs(
    repo_root: Path,
    dataframe: pd.DataFrame,
    y: pd.Series,
    feature_columns: list[str],
    excluded_columns: list[str],
    results: pd.DataFrame,
    final_model: Pipeline,
    selected_n_components: int,
    selection_rationale: str,
) -> dict[str, Path]:
    """Write CV results, summary JSON, PCA loadings, and model artifact."""
    output_paths = {
        "cv_results": repo_root / CV_RESULTS_PATH,
        "cv_summary": repo_root / CV_SUMMARY_PATH,
        "loadings": repo_root / LOADINGS_PATH,
        "model": repo_root / MODEL_PATH,
    }
    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    results.to_csv(output_paths["cv_results"], index=False)

    loadings = _build_loadings_frame(final_model, feature_columns)
    loadings.to_csv(output_paths["loadings"], index=False)

    class_counts = y.value_counts().sort_index()
    summary_payload: dict[str, Any] = {
        "input_path": str(INPUT_PATH),
        "target_column": TARGET_COLUMN,
        "n_rows": int(len(dataframe)),
        "n_features_before_pca": int(len(feature_columns)),
        "class_counts": {str(key): int(value) for key, value in class_counts.items()},
        "cv_method": "RepeatedStratifiedKFold",
        "n_splits": N_SPLITS,
        "n_repeats": N_REPEATS,
        "tested_components": TESTED_COMPONENTS,
        "selected_n_components": selected_n_components,
        "selection_rationale": selection_rationale,
        "metrics_by_component_count": _metric_summary(results),
        "feature_columns": feature_columns,
        "excluded_columns": excluded_columns,
        "notes": RESPONSIBLE_NOTE,
    }
    output_paths["cv_summary"].write_text(
        json.dumps(summary_payload, indent=2), encoding="utf-8"
    )

    joblib.dump(final_model, output_paths["model"])
    return output_paths


def main() -> None:
    repo_root = find_repo_root()
    dataframe = load_dataset(repo_root)
    x, y, feature_columns, excluded_columns = select_features(dataframe)
    results = evaluate_component_range(x, y)
    selected_n_components, selection_rationale = _select_component_count(results)
    final_model = train_final_model(x, y, selected_n_components)
    output_paths = export_outputs(
        repo_root=repo_root,
        dataframe=dataframe,
        y=y,
        feature_columns=feature_columns,
        excluded_columns=excluded_columns,
        results=results,
        final_model=final_model,
        selected_n_components=selected_n_components,
        selection_rationale=selection_rationale,
    )

    class_counts = y.value_counts().sort_index().to_dict()
    print("Evaluated PCA-compressed logistic regression for tract-level arrest activity.")
    print(f"Input path: {INPUT_PATH}")
    print(f"Rows used: {len(dataframe)}")
    print(f"Number of original features: {len(feature_columns)}")
    print(f"Class counts: {class_counts}")
    print(f"CV method: RepeatedStratifiedKFold ({N_SPLITS} splits, {N_REPEATS} repeats)")
    print(f"Tested component counts: {TESTED_COMPONENTS}")

    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    for n_components, group in results.groupby("n_components"):
        print(f"{int(n_components)} components:")
        for metric in metrics:
            values = group[metric].dropna()
            if values.empty:
                print(f"  {metric}: mean=nan std=nan")
            else:
                print(f"  {metric}: mean={values.mean():.6f} std={values.std(ddof=1):.6f}")

    print(f"Selected component count: {selected_n_components}")
    print(f"Selection rationale: {selection_rationale}")
    print(f"CV results output: {output_paths['cv_results'].relative_to(repo_root)}")
    print(f"CV summary output: {output_paths['cv_summary'].relative_to(repo_root)}")
    print(f"Component loadings output: {output_paths['loadings'].relative_to(repo_root)}")
    print(f"Model output: {output_paths['model'].relative_to(repo_root)}")


if __name__ == "__main__":
    main()
