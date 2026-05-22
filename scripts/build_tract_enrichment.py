from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

TRACTS_GEOJSON_PATH = (
    PROJECT_ROOT
    / "app"
    / "static"
    / "geojson"
    / "durham_city_intersecting_tracts.geojson"
)

ARRESTS_WITH_TRACTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "arrests_with_tract_join.csv"
)

ACS_DEMOGRAPHICS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "durham_acs_tract_demographics.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_GEOJSON_PATH = OUTPUT_DIR / "durham_tract_enriched.geojson"
OUTPUT_CSV_PATH = OUTPUT_DIR / "durham_tract_enriched.csv"

WEB_CRS = "EPSG:4326"
PROJECTED_CRS = "EPSG:2264"


def normalize_geoid(value):
    if pd.isna(value):
        return None

    geoid = str(value).strip()

    if geoid.endswith(".0"):
        geoid = geoid[:-2]

    if not geoid or geoid.lower() in ["nan", "none", "not assigned"]:
        return None

    return geoid.zfill(11)


def pct(numerator, denominator):
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return 0.0

    return round((numerator / denominator) * 100, 2)


def rate_per_1000(numerator, denominator):
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return 0.0

    return round((numerator / denominator) * 1000, 2)


def safe_mode(series):
    clean_values = series.dropna().astype(str).str.strip()
    clean_values = clean_values[clean_values != ""]

    if clean_values.empty:
        return "Not available"

    return clean_values.value_counts().idxmax()


def load_tract_geometries():
    if not TRACTS_GEOJSON_PATH.exists():
        raise FileNotFoundError(
            f"Missing tract geometry file: {TRACTS_GEOJSON_PATH}"
        )

    tracts = gpd.read_file(TRACTS_GEOJSON_PATH)

    print(f"Loaded tract geometries from: {TRACTS_GEOJSON_PATH}")
    print(f"Original tract CRS: {tracts.crs}")

    if tracts.crs is None:
        tracts = tracts.set_crs(WEB_CRS)

    tracts = tracts.to_crs(WEB_CRS)

    geoid_candidates = ["GEOID", "GEOID20", "geoid", "TRACT_GEOID", "tract_geoid"]
    name_candidates = ["NAMELSAD", "NAME", "name", "tract_name"]

    geoid_column = next(
        (column for column in geoid_candidates if column in tracts.columns),
        None,
    )

    name_column = next(
        (column for column in name_candidates if column in tracts.columns),
        None,
    )

    if geoid_column is None:
        raise ValueError("Could not find a tract GEOID field in the tract geometry layer.")

    if name_column is None:
        name_column = geoid_column

    tracts["tract_geoid"] = tracts[geoid_column].apply(normalize_geoid)
    tracts["tract_name"] = tracts[name_column].fillna("").astype(str)

    projected_tracts = tracts.to_crs(PROJECTED_CRS)
    tracts["tract_area_sq_m"] = projected_tracts.geometry.area
    tracts["tract_area_sq_mi"] = tracts["tract_area_sq_m"] / 2_589_988.110336

    tracts = tracts[
        [
            "tract_geoid",
            "tract_name",
            "tract_area_sq_m",
            "tract_area_sq_mi",
            "geometry",
        ]
    ].copy()

    return tracts


def load_acs_demographics():
    if not ACS_DEMOGRAPHICS_PATH.exists():
        raise FileNotFoundError(
            f"Missing ACS demographic file: {ACS_DEMOGRAPHICS_PATH}\n"
            "Run scripts/extract_durham_acs_tracts.py first."
        )

    acs = pd.read_csv(ACS_DEMOGRAPHICS_PATH, dtype={"GEOID": str, "tract_geoid": str})

    print(f"Loaded ACS demographics from: {ACS_DEMOGRAPHICS_PATH}")

    geoid_candidates = ["GEOID", "geoid", "tract_geoid", "TRACT_GEOID"]

    geoid_column = next(
        (column for column in geoid_candidates if column in acs.columns),
        None,
    )

    if geoid_column is None:
        raise ValueError("Could not find a tract GEOID field in the ACS demographic data.")

    acs["tract_geoid"] = acs[geoid_column].apply(normalize_geoid)

    if geoid_column != "tract_geoid":
        acs = acs.drop(columns=[geoid_column], errors="ignore")

    for column in acs.columns:
        if column in ["tract_geoid", "NAME", "state", "county", "tract"]:
            continue

        acs[column] = pd.to_numeric(acs[column], errors="coerce")

    return acs


def load_arrests_with_tracts():
    if not ARRESTS_WITH_TRACTS_PATH.exists():
        raise FileNotFoundError(
            f"Missing arrest tract join file: {ARRESTS_WITH_TRACTS_PATH}\n"
            "Run scripts/build_tract_join.py first."
        )

    arrests = pd.read_csv(
        ARRESTS_WITH_TRACTS_PATH,
        low_memory=False,
        dtype={"tract_geoid": str},
    )

    print(f"Loaded tract joined arrests from: {ARRESTS_WITH_TRACTS_PATH}")

    if "tract_geoid" not in arrests.columns:
        raise ValueError("The arrest tract join file must include tract_geoid.")

    arrests["tract_geoid"] = arrests["tract_geoid"].apply(normalize_geoid)

    if "inside_intersecting_tract" in arrests.columns:
        arrests["inside_intersecting_tract"] = (
            arrests["inside_intersecting_tract"]
            .fillna(False)
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes", "y"])
        )

        arrests = arrests[arrests["inside_intersecting_tract"]].copy()

    arrests = arrests[arrests["tract_geoid"].notna()].copy()

    if "severity_label" not in arrests.columns:
        if "F/M" in arrests.columns:
            arrests["severity_label"] = (
                arrests["F/M"]
                .fillna("Unknown")
                .astype(str)
                .str.upper()
                .map({"F": "Felony", "M": "Misdemeanor"})
                .fillna("Unknown")
            )
        else:
            arrests["severity_label"] = "Unknown"

    if "event_date" in arrests.columns:
        arrests["event_date"] = pd.to_datetime(arrests["event_date"], errors="coerce")
    elif "Arrest Date" in arrests.columns:
        arrests["event_date"] = pd.to_datetime(arrests["Arrest Date"], errors="coerce")
    else:
        arrests["event_date"] = pd.NaT

    if "event_weekday" not in arrests.columns:
        arrests["event_weekday"] = arrests["event_date"].dt.day_name()

    if "event_hour" in arrests.columns:
        arrests["event_hour"] = pd.to_numeric(arrests["event_hour"], errors="coerce")
    elif "Arrest Date" in arrests.columns and "Arrest Time" in arrests.columns:
        combined_datetime = (
            arrests["Arrest Date"].astype(str).str.strip()
            + " "
            + arrests["Arrest Time"].astype(str).str.strip()
        )

        arrests["event_hour"] = pd.to_datetime(
            combined_datetime,
            errors="coerce",
        ).dt.hour
    else:
        arrests["event_hour"] = pd.NA

    if "time_period" not in arrests.columns:
        def get_time_period(hour):
            if pd.isna(hour):
                return "Unknown"

            hour = int(hour)

            if 5 <= hour <= 11:
                return "Morning"

            if 12 <= hour <= 16:
                return "Afternoon"

            if 17 <= hour <= 20:
                return "Evening"

            return "Night"

        arrests["time_period"] = arrests["event_hour"].apply(get_time_period)

    return arrests


def calculate_recent_activity_trend(group):
    valid_dates = group["event_date"].dropna()

    if valid_dates.empty:
        return "Stable"

    latest_date = valid_dates.max()
    current_start = latest_date - pd.Timedelta(days=29)
    previous_start = current_start - pd.Timedelta(days=30)
    previous_end = current_start - pd.Timedelta(days=1)

    current_count = int(
        (
            (group["event_date"] >= current_start)
            & (group["event_date"] <= latest_date)
        ).sum()
    )

    previous_count = int(
        (
            (group["event_date"] >= previous_start)
            & (group["event_date"] <= previous_end)
        ).sum()
    )

    if previous_count == 0:
        percent_change = 100.0 if current_count > 0 else 0.0
    else:
        percent_change = ((current_count - previous_count) / previous_count) * 100

    if percent_change > 10:
        return "Increasing"

    if percent_change < -10:
        return "Decreasing"

    return "Stable"


def aggregate_arrests_by_tract(arrests):
    if arrests.empty:
        return pd.DataFrame(
            columns=[
                "tract_geoid",
                "total_arrests",
                "felony_arrests",
                "misdemeanor_arrests",
                "felony_share",
                "misdemeanor_share",
                "weekend_activity_share",
                "evening_night_activity_share",
                "most_common_offense",
                "most_common_arrest_type",
                "recent_activity_trend",
                "arrest_activity_share",
            ]
        )

    working = arrests[
        arrests["tract_geoid"].notna()
        & (arrests["tract_geoid"].astype(str) != "Not assigned")
    ].copy()

    total_study_area_arrests = len(working)

    working["is_felony"] = working["severity_label"] == "Felony"
    working["is_misdemeanor"] = working["severity_label"] == "Misdemeanor"
    working["is_weekend"] = working["event_weekday"].isin(["Saturday", "Sunday"])
    working["is_evening_night"] = working["time_period"].isin(["Evening", "Night"])

    grouped = (
        working
        .groupby("tract_geoid")
        .agg(
            total_arrests=("tract_geoid", "size"),
            felony_arrests=("is_felony", "sum"),
            misdemeanor_arrests=("is_misdemeanor", "sum"),
            weekend_arrests=("is_weekend", "sum"),
            evening_night_arrests=("is_evening_night", "sum"),
        )
        .reset_index()
    )

    offense_lookup = (
        working
        .groupby("tract_geoid")["Description"]
        .apply(safe_mode)
        .reset_index(name="most_common_offense")
    )

    arrest_type_lookup = (
        working
        .groupby("tract_geoid")["Arrest Type"]
        .apply(safe_mode)
        .reset_index(name="most_common_arrest_type")
    )

    trend_lookup = (
        working
        .groupby("tract_geoid")
        .apply(calculate_recent_activity_trend)
        .reset_index(name="recent_activity_trend")
    )

    grouped = grouped.merge(offense_lookup, on="tract_geoid", how="left")
    grouped = grouped.merge(arrest_type_lookup, on="tract_geoid", how="left")
    grouped = grouped.merge(trend_lookup, on="tract_geoid", how="left")

    grouped["felony_share"] = grouped.apply(
        lambda row: pct(row["felony_arrests"], row["total_arrests"]),
        axis=1,
    )

    grouped["misdemeanor_share"] = grouped.apply(
        lambda row: pct(row["misdemeanor_arrests"], row["total_arrests"]),
        axis=1,
    )

    grouped["weekend_activity_share"] = grouped.apply(
        lambda row: pct(row["weekend_arrests"], row["total_arrests"]),
        axis=1,
    )

    grouped["evening_night_activity_share"] = grouped.apply(
        lambda row: pct(row["evening_night_arrests"], row["total_arrests"]),
        axis=1,
    )

    grouped["arrest_activity_share"] = grouped.apply(
        lambda row: pct(row["total_arrests"], total_study_area_arrests),
        axis=1,
    )

    return grouped


def calculate_derived_metrics(enriched):
    enriched = enriched.copy()

    numeric_columns = [
        "total_population",
        "median_household_income",
        "poverty_rate",
        "unemployment_rate",
        "housing_vacancy_rate",
        "total_arrests",
        "felony_arrests",
        "misdemeanor_arrests",
        "tract_area_sq_mi",
    ]

    for column in numeric_columns:
        if column in enriched.columns:
            enriched[column] = pd.to_numeric(enriched[column], errors="coerce")

    if "total_population" in enriched.columns:
        enriched["arrests_per_1000_population"] = enriched.apply(
            lambda row: rate_per_1000(
                row.get("total_arrests", 0),
                row.get("total_population", 0),
            ),
            axis=1,
        )

        enriched["felony_arrests_per_1000_population"] = enriched.apply(
            lambda row: rate_per_1000(
                row.get("felony_arrests", 0),
                row.get("total_population", 0),
            ),
            axis=1,
        )

        enriched["population_density"] = enriched.apply(
            lambda row: round(row.get("total_population", 0) / row["tract_area_sq_mi"], 2)
            if pd.notna(row.get("total_population"))
            and pd.notna(row.get("tract_area_sq_mi"))
            and row.get("tract_area_sq_mi", 0) > 0
            else 0.0,
            axis=1,
        )
    else:
        enriched["arrests_per_1000_population"] = 0.0
        enriched["felony_arrests_per_1000_population"] = 0.0
        enriched["population_density"] = 0.0

    if "youth_population_share" not in enriched.columns:
        if "youth_population" in enriched.columns and "total_population" in enriched.columns:
            enriched["youth_population_share"] = enriched.apply(
                lambda row: pct(
                    row.get("youth_population", 0),
                    row.get("total_population", 0),
                ),
                axis=1,
            )
        else:
            enriched["youth_population_share"] = pd.NA

    if "senior_population_share" not in enriched.columns:
        if "senior_population" in enriched.columns and "total_population" in enriched.columns:
            enriched["senior_population_share"] = enriched.apply(
                lambda row: pct(
                    row.get("senior_population", 0),
                    row.get("total_population", 0),
                ),
                axis=1,
            )
        else:
            enriched["senior_population_share"] = pd.NA

    mean_arrests_per_1000 = enriched["arrests_per_1000_population"].mean()

    if pd.isna(mean_arrests_per_1000) or mean_arrests_per_1000 == 0:
        enriched["arrest_concentration_index"] = 0.0
    else:
        enriched["arrest_concentration_index"] = (
            enriched["arrests_per_1000_population"] / mean_arrests_per_1000
        ).round(2)

    return enriched


def build_enriched_tract_layer():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tracts = load_tract_geometries()
    arrests = load_arrests_with_tracts()
    acs = load_acs_demographics()

    tracts["tract_geoid"] = tracts["tract_geoid"].apply(normalize_geoid)
    arrests["tract_geoid"] = arrests["tract_geoid"].apply(normalize_geoid)
    acs["tract_geoid"] = acs["tract_geoid"].apply(normalize_geoid)

    arrest_summary = aggregate_arrests_by_tract(arrests)

    enriched = tracts.merge(
        acs,
        on="tract_geoid",
        how="left",
        validate="one_to_one",
    )

    enriched = enriched.merge(
        arrest_summary,
        on="tract_geoid",
        how="left",
        validate="one_to_one",
    )

    arrest_count_columns = [
        "total_arrests",
        "felony_arrests",
        "misdemeanor_arrests",
        "weekend_arrests",
        "evening_night_arrests",
    ]

    arrest_share_columns = [
        "felony_share",
        "misdemeanor_share",
        "weekend_activity_share",
        "evening_night_activity_share",
        "arrest_activity_share",
    ]

    for column in arrest_count_columns:
        if column in enriched.columns:
            enriched[column] = enriched[column].fillna(0).astype(int)

    for column in arrest_share_columns:
        if column in enriched.columns:
            enriched[column] = enriched[column].fillna(0.0)

    for column in ["most_common_offense", "most_common_arrest_type", "recent_activity_trend"]:
        if column in enriched.columns:
            enriched[column] = enriched[column].fillna("Not available")

    enriched = calculate_derived_metrics(enriched)
    enriched = enriched.to_crs(WEB_CRS)

    csv_output = pd.DataFrame(enriched.drop(columns="geometry"))
    csv_output.to_csv(OUTPUT_CSV_PATH, index=False)

    enriched.to_file(OUTPUT_GEOJSON_PATH, driver="GeoJSON")

    print_validation_report(
        tracts=tracts,
        acs=acs,
        arrests=arrests,
        arrest_summary=arrest_summary,
        enriched=enriched,
    )


def print_validation_report(tracts, acs, arrests, arrest_summary, enriched):
    print("")
    print("=" * 80)
    print("DURHAM TRACT ENRICHMENT VALIDATION REPORT")
    print("=" * 80)

    print(f"Input tract geometries: {len(tracts):,}")
    print(f"ACS demographic rows: {len(acs):,}")
    print(f"Arrest records used: {len(arrests):,}")
    print(f"Tracts with arrest summaries: {len(arrest_summary):,}")
    print(f"Enriched output tracts: {len(enriched):,}")
    print(f"Output CRS: {enriched.crs}")

    print("")
    print("Output files:")
    print(f"- {OUTPUT_GEOJSON_PATH}")
    print(f"- {OUTPUT_CSV_PATH}")

    duplicate_tracts = int(enriched["tract_geoid"].duplicated().sum())
    missing_output_geoids = int(enriched["tract_geoid"].isna().sum())

    print("")
    print("GEOID validation:")
    print(f"Duplicate output GEOIDs: {duplicate_tracts:,}")
    print(f"Missing output GEOIDs: {missing_output_geoids:,}")

    tract_geoids = set(tracts["tract_geoid"].dropna())
    acs_geoids = set(acs["tract_geoid"].dropna())
    arrest_geoids = set(arrest_summary["tract_geoid"].dropna())

    missing_acs_geoids = sorted(tract_geoids - acs_geoids)
    acs_not_in_tracts = sorted(acs_geoids - tract_geoids)
    arrest_geoids_not_in_tracts = sorted(arrest_geoids - tract_geoids)

    print(f"Tract GEOIDs missing ACS data: {len(missing_acs_geoids):,}")
    print(f"ACS GEOIDs not found in tract geometries: {len(acs_not_in_tracts):,}")
    print(f"Arrest summary GEOIDs not found in tract geometries: {len(arrest_geoids_not_in_tracts):,}")

    if missing_acs_geoids:
        print("Sample missing ACS GEOIDs:", missing_acs_geoids[:10])

    if acs_not_in_tracts:
        print("Sample ACS GEOIDs not in tracts:", acs_not_in_tracts[:10])

    if arrest_geoids_not_in_tracts:
        print("Sample arrest GEOIDs not in tracts:", arrest_geoids_not_in_tracts[:10])

    if "total_arrests" in enriched.columns:
        zero_arrest_tracts = int((enriched["total_arrests"] == 0).sum())
        print(f"Tracts with zero arrests: {zero_arrest_tracts:,}")

    demographic_columns_to_check = [
        "total_population",
        "median_household_income",
        "poverty_rate",
        "unemployment_rate",
        "housing_vacancy_rate",
    ]

    existing_demo_columns = [
        column for column in demographic_columns_to_check if column in enriched.columns
    ]

    print("")
    print("Missing demographic values:")
    if existing_demo_columns:
        for column in existing_demo_columns:
            print(f"- {column}: {int(enriched[column].isna().sum()):,}")
    else:
        print("No standard demographic fields found yet. Confirm ACS extraction field names.")

    summary_fields = [
        "total_population",
        "total_arrests",
        "arrests_per_1000_population",
        "felony_share",
        "poverty_rate",
        "unemployment_rate",
        "median_household_income",
    ]

    existing_summary_fields = [
        column for column in summary_fields if column in enriched.columns
    ]

    print("")
    print("Summary statistics:")
    if existing_summary_fields:
        print(enriched[existing_summary_fields].describe().round(2))
    else:
        print("No requested summary statistic fields found.")

    print("")
    print("Dashboard readiness:")
    print("- Choropleth ready: yes")
    print("- Hover popup ready: yes")
    print("- Click filtering key: tract_geoid")
    print("- Full tract geometries preserved: yes")
    print("- Tracts clipped to city boundary: no")
    print("- Intended use: monitoring and resilience intelligence, not enforcement prediction")

    print("=" * 80)
    print("TRACT ENRICHMENT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    build_enriched_tract_layer()