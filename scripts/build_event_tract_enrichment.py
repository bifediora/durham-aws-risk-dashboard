from pathlib import Path
import json
import os

import geopandas as gpd
import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent

TRACTS_GEOJSON_PATH = (
    PROJECT_ROOT
    / "app"
    / "static"
    / "geojson"
    / "durham_city_intersecting_tracts.geojson"
)

ARRESTS_JOIN_PATH = PROJECT_ROOT / "data" / "processed" / "arrests_with_tract_join.csv"

ACS_PRIMARY_PATH = PROJECT_ROOT / "data" / "processed" / "durham_acs_tract_demographics.csv"
ACS_COMPAT_PATH = PROJECT_ROOT / "data" / "processed" / "acs_durham_tract_demographics.csv"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
ARRESTS_OUTPUT_CSV = OUTPUT_DIR / "durham_arrests_tract_enriched.csv"
ARRESTS_OUTPUT_GEOJSON = OUTPUT_DIR / "durham_arrests_tract_enriched.geojson"
SHOOTINGS_OUTPUT_CSV = OUTPUT_DIR / "durham_shootings_tract_enriched.csv"
SHOOTINGS_OUTPUT_GEOJSON = OUTPUT_DIR / "durham_shootings_tract_enriched.geojson"
CHOROPLETH_CATALOG_PATH = OUTPUT_DIR / "durham_choropleth_metric_catalog.json"
REPORT_PATH = OUTPUT_DIR / "durham_event_tract_enrichment_validation_report.txt"

WEB_CRS = "EPSG:4326"
PROJECTED_CRS = "EPSG:2264"
ACS_YEAR = "2024"
ACS_ENDPOINT = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"
STATE_FIPS = "37"
COUNTY_FIPS = "063"


REQUIRED_ACS_COLUMNS = {
    "total_population": "B01003_001E",
    "median_household_income": "B19013_001E",
    "average_household_size": "B25010_001E",
    "bachelors_or_higher_rate": None,
    "white_non_hispanic_share": None,
    "black_non_hispanic_share": None,
    "hispanic_or_latino_share": None,
    "asian_non_hispanic_share": None,
    "american_indian_alaska_native_non_hispanic_share": None,
    "native_hawaiian_pacific_islander_non_hispanic_share": None,
    "other_race_non_hispanic_share": None,
    "two_or_more_races_non_hispanic_share": None,
    "poverty_rate": None,
    "housing_vacancy_rate": None,
    "youth_population_share": None,
}

ACS_FETCH_VARIABLES = {
    "B25010_001E": "average_household_size",
}

SHOOTINGS_CANDIDATE_PATHS = [
    PROJECT_ROOT / "data" / "processed" / "shootings_with_tract_join.csv",
    PROJECT_ROOT / "data" / "processed" / "durham_shootings_with_tract_join.csv",
    PROJECT_ROOT / "data" / "processed" / "shootings.csv",
    PROJECT_ROOT / "data" / "processed" / "shootings.xlsx",
    PROJECT_ROOT / "data" / "shootings.csv",
    PROJECT_ROOT / "data" / "shootings.xlsx",
    PROJECT_ROOT / "data" / "durham_shootings.csv",
    PROJECT_ROOT / "data" / "durham_shootings.xlsx",
]


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


def add_report_line(lines, text=""):
    print(text)
    lines.append(text)


def load_table(path):
    if path.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    return pd.read_csv(path, low_memory=False)


def load_tract_geometries():
    if not TRACTS_GEOJSON_PATH.exists():
        raise FileNotFoundError(f"Missing tract geometry layer: {TRACTS_GEOJSON_PATH}")

    tracts = gpd.read_file(TRACTS_GEOJSON_PATH)

    if tracts.crs is None:
        tracts = tracts.set_crs(WEB_CRS)

    tracts = tracts.to_crs(WEB_CRS)

    geoid_column = next(
        (
            column
            for column in ["GEOID", "GEOID20", "geoid", "tract_geoid"]
            if column in tracts.columns
        ),
        None,
    )

    name_column = next(
        (
            column
            for column in ["NAMELSAD", "NAME", "name", "tract_name"]
            if column in tracts.columns
        ),
        geoid_column,
    )

    if geoid_column is None:
        raise ValueError("Could not find a tract GEOID column in tract geometries.")

    tracts["tract_geoid"] = tracts[geoid_column].apply(normalize_geoid)
    tracts["tract_name"] = tracts[name_column].fillna("").astype(str)

    projected = tracts.to_crs(PROJECTED_CRS)
    tracts["tract_area_sq_m"] = projected.geometry.area
    tracts["tract_area_sq_mi"] = tracts["tract_area_sq_m"] / 2_589_988.110336

    return tracts[
        [
            "tract_geoid",
            "tract_name",
            "tract_area_sq_m",
            "tract_area_sq_mi",
            "geometry",
        ]
    ].copy()


def load_acs_demographics():
    if not ACS_PRIMARY_PATH.exists():
        raise FileNotFoundError(f"Missing ACS demographic file: {ACS_PRIMARY_PATH}")

    acs = pd.read_csv(ACS_PRIMARY_PATH, dtype={"GEOID": str, "tract_geoid": str})

    geoid_column = next(
        (
            column
            for column in ["tract_geoid", "GEOID", "geoid"]
            if column in acs.columns
        ),
        None,
    )

    if geoid_column is None:
        raise ValueError("Could not find a tract GEOID column in ACS data.")

    acs["tract_geoid"] = acs[geoid_column].apply(normalize_geoid)

    for column in acs.columns:
        if column in ["GEOID", "tract_geoid", "NAME", "state", "county", "tract"]:
            continue

        acs[column] = pd.to_numeric(acs[column], errors="coerce")

    return acs


def read_optional_env_key():
    env_path = PROJECT_ROOT / ".env"

    if env_path.exists() and not os.getenv("CENSUS_API_KEY"):
        for line in env_path.read_text().splitlines():
            if line.startswith("CENSUS_API_KEY="):
                os.environ["CENSUS_API_KEY"] = line.split("=", 1)[1].strip()
                break

    return os.getenv("CENSUS_API_KEY")


def fetch_missing_acs_variables(missing_columns):
    variable_codes = [
        REQUIRED_ACS_COLUMNS[column]
        for column in missing_columns
        if REQUIRED_ACS_COLUMNS.get(column)
    ]

    if not variable_codes:
        return pd.DataFrame()

    params = {
        "get": ",".join(["NAME"] + variable_codes),
        "for": "tract:*",
        "in": f"state:{STATE_FIPS} county:{COUNTY_FIPS}",
    }

    api_key = read_optional_env_key()

    if api_key:
        params["key"] = api_key

    try:
        response = requests.get(
            ACS_ENDPOINT,
            params=params,
            timeout=60,
            allow_redirects=False,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            "Census API request failed while retrieving missing ACS variables."
        ) from exc

    if response.status_code == 302:
        raise RuntimeError(
            "Census API redirected the request. Confirm CENSUS_API_KEY is available in .env."
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Census API returned a non-JSON response while retrieving missing ACS variables."
        ) from exc

    if not data or len(data) < 2:
        raise RuntimeError("Census API returned no ACS records for missing variables.")

    fetched = pd.DataFrame(data[1:], columns=data[0])
    fetched["state"] = fetched["state"].astype(str).str.zfill(2)
    fetched["county"] = fetched["county"].astype(str).str.zfill(3)
    fetched["tract"] = fetched["tract"].astype(str).str.zfill(6)
    fetched["tract_geoid"] = fetched["state"] + fetched["county"] + fetched["tract"]
    fetched["GEOID"] = fetched["tract_geoid"]
    fetched = fetched.rename(columns=ACS_FETCH_VARIABLES)

    for column in fetched.columns:
        if column in ["NAME", "state", "county", "tract", "tract_geoid", "GEOID"]:
            continue

        fetched[column] = pd.to_numeric(fetched[column], errors="coerce")
        fetched.loc[fetched[column] < 0, column] = pd.NA

    return fetched


def ensure_required_acs_columns(acs, report_lines):
    existing_columns = [column for column in REQUIRED_ACS_COLUMNS if column in acs.columns]
    missing_columns = [column for column in REQUIRED_ACS_COLUMNS if column not in acs.columns]

    add_report_line(report_lines, "ACS variable coverage:")
    add_report_line(report_lines, f"  Existing required columns: {len(existing_columns)}")
    add_report_line(report_lines, f"  Missing required columns: {len(missing_columns)}")

    for column in existing_columns:
        add_report_line(report_lines, f"    existing: {column}")

    for column in missing_columns:
        add_report_line(report_lines, f"    missing: {column}")

    fetchable_missing = [
        column
        for column in missing_columns
        if REQUIRED_ACS_COLUMNS.get(column)
    ]

    if not fetchable_missing:
        return acs, existing_columns, []

    add_report_line(
        report_lines,
        f"Retrieving missing ACS columns through Census API: {', '.join(fetchable_missing)}",
    )

    fetched = fetch_missing_acs_variables(fetchable_missing)

    fetched_columns = [
        column
        for column in fetchable_missing
        if column in fetched.columns
    ]

    acs = acs.merge(
        fetched[["tract_geoid"] + fetched_columns],
        on="tract_geoid",
        how="left",
        validate="one_to_one",
    )

    acs.to_csv(ACS_PRIMARY_PATH, index=False)
    acs.to_csv(ACS_COMPAT_PATH, index=False)

    return acs, existing_columns, fetched_columns


def detect_shootings_dataset():
    for path in SHOOTINGS_CANDIDATE_PATHS:
        if path.exists():
            return path

    return None


def normalize_event_dates(df, dataset_name):
    df = df.copy()

    date_candidates = [
        "event_date",
        "date",
        "Date",
        "OCCURRED_ON_DATE",
        "Incident Date",
        "IncidentDate",
        "Shooting Date",
        "Report Date",
        "Arrest Date",
    ]

    time_candidates = [
        "event_time",
        "time",
        "Time",
        "Incident Time",
        "IncidentTime",
        "Shooting Time",
        "Report Time",
        "Arrest Time",
    ]

    date_column = next((column for column in date_candidates if column in df.columns), None)
    time_column = next((column for column in time_candidates if column in df.columns), None)

    if date_column is None:
        df["event_date"] = pd.NaT
        df["event_datetime"] = pd.NaT
    elif time_column:
        combined = df[date_column].astype(str).str.strip() + " " + df[time_column].astype(str).str.strip()
        df["event_datetime"] = pd.to_datetime(combined, errors="coerce", format="mixed")
        df["event_date"] = pd.to_datetime(df[date_column], errors="coerce")
    else:
        df["event_date"] = pd.to_datetime(df[date_column], errors="coerce")
        df["event_datetime"] = df["event_date"]

    df["event_weekday"] = df["event_datetime"].dt.day_name()
    df["event_hour"] = df["event_datetime"].dt.hour

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

    df["time_period"] = df["event_hour"].apply(get_time_period)
    df["_dataset_name"] = dataset_name

    return df


def normalize_arrests(arrests):
    arrests = arrests.copy()
    arrests["tract_geoid"] = arrests["tract_geoid"].apply(normalize_geoid)

    if "inside_intersecting_tract" in arrests.columns:
        inside = (
            arrests["inside_intersecting_tract"]
            .fillna(False)
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes", "y"])
        )
        arrests = arrests[inside].copy()

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

    arrests = normalize_event_dates(arrests, "arrests")
    arrests = arrests[arrests["tract_geoid"].notna()].copy()

    return arrests


def infer_coordinate_columns(df):
    lon_candidates = ["longitude", "Longitude", "LONGITUDE", "lon", "Lon", "X", "x"]
    lat_candidates = ["latitude", "Latitude", "LATITUDE", "lat", "Lat", "Y", "y"]

    lon_column = next((column for column in lon_candidates if column in df.columns), None)
    lat_column = next((column for column in lat_candidates if column in df.columns), None)

    return lon_column, lat_column


def normalize_shootings(shootings, tracts):
    shootings = shootings.copy()

    geoid_column = next(
        (
            column
            for column in ["tract_geoid", "GEOID", "geoid", "TRACT_GEOID"]
            if column in shootings.columns
        ),
        None,
    )

    if geoid_column:
        shootings["tract_geoid"] = shootings[geoid_column].apply(normalize_geoid)
    else:
        lon_column, lat_column = infer_coordinate_columns(shootings)

        if lon_column is None or lat_column is None:
            raise ValueError(
                "Shootings dataset must contain tract_geoid/GEOID or recognizable coordinate columns."
            )

        shootings[lon_column] = pd.to_numeric(shootings[lon_column], errors="coerce")
        shootings[lat_column] = pd.to_numeric(shootings[lat_column], errors="coerce")
        valid = shootings[lon_column].notna() & shootings[lat_column].notna()

        source_crs = PROJECTED_CRS if lon_column.lower() == "x" or lat_column.lower() == "y" else WEB_CRS

        points = gpd.GeoDataFrame(
            shootings[valid].copy(),
            geometry=gpd.points_from_xy(
                shootings.loc[valid, lon_column],
                shootings.loc[valid, lat_column],
            ),
            crs=source_crs,
        ).to_crs(PROJECTED_CRS)

        tracts_projected = tracts.to_crs(PROJECTED_CRS)
        joined = gpd.sjoin(
            points,
            tracts_projected[["tract_geoid", "tract_name", "geometry"]],
            how="left",
            predicate="intersects",
        )

        joined_lookup = joined[["tract_geoid", "tract_name"]].copy()
        joined_lookup.index = points.index

        shootings.loc[joined_lookup.index, "tract_geoid"] = joined_lookup["tract_geoid"]

    shootings = normalize_event_dates(shootings, "shootings")
    shootings = shootings[shootings["tract_geoid"].notna()].copy()

    return shootings


def calculate_recent_activity_trend(group):
    valid_dates = group["event_date"].dropna()

    if valid_dates.empty:
        return "Stable"

    latest_date = valid_dates.max()
    current_start = latest_date - pd.Timedelta(days=29)
    previous_start = current_start - pd.Timedelta(days=30)
    previous_end = current_start - pd.Timedelta(days=1)

    current_count = int(((group["event_date"] >= current_start) & (group["event_date"] <= latest_date)).sum())
    previous_count = int(((group["event_date"] >= previous_start) & (group["event_date"] <= previous_end)).sum())

    if previous_count == 0:
        percent_change = 100.0 if current_count > 0 else 0.0
    else:
        percent_change = ((current_count - previous_count) / previous_count) * 100

    if percent_change > 10:
        return "Increasing"

    if percent_change < -10:
        return "Decreasing"

    return "Stable"


def aggregate_events_by_tract(events, dataset_name):
    prefix = "arrest" if dataset_name == "arrests" else "shooting"
    count_column = f"total_{dataset_name}"

    if events.empty:
        return pd.DataFrame(columns=["tract_geoid", count_column])

    working = events[events["tract_geoid"].notna()].copy()
    total_events = len(working)
    working["is_weekend"] = working["event_weekday"].isin(["Saturday", "Sunday"])
    working["is_evening_night"] = working["time_period"].isin(["Evening", "Night"])
    working["is_night"] = working["time_period"] == "Night"

    grouped = (
        working
        .groupby("tract_geoid")
        .agg(
            **{
                count_column: ("tract_geoid", "size"),
                f"{prefix}_weekend_events": ("is_weekend", "sum"),
                f"{prefix}_evening_night_events": ("is_evening_night", "sum"),
                f"{prefix}_night_events": ("is_night", "sum"),
            }
        )
        .reset_index()
    )

    trend_lookup = (
        working
        .groupby("tract_geoid")
        .apply(calculate_recent_activity_trend)
        .reset_index(name=f"{prefix}_recent_activity_trend")
    )

    grouped = grouped.merge(trend_lookup, on="tract_geoid", how="left")

    grouped[f"{prefix}_activity_share"] = grouped[count_column].apply(
        lambda value: pct(value, total_events)
    )

    grouped[f"{prefix}_weekend_share"] = grouped.apply(
        lambda row: pct(row[f"{prefix}_weekend_events"], row[count_column]),
        axis=1,
    )

    grouped[f"{prefix}_evening_night_share"] = grouped.apply(
        lambda row: pct(row[f"{prefix}_evening_night_events"], row[count_column]),
        axis=1,
    )

    grouped[f"{prefix}_night_share"] = grouped.apply(
        lambda row: pct(row[f"{prefix}_night_events"], row[count_column]),
        axis=1,
    )

    if dataset_name == "arrests":
        working["is_felony"] = working["severity_label"] == "Felony"
        working["is_misdemeanor"] = working["severity_label"] == "Misdemeanor"

        severity = (
            working
            .groupby("tract_geoid")
            .agg(
                felony_arrests=("is_felony", "sum"),
                misdemeanor_arrests=("is_misdemeanor", "sum"),
            )
            .reset_index()
        )

        grouped = grouped.merge(severity, on="tract_geoid", how="left")

        grouped["felony_share"] = grouped.apply(
            lambda row: pct(row["felony_arrests"], row[count_column]),
            axis=1,
        )

        grouped["misdemeanor_share"] = grouped.apply(
            lambda row: pct(row["misdemeanor_arrests"], row[count_column]),
            axis=1,
        )

        if "Description" in working.columns:
            offense_lookup = (
                working
                .groupby("tract_geoid")["Description"]
                .apply(safe_mode)
                .reset_index(name="most_common_offense")
            )
            grouped = grouped.merge(offense_lookup, on="tract_geoid", how="left")

        if "Arrest Type" in working.columns:
            type_lookup = (
                working
                .groupby("tract_geoid")["Arrest Type"]
                .apply(safe_mode)
                .reset_index(name="most_common_arrest_type")
            )
            grouped = grouped.merge(type_lookup, on="tract_geoid", how="left")

    return grouped


def build_enriched_layer(tracts, acs, event_summary, dataset_name):
    enriched = tracts.merge(
        acs,
        on="tract_geoid",
        how="left",
        validate="one_to_one",
    )

    enriched = enriched.merge(
        event_summary,
        on="tract_geoid",
        how="left",
        validate="one_to_one",
    )

    count_column = f"total_{dataset_name}"
    prefix = "arrest" if dataset_name == "arrests" else "shooting"

    for column in enriched.columns:
        if column.startswith(prefix) or column.startswith("total_") or column in [
            "felony_arrests",
            "misdemeanor_arrests",
        ]:
            if column.endswith("_trend"):
                enriched[column] = enriched[column].fillna("Not available")
            elif pd.api.types.is_numeric_dtype(enriched[column]):
                enriched[column] = enriched[column].fillna(0)

    if count_column not in enriched.columns:
        enriched[count_column] = 0

    enriched[count_column] = pd.to_numeric(enriched[count_column], errors="coerce").fillna(0).astype(int)
    enriched["total_population"] = pd.to_numeric(enriched["total_population"], errors="coerce")

    enriched[f"{dataset_name}_per_1000_population"] = enriched.apply(
        lambda row: rate_per_1000(row[count_column], row["total_population"]),
        axis=1,
    )

    enriched[f"{dataset_name}_density_per_sq_mi"] = enriched.apply(
        lambda row: round(row[count_column] / row["tract_area_sq_mi"], 2)
        if pd.notna(row.get("tract_area_sq_mi")) and row.get("tract_area_sq_mi", 0) > 0
        else 0.0,
        axis=1,
    )

    enriched["population_density"] = enriched.apply(
        lambda row: round(row["total_population"] / row["tract_area_sq_mi"], 2)
        if pd.notna(row.get("total_population"))
        and pd.notna(row.get("tract_area_sq_mi"))
        and row.get("tract_area_sq_mi", 0) > 0
        else 0.0,
        axis=1,
    )

    return enriched.to_crs(WEB_CRS)


def write_enriched_outputs(enriched, csv_path, geojson_path):
    pd.DataFrame(enriched.drop(columns="geometry")).to_csv(csv_path, index=False)
    enriched.to_file(geojson_path, driver="GeoJSON")


def build_metric_catalog(shootings_available):
    shared_context = [
        {
            "key": "total_population",
            "label": "Total population",
            "format": "count",
            "priority": "context",
        },
        {
            "key": "median_household_income",
            "label": "Median household income",
            "format": "currency",
            "priority": "context",
        },
        {
            "key": "average_household_size",
            "label": "Average household size",
            "format": "decimal",
            "priority": "context",
        },
        {
            "key": "bachelors_or_higher_rate",
            "label": "Bachelor's degree or higher",
            "format": "percent",
            "priority": "context",
        },
        {
            "key": "poverty_rate",
            "label": "Poverty rate",
            "format": "percent",
            "priority": "vulnerability",
        },
        {
            "key": "housing_vacancy_rate",
            "label": "Vacancy rate",
            "format": "percent",
            "priority": "vulnerability",
        },
        {
            "key": "youth_population_share",
            "label": "Population under 18",
            "format": "percent",
            "priority": "composition",
        },
        {
            "key": "senior_population_share",
            "label": "Population 65 and older",
            "format": "percent",
            "priority": "composition",
        },
        {
            "key": "no_high_school_diploma_rate",
            "label": "No high school diploma",
            "format": "percent",
            "priority": "context",
        },
        {
            "key": "white_non_hispanic_share",
            "label": "White population share",
            "format": "percent",
            "priority": "composition",
        },
        {
            "key": "black_non_hispanic_share",
            "label": "Black population share",
            "format": "percent",
            "priority": "composition",
        },
        {
            "key": "hispanic_or_latino_share",
            "label": "Hispanic or Latino population share",
            "format": "percent",
            "priority": "composition",
        },
        {
            "key": "asian_non_hispanic_share",
            "label": "Asian population share",
            "format": "percent",
            "priority": "composition",
        },
    ]

    catalog = {
        "public_facing_guidance": (
            "Use normalized rates and percentage-based contextual indicators for tract comparison. "
            "Raw event counts remain available for operational monitoring, but should not be the "
            "primary choropleth interpretation."
        ),
        "arrests": [
            {
                "key": "arrests_per_1000_population",
                "label": "Arrests per 1,000 population",
                "format": "rate",
                "priority": "primary",
            },
            {
                "key": "felony_share",
                "label": "Felony share",
                "format": "percent",
                "priority": "primary",
            },
            {
                "key": "total_arrests",
                "label": "Total arrests",
                "format": "count",
                "priority": "operational",
            },
        ] + shared_context,
        "shootings": [
            {
                "key": "shootings_per_1000_population",
                "label": "Shootings per 1,000 population",
                "format": "rate",
                "priority": "primary",
                "available": shootings_available,
            },
            {
                "key": "total_shootings",
                "label": "Total shootings",
                "format": "count",
                "priority": "operational",
                "available": shootings_available,
            },
        ] + shared_context,
    }

    CHOROPLETH_CATALOG_PATH.write_text(json.dumps(catalog, indent=2))


def validate_and_report(
    report_lines,
    tracts,
    acs,
    arrests,
    arrest_summary,
    arrests_enriched,
    shootings_path,
    shootings,
    shooting_summary,
    shootings_enriched,
    existing_acs_columns,
    fetched_acs_columns,
):
    add_report_line(report_lines)
    add_report_line(report_lines, "=" * 80)
    add_report_line(report_lines, "DURHAM EVENT TRACT ENRICHMENT VALIDATION REPORT")
    add_report_line(report_lines, "=" * 80)

    add_report_line(report_lines, f"Tract geometry file: {TRACTS_GEOJSON_PATH}")
    add_report_line(report_lines, f"Tract CRS: {tracts.crs}")
    add_report_line(report_lines, f"Tract count: {len(tracts):,}")
    add_report_line(report_lines, f"Unique tract GEOIDs: {tracts['tract_geoid'].nunique():,}")
    add_report_line(report_lines, f"Duplicate tract GEOIDs: {int(tracts['tract_geoid'].duplicated().sum()):,}")
    add_report_line(report_lines, f"Missing tract GEOIDs: {int(tracts['tract_geoid'].isna().sum()):,}")

    add_report_line(report_lines)
    add_report_line(report_lines, f"ACS demographic file: {ACS_PRIMARY_PATH}")
    add_report_line(report_lines, f"ACS records: {len(acs):,}")
    add_report_line(report_lines, f"ACS unique GEOIDs: {acs['tract_geoid'].nunique():,}")
    add_report_line(report_lines, f"ACS duplicate GEOIDs: {int(acs['tract_geoid'].duplicated().sum()):,}")
    add_report_line(report_lines, f"ACS columns already available: {', '.join(existing_acs_columns)}")
    add_report_line(
        report_lines,
        "ACS columns newly retrieved: "
        + (", ".join(fetched_acs_columns) if fetched_acs_columns else "none"),
    )

    missing_acs_geoids = sorted(set(tracts["tract_geoid"]) - set(acs["tract_geoid"]))
    add_report_line(report_lines, f"Tract GEOIDs missing from ACS: {len(missing_acs_geoids):,}")

    add_report_line(report_lines)
    add_report_line(report_lines, f"Arrests source: {ARRESTS_JOIN_PATH}")
    add_report_line(report_lines, f"Arrest records assigned to tracts: {len(arrests):,}")
    add_report_line(report_lines, f"Arrest tracts with events: {arrest_summary['tract_geoid'].nunique():,}")
    add_report_line(report_lines, f"Arrest enriched tract records: {len(arrests_enriched):,}")
    add_report_line(report_lines, f"Arrest output CSV: {ARRESTS_OUTPUT_CSV}")
    add_report_line(report_lines, f"Arrest output GeoJSON: {ARRESTS_OUTPUT_GEOJSON}")

    if shootings_path:
        add_report_line(report_lines)
        add_report_line(report_lines, f"Shootings source: {shootings_path}")
        add_report_line(report_lines, f"Shooting records assigned to tracts: {len(shootings):,}")
        add_report_line(report_lines, f"Shooting tracts with events: {shooting_summary['tract_geoid'].nunique():,}")
        add_report_line(report_lines, f"Shooting enriched tract records: {len(shootings_enriched):,}")
        add_report_line(report_lines, f"Shooting output CSV: {SHOOTINGS_OUTPUT_CSV}")
        add_report_line(report_lines, f"Shooting output GeoJSON: {SHOOTINGS_OUTPUT_GEOJSON}")
    else:
        add_report_line(report_lines)
        add_report_line(report_lines, "Shootings source: NOT FOUND")
        add_report_line(
            report_lines,
            "Expected one of: " + ", ".join(str(path.relative_to(PROJECT_ROOT)) for path in SHOOTINGS_CANDIDATE_PATHS),
        )
        add_report_line(
            report_lines,
            "Shootings outputs were not generated because no shootings dataset is currently available.",
        )

    add_report_line(report_lines)
    add_report_line(report_lines, "Key summary statistics:")
    summary_columns = [
        "total_population",
        "average_household_size",
        "median_household_income",
        "poverty_rate",
        "housing_vacancy_rate",
        "youth_population_share",
        "bachelors_or_higher_rate",
        "arrests_per_1000_population",
        "felony_share",
    ]

    if shootings_enriched is not None:
        summary_columns.append("shootings_per_1000_population")

    stats_source = arrests_enriched if shootings_enriched is None else shootings_enriched

    for column in summary_columns:
        if column not in stats_source.columns:
            continue

        values = pd.to_numeric(stats_source[column], errors="coerce")
        add_report_line(
            report_lines,
            f"  {column}: min={values.min():.2f}, median={values.median():.2f}, max={values.max():.2f}",
        )

    REPORT_PATH.write_text("\n".join(report_lines))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_lines = []

    add_report_line(report_lines, "Starting Durham event tract enrichment workflow.")
    add_report_line(report_lines, "Analytical principle: arrests and shootings remain separate event layers.")

    tracts = load_tract_geometries()
    acs = load_acs_demographics()
    acs, existing_acs_columns, fetched_acs_columns = ensure_required_acs_columns(acs, report_lines)

    if not ARRESTS_JOIN_PATH.exists():
        raise FileNotFoundError(f"Missing arrests tract join file: {ARRESTS_JOIN_PATH}")

    arrests_raw = pd.read_csv(ARRESTS_JOIN_PATH, low_memory=False, dtype={"tract_geoid": str})
    arrests = normalize_arrests(arrests_raw)
    arrest_summary = aggregate_events_by_tract(arrests, "arrests")
    arrests_enriched = build_enriched_layer(tracts, acs, arrest_summary, "arrests")
    write_enriched_outputs(arrests_enriched, ARRESTS_OUTPUT_CSV, ARRESTS_OUTPUT_GEOJSON)

    shootings_path = detect_shootings_dataset()
    shootings = None
    shooting_summary = None
    shootings_enriched = None

    if shootings_path:
        shootings_raw = load_table(shootings_path)
        shootings = normalize_shootings(shootings_raw, tracts)
        shooting_summary = aggregate_events_by_tract(shootings, "shootings")
        shootings_enriched = build_enriched_layer(tracts, acs, shooting_summary, "shootings")
        write_enriched_outputs(shootings_enriched, SHOOTINGS_OUTPUT_CSV, SHOOTINGS_OUTPUT_GEOJSON)

    build_metric_catalog(shootings_available=shootings_path is not None)

    validate_and_report(
        report_lines=report_lines,
        tracts=tracts,
        acs=acs,
        arrests=arrests,
        arrest_summary=arrest_summary,
        arrests_enriched=arrests_enriched,
        shootings_path=shootings_path,
        shootings=shootings,
        shooting_summary=shooting_summary,
        shootings_enriched=shootings_enriched,
        existing_acs_columns=existing_acs_columns,
        fetched_acs_columns=fetched_acs_columns,
    )

    add_report_line(report_lines)
    add_report_line(report_lines, f"Validation report saved to: {REPORT_PATH}")
    REPORT_PATH.write_text("\n".join(report_lines))


if __name__ == "__main__":
    main()
