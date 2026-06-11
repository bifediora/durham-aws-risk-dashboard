"""Run Moran's I and local spatial association analysis for tract-level arrest activity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import geopandas as gpd
    import numpy as np
    import pandas as pd
    from esda.moran import Moran, Moran_Local
    from libpysal.weights import Queen
except ImportError as exc:
    raise SystemExit(
        "Missing required spatial analysis dependency. Install pandas, geopandas, "
        "numpy, libpysal, and esda in the active environment, then rerun "
        "`python ml/scripts/run_morans_i_hotspot_analysis.py`."
    ) from exc


INPUT_PATH = Path("data/processed/durham_arrests_tract_enriched.geojson")
GLOBAL_SUMMARY_PATH = Path("ml/outputs/morans_i_global_summary.json")
LOCAL_RESULTS_CSV_PATH = Path("ml/outputs/local_morans_i_results.csv")
LOCAL_RESULTS_GEOJSON_PATH = Path("ml/outputs/local_morans_i_tracts.geojson")
ANALYSIS_VARIABLE = "arrests_per_1000_population"
PERMUTATIONS = 999
RESPONSIBLE_USE_NOTE = (
    "This spatial autocorrelation analysis evaluates whether tract-level arrest "
    "activity is spatially clustered across census tracts. It is an exploratory "
    "spatial analysis, not an individual-level risk model, and should not be "
    "interpreted as predicting criminal behavior."
)


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


def load_tract_data(repo_root: Path) -> gpd.GeoDataFrame:
    """Load the tract-level arrest activity GeoJSON."""
    input_path = repo_root / INPUT_PATH
    if not input_path.exists():
        raise RuntimeError(f"Input spatial file not found: {INPUT_PATH}")

    return gpd.read_file(input_path)


def validate_inputs(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Validate geometry and the arrest activity analysis variable."""
    if gdf.empty:
        raise RuntimeError("Input GeoDataFrame is empty.")
    if gdf.geometry.name not in gdf.columns:
        raise RuntimeError("Input GeoDataFrame does not contain a geometry column.")
    if ANALYSIS_VARIABLE not in gdf.columns:
        raise RuntimeError(f"Missing required analysis variable: {ANALYSIS_VARIABLE}")

    validated = gdf.copy()
    validated[ANALYSIS_VARIABLE] = pd.to_numeric(
        validated[ANALYSIS_VARIABLE], errors="coerce"
    )
    if validated[ANALYSIS_VARIABLE].isna().any():
        missing_count = int(validated[ANALYSIS_VARIABLE].isna().sum())
        raise RuntimeError(
            f"Analysis variable {ANALYSIS_VARIABLE!r} contains {missing_count} "
            "missing or nonnumeric values."
        )
    if validated.geometry.is_empty.any() or validated.geometry.isna().any():
        raise RuntimeError("Input contains missing or empty geometries.")
    if len(validated) < 3:
        raise RuntimeError("At least three tracts are required for spatial analysis.")

    return validated


def build_spatial_weights(gdf: gpd.GeoDataFrame) -> Queen:
    """Build row-standardized Queen contiguity weights from tract polygons."""
    weights = Queen.from_dataframe(gdf, use_index=False)
    weights.transform = "R"
    return weights


def run_global_morans_i(values: np.ndarray, weights: Queen) -> Moran:
    """Run global Moran's I with permutation inference."""
    return Moran(values, weights, permutations=PERMUTATIONS)


def run_local_morans_i(values: np.ndarray, weights: Queen) -> Moran_Local:
    """Run local Moran's I with permutation inference."""
    return Moran_Local(values, weights, permutations=PERMUTATIONS)


def classify_lisa_clusters(
    quadrants: np.ndarray,
    p_values: np.ndarray,
    significance_threshold: float = 0.05,
) -> list[str]:
    """Classify local spatial association clusters using quadrant and significance."""
    quadrant_labels = {
        1: "High-High",
        2: "Low-High",
        3: "Low-Low",
        4: "High-Low",
    }

    clusters: list[str] = []
    for quadrant, p_value in zip(quadrants, p_values):
        if p_value <= significance_threshold:
            clusters.append(quadrant_labels.get(int(quadrant), "Not significant"))
        else:
            clusters.append("Not significant")
    return clusters


def _json_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if np.isnan(value):
            return None
    except TypeError:
        pass
    return float(value)


def export_outputs(
    repo_root: Path,
    gdf: gpd.GeoDataFrame,
    weights: Queen,
    global_moran: Moran,
) -> dict[str, Path]:
    """Export global summary JSON plus local CSV and GeoJSON results."""
    output_paths = {
        "global_summary": repo_root / GLOBAL_SUMMARY_PATH,
        "local_results_csv": repo_root / LOCAL_RESULTS_CSV_PATH,
        "local_results_geojson": repo_root / LOCAL_RESULTS_GEOJSON_PATH,
    }
    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    non_geometry_columns = [column for column in gdf.columns if column != gdf.geometry.name]
    gdf[non_geometry_columns].to_csv(output_paths["local_results_csv"], index=False)
    gdf.to_file(output_paths["local_results_geojson"], driver="GeoJSON")

    cluster_counts_05 = gdf["lisa_cluster"].value_counts().sort_index().to_dict()
    cluster_counts_10 = (
        gdf.loc[gdf["lisa_significant_10"], "local_moran_quadrant"]
        .map({1: "High-High", 2: "Low-High", 3: "Low-Low", 4: "High-Low"})
        .fillna("Not significant")
        .value_counts()
        .reindex(["High-High", "Low-High", "Low-Low", "High-Low"], fill_value=0)
        .to_dict()
    )
    cluster_counts_10["Not significant"] = int((~gdf["lisa_significant_10"]).sum())

    summary = {
        "input_path": str(INPUT_PATH),
        "analysis_variable": ANALYSIS_VARIABLE,
        "n_tracts": int(len(gdf)),
        "spatial_weights_method": "Queen contiguity",
        "spatial_weights": "Queen contiguity",
        "weights_transform": "row-standardized",
        "islands": [int(island) for island in weights.islands],
        "permutations": PERMUTATIONS,
        "morans_i": _json_float(global_moran.I),
        "global_morans_i": _json_float(global_moran.I),
        "expected_i": _json_float(global_moran.EI),
        "variance_norm": _json_float(global_moran.VI_norm),
        "z_norm": _json_float(global_moran.z_norm),
        "p_norm": _json_float(global_moran.p_norm),
        "z_rand": _json_float(getattr(global_moran, "z_rand", None)),
        "p_rand": _json_float(getattr(global_moran, "p_rand", None)),
        "p_sim": _json_float(global_moran.p_sim),
        "z_sim": _json_float(getattr(global_moran, "z_sim", None)),
        "cluster_counts_05": {key: int(value) for key, value in cluster_counts_05.items()},
        "cluster_counts_10": {key: int(value) for key, value in cluster_counts_10.items()},
        "output_paths": {
            name: str(path.relative_to(repo_root)) for name, path in output_paths.items()
        },
        "responsible_use_note": RESPONSIBLE_USE_NOTE,
    }
    output_paths["global_summary"].write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return output_paths


def main() -> None:
    repo_root = find_repo_root()
    gdf = validate_inputs(load_tract_data(repo_root))
    weights = build_spatial_weights(gdf)

    values = gdf[ANALYSIS_VARIABLE].to_numpy()
    global_moran = run_global_morans_i(values, weights)
    local_moran = run_local_morans_i(values, weights)

    gdf = gdf.copy()
    gdf["local_moran_i"] = local_moran.Is
    gdf["local_moran_p_sim"] = local_moran.p_sim
    gdf["local_moran_z_sim"] = local_moran.z_sim
    gdf["local_moran_quadrant"] = local_moran.q
    gdf["lisa_significant_05"] = gdf["local_moran_p_sim"] <= 0.05
    gdf["lisa_significant_10"] = gdf["local_moran_p_sim"] <= 0.10
    gdf["lisa_cluster"] = classify_lisa_clusters(
        gdf["local_moran_quadrant"].to_numpy(),
        gdf["local_moran_p_sim"].to_numpy(),
        significance_threshold=0.05,
    )

    output_paths = export_outputs(repo_root, gdf, weights, global_moran)
    cluster_counts_05 = gdf["lisa_cluster"].value_counts().sort_index().to_dict()

    print("Ran exploratory spatial autocorrelation analysis for tract-level arrest activity.")
    print(f"Input path: {INPUT_PATH}")
    print(f"Analysis variable: {ANALYSIS_VARIABLE}")
    print(f"Number of tracts: {len(gdf)}")
    print("Spatial weights method: Queen contiguity, row-standardized")
    print(f"Number of islands: {len(weights.islands)}")
    print(f"Weight diagnostics: n={weights.n}, components={weights.n_components}")
    print(f"Global Moran's I: {global_moran.I:.6f}")
    print(f"p_sim: {global_moran.p_sim:.6f}")
    print(f"Cluster counts at p <= 0.05: {cluster_counts_05}")
    print(f"Global summary output: {output_paths['global_summary'].relative_to(repo_root)}")
    print(f"Local CSV output: {output_paths['local_results_csv'].relative_to(repo_root)}")
    print(
        "Local GeoJSON output: "
        f"{output_paths['local_results_geojson'].relative_to(repo_root)}"
    )


if __name__ == "__main__":
    main()
