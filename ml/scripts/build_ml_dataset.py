"""Build the first tract-level ML dataset for arrest activity analysis."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing required dependency: pandas. Activate the project environment "
        "or install dependencies from requirements.txt, then rerun "
        "`python ml/scripts/build_ml_dataset.py`."
    ) from exc


OUTPUT_PATH = Path("ml/outputs/ml_tract_dataset.csv")
PREFERRED_RATE_COLUMN = "arrests_per_1000_population"
TARGET_COLUMN = "elevated_arrest_activity_flag"
TRACT_ID_CANDIDATES = ("tract_geoid", "GEOID", "geoid", "tract")
RATE_COLUMN_CANDIDATES = (
    PREFERRED_RATE_COLUMN,
    "arrest_per_1000_population",
    "arrests_per_1000_residents",
    "arrest_rate_per_1000",
    "arrests_rate_per_1000",
    "arrest_activity_rate",
)


@dataclass
class CandidateInspection:
    path: Path
    status: str
    rows: int | None = None
    columns: list[str] | None = None


def find_repo_root() -> Path:
    """Find the repository root from this script or the current working tree."""
    start_paths = [Path.cwd(), Path(__file__).resolve()]

    for start_path in start_paths:
        current = start_path if start_path.is_dir() else start_path.parent
        for path in (current, *current.parents):
            if (path / "README.md").exists() and (path / "data").exists():
                return path

    raise RuntimeError(
        "Could not find the repository root. Run this script from inside the "
        "Durham Risk Intelligence Dashboard repository."
    )


def discover_candidate_files(repo_root: Path) -> list[Path]:
    """Discover likely processed tract-level arrest/context files."""
    processed_dir = repo_root / "data" / "processed"
    if not processed_dir.exists():
        return []

    supported_suffixes = {".csv", ".geojson", ".json", ".parquet"}
    files = [
        path
        for path in processed_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in supported_suffixes
        and "shooting" not in path.name.lower()
        and "shootings" not in path.name.lower()
    ]

    def priority(path: Path) -> tuple[int, str]:
        name = path.name.lower()
        score = 100
        if "arrest" in name and "tract" in name and "enriched" in name:
            score = 0
        elif "tract" in name and "enriched" in name:
            score = 10
        elif "acs" in name and "tract" in name:
            score = 30
        elif "arrest" in name and "tract" in name:
            score = 40
        return (score, str(path))

    return sorted(files, key=priority)


def _read_geojson_properties(path: Path) -> pd.DataFrame:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("GeoJSON file does not contain a features list.")

    properties = [feature.get("properties", {}) for feature in features]
    return pd.DataFrame(properties)


def _read_dataset(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".geojson":
        return _read_geojson_properties(path)
    if suffix == ".json":
        return pd.read_json(path)

    raise ValueError(f"Unsupported file type: {path.suffix}")


def detect_rate_column(columns: list[str]) -> str | None:
    """Detect the tract-level arrest activity rate column."""
    exact_lookup = {column.lower(): column for column in columns}
    for candidate in RATE_COLUMN_CANDIDATES:
        if candidate.lower() in exact_lookup:
            return exact_lookup[candidate.lower()]

    for column in columns:
        normalized = column.lower()
        if "arrest" in normalized and "1000" in normalized:
            return column

    return None


def _detect_tract_id_column(columns: list[str]) -> str | None:
    exact_lookup = {column.lower(): column for column in columns}
    for candidate in TRACT_ID_CANDIDATES:
        if candidate.lower() in exact_lookup:
            return exact_lookup[candidate.lower()]
    return None


def load_candidate_dataset(
    candidate_files: list[Path],
) -> tuple[pd.DataFrame, Path, str, list[CandidateInspection]]:
    """Load the first usable tract-level arrest activity dataset."""
    inspections: list[CandidateInspection] = []

    for path in candidate_files:
        try:
            dataframe = _read_dataset(path)
        except Exception as exc:
            inspections.append(CandidateInspection(path=path, status=f"load failed: {exc}"))
            continue

        columns = list(dataframe.columns)
        rate_column = detect_rate_column(columns)
        tract_id_column = _detect_tract_id_column(columns)
        inspections.append(
            CandidateInspection(
                path=path,
                status=(
                    f"loaded; tract_id_column={tract_id_column or 'missing'}; "
                    f"rate_column={rate_column or 'missing'}"
                ),
                rows=len(dataframe),
                columns=columns,
            )
        )

        if tract_id_column is None or rate_column is None:
            continue

        if dataframe[tract_id_column].duplicated().any():
            inspections[-1].status += "; skipped duplicate tract identifiers"
            continue

        return dataframe.copy(), path, rate_column, inspections

    inspected = "\n".join(_format_inspection(item) for item in inspections)
    raise RuntimeError(
        "Could not find a usable tract-level arrest activity dataset.\n"
        "Required: one tract identifier column and one arrests-per-1,000 rate column.\n"
        "Inspected candidate files:\n"
        f"{inspected or 'No candidate files found under data/processed.'}"
    )


def build_target(dataframe: pd.DataFrame, rate_column: str) -> tuple[pd.DataFrame, float]:
    """Add the elevated arrest activity target from the top quartile rate."""
    output = dataframe.copy()
    output[rate_column] = pd.to_numeric(output[rate_column], errors="coerce")

    valid_rates = output[rate_column].dropna()
    if valid_rates.empty:
        raise RuntimeError(
            f"Column {rate_column!r} exists but does not contain numeric rate values."
        )

    threshold = float(valid_rates.quantile(0.75))
    output[TARGET_COLUMN] = (output[rate_column] >= threshold).astype(int)
    return output, threshold


def _format_inspection(inspection: CandidateInspection) -> str:
    row_text = "unknown rows" if inspection.rows is None else f"{inspection.rows} rows"
    columns = inspection.columns or []
    column_preview = ", ".join(columns[:12])
    if len(columns) > 12:
        column_preview += ", ..."
    return f"- {inspection.path}: {inspection.status}; {row_text}; columns: {column_preview}"


def main() -> None:
    repo_root = find_repo_root()
    candidate_files = discover_candidate_files(repo_root)

    dataframe, input_path, rate_column, inspections = load_candidate_dataset(candidate_files)
    ml_dataset, threshold = build_target(dataframe, rate_column)

    output_path = repo_root / OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ml_dataset.to_csv(output_path, index=False)

    elevated_count = int(ml_dataset[TARGET_COLUMN].sum())
    non_elevated_count = int(len(ml_dataset) - elevated_count)

    # This is a tract-level analytical dataset, not individual-level risk scoring.
    print("Built tract-level arrest activity ML dataset.")
    print(f"Input file used: {input_path.relative_to(repo_root)}")
    print(f"Detected rate column: {rate_column}")
    print(f"Number of tracts: {len(ml_dataset)}")
    print(f"Target threshold value: {threshold:.6f}")
    print(f"Elevated tracts: {elevated_count}")
    print(f"Non-elevated tracts: {non_elevated_count}")
    print(f"Output path: {output_path.relative_to(repo_root)}")

    if len(inspections) > 1:
        print("Candidate files inspected before selection:")
        for inspection in inspections:
            print(_format_inspection(inspection))


if __name__ == "__main__":
    main()
