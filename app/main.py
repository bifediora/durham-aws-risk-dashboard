from functools import lru_cache
from pathlib import Path
from typing import Optional
import json
import math

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pyproj import Transformer
from shapely.geometry import Point, Polygon, shape


app = FastAPI(
    title="Durham Risk Intelligence Dashboard",
    description="A cloud hosted monitoring dashboard for public safety risk intelligence.",
    version="0.3.6",
)

BASE_DIR = Path(__file__).resolve().parent.parent

PROCESSED_ARRESTS_PATH = BASE_DIR / "data" / "processed" / "arrests_with_tract_join.csv"
ARRESTS_ENRICHED_TRACTS_PATH = BASE_DIR / "data" / "processed" / "durham_arrests_tract_enriched.geojson"
LEGACY_ENRICHED_TRACTS_PATH = BASE_DIR / "data" / "processed" / "durham_tract_enriched.geojson"
ENRICHED_TRACTS_PATH = (
    ARRESTS_ENRICHED_TRACTS_PATH
    if ARRESTS_ENRICHED_TRACTS_PATH.exists()
    else LEGACY_ENRICHED_TRACTS_PATH
)
CHOROPLETH_CATALOG_PATH = BASE_DIR / "data" / "processed" / "durham_choropleth_metric_catalog.json"
NEIGHBORHOODS_WEB_PATH = BASE_DIR / "data" / "processed" / "durham_neighborhoods_web.geojson"

FULL_ARRESTS_PATH = BASE_DIR / "data" / "arrests.xlsx"
FULL_SHOOTINGS_PATH = BASE_DIR / "data" / "shootings.xlsx"
SAMPLE_ARRESTS_PATH = BASE_DIR / "data" / "sample_arrests.csv"

TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

coordinate_transformer = Transformer.from_crs(
    "EPSG:2264",
    "EPSG:4326",
    always_xy=True,
)


CHOROPLETH_ALLOWED_METRICS = {
    "total_arrests",
    "total_population",
    "arrest_activity_share",
    "arrests_per_1000_population",
    "felony_arrests_per_1000_population",
    "felony_share",
    "activity_density",
    "arrests_density_per_sq_mi",
    "weekend_activity_share",
    "evening_night_activity_share",
    "night_share",
    "poverty_rate",
    "unemployment_rate",
    "median_household_income",
    "average_household_size",
    "youth_population_share",
    "senior_population_share",
    "no_high_school_diploma_rate",
    "housing_vacancy_rate",
    "bachelors_or_higher_rate",
    "white_non_hispanic_share",
    "black_non_hispanic_share",
    "hispanic_or_latino_share",
    "asian_non_hispanic_share",
    "american_indian_alaska_native_non_hispanic_share",
    "native_hawaiian_pacific_islander_non_hispanic_share",
    "other_race_non_hispanic_share",
    "two_or_more_races_non_hispanic_share",
    "arrest_concentration_index",
    "population_density",
}


STATIC_ENRICHED_METRICS = {
    "poverty_rate",
    "unemployment_rate",
    "total_population",
    "median_household_income",
    "average_household_size",
    "youth_population_share",
    "senior_population_share",
    "no_high_school_diploma_rate",
    "housing_vacancy_rate",
    "bachelors_or_higher_rate",
    "white_non_hispanic_share",
    "black_non_hispanic_share",
    "hispanic_or_latino_share",
    "asian_non_hispanic_share",
    "american_indian_alaska_native_non_hispanic_share",
    "native_hawaiian_pacific_islander_non_hispanic_share",
    "other_race_non_hispanic_share",
    "two_or_more_races_non_hispanic_share",
    "arrest_concentration_index",
    "population_density",
}


def safe_string(value):
    if pd.isna(value):
        return "Not available"

    value_string = str(value).strip()

    if not value_string:
        return "Not available"

    return value_string


def safe_float(value):
    if pd.isna(value):
        return None

    try:
        float_value = float(value)
    except (TypeError, ValueError):
        return None

    if pd.isna(float_value):
        return None

    return float_value


def convert_xy_to_lon_lat(x_value, y_value):
    x = safe_float(x_value)
    y = safe_float(y_value)

    if x is None or y is None:
        return None, None

    try:
        lon, lat = coordinate_transformer.transform(x, y)
    except Exception:
        return None, None

    if pd.isna(lat) or pd.isna(lon):
        return None, None

    return lon, lat


def parse_selected_values(value: Optional[str]):
    if not value:
        return []

    values = [
        item.strip()
        for item in str(value).split(",")
        if item.strip() and item.strip().lower() != "all"
    ]

    return values


def normalize_tract_geoid(value):
    if value is None or pd.isna(value):
        return "Not assigned"

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "not assigned"}:
        return "Not assigned"

    if text.endswith(".0"):
        text = text[:-2]

    digits = "".join(character for character in text if character.isdigit())

    if len(digits) == 11:
        return digits

    if digits and len(digits) < 11:
        return digits.zfill(11)

    return text


def normalize_bool_series(series):
    if series.dtype == bool:
        return series

    return (
        series
        .fillna(False)
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes", "y"])
    )


def pct(numerator, denominator):
    if denominator == 0 or pd.isna(denominator):
        return 0.0

    return round((numerator / denominator) * 100, 1)


def ratio(numerator, denominator):
    if denominator == 0 or pd.isna(denominator):
        return 0.0

    return round(numerator / denominator, 2)


def rate_per_1000(numerator, denominator):
    if denominator == 0 or pd.isna(denominator):
        return 0.0

    return round((numerator / denominator) * 1000, 2)


def normalize_date_time(df):
    df = df.copy()

    if "Arrest Date" not in df.columns:
        df["event_date"] = pd.NaT
        df["event_datetime"] = pd.NaT
        return df

    arrest_date = df["Arrest Date"].astype(str).str.strip()

    if "Arrest Time" in df.columns:
        arrest_time = df["Arrest Time"].astype(str).str.strip()
    else:
        arrest_time = ""

    combined_datetime = arrest_date + " " + arrest_time

    df["event_datetime"] = pd.to_datetime(
        combined_datetime,
        errors="coerce",
    )

    df["event_date"] = pd.to_datetime(
        df["Arrest Date"],
        errors="coerce",
    )

    df["event_year"] = df["event_datetime"].dt.year
    df["event_month"] = df["event_datetime"].dt.month
    df["event_month_label"] = df["event_datetime"].dt.strftime("%b")
    df["event_weekday"] = df["event_datetime"].dt.day_name()
    df["event_hour"] = df["event_datetime"].dt.hour

    def get_season(month):
        if pd.isna(month):
            return "Unknown"

        month = int(month)

        if month in [12, 1, 2]:
            return "Winter"

        if month in [3, 4, 5]:
            return "Spring"

        if month in [6, 7, 8]:
            return "Summer"

        if month in [9, 10, 11]:
            return "Fall"

        return "Unknown"

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

    df["season"] = df["event_month"].apply(get_season)
    df["time_period"] = df["event_hour"].apply(get_time_period)

    return df


def normalize_arrests(df):
    df = df.copy()

    for column in ["District", "Beat", "Tract", "Description", "Arrest Type", "F/M"]:
        if column not in df.columns:
            df[column] = "Unknown"

    df["severity_label"] = (
        df["F/M"]
        .fillna("Unknown")
        .astype(str)
        .str.upper()
        .map({"F": "Felony", "M": "Misdemeanor"})
        .fillna(df["F/M"].fillna("Unknown").astype(str))
    )

    df = normalize_date_time(df)

    if "longitude" not in df.columns or "latitude" not in df.columns:
        coordinates = [
            convert_xy_to_lon_lat(row.get("X"), row.get("Y"))
            for _, row in df.iterrows()
        ]

        df["longitude"] = [item[0] for item in coordinates]
        df["latitude"] = [item[1] for item in coordinates]

    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")

    if "tract_geoid" not in df.columns:
        df["tract_geoid"] = "Not assigned"

    if "tract_name" not in df.columns:
        df["tract_name"] = "Not assigned"

    if "tract_area_sq_mi" not in df.columns:
        df["tract_area_sq_mi"] = pd.NA

    df["tract_geoid"] = df["tract_geoid"].apply(normalize_tract_geoid)
    df["tract_name"] = df["tract_name"].fillna("Not assigned").astype(str)
    df["tract_area_sq_mi"] = pd.to_numeric(df["tract_area_sq_mi"], errors="coerce")

    if "inside_intersecting_tract" in df.columns:
        df["inside_intersecting_tract"] = normalize_bool_series(
            df["inside_intersecting_tract"]
        )
    else:
        df["inside_intersecting_tract"] = df["tract_geoid"] != "Not assigned"

    df["dataset"] = "arrests"

    return df


@lru_cache(maxsize=1)
def load_arrest_data_cached():
    if PROCESSED_ARRESTS_PATH.exists():
        df = pd.read_csv(PROCESSED_ARRESTS_PATH, low_memory=False)
        source = str(PROCESSED_ARRESTS_PATH)
    elif FULL_ARRESTS_PATH.exists():
        df = pd.read_excel(FULL_ARRESTS_PATH)
        source = str(FULL_ARRESTS_PATH)
    elif SAMPLE_ARRESTS_PATH.exists():
        df = pd.read_csv(SAMPLE_ARRESTS_PATH)
        source = str(SAMPLE_ARRESTS_PATH)
    else:
        return pd.DataFrame(), "No data file found."

    df = normalize_arrests(df)

    if "inside_intersecting_tract" in df.columns:
        df = df[df["inside_intersecting_tract"]].copy()

    return df, source


def load_arrest_data():
    df, _ = load_arrest_data_cached()
    return df.copy()


def get_data_source():
    _, source = load_arrest_data_cached()
    return source


@lru_cache(maxsize=1)
def load_shooting_points_cached():
    if not FULL_SHOOTINGS_PATH.exists():
        return pd.DataFrame()

    try:
        shootings = pd.read_excel(FULL_SHOOTINGS_PATH)
    except Exception:
        return pd.DataFrame()

    if "X" not in shootings.columns or "Y" not in shootings.columns:
        return pd.DataFrame()

    shootings = shootings.copy()
    shootings["X"] = pd.to_numeric(shootings["X"], errors="coerce")
    shootings["Y"] = pd.to_numeric(shootings["Y"], errors="coerce")
    shootings = shootings[shootings["X"].notna() & shootings["Y"].notna()].copy()

    lon_lat_values = shootings.apply(
        lambda row: convert_xy_to_lon_lat(row["X"], row["Y"]),
        axis=1,
    )

    shootings["longitude"] = [value[0] for value in lon_lat_values]
    shootings["latitude"] = [value[1] for value in lon_lat_values]
    shootings = shootings[shootings["longitude"].notna() & shootings["latitude"].notna()].copy()

    return shootings


def load_shooting_points():
    return load_shooting_points_cached().copy()


@lru_cache(maxsize=1)
def load_enriched_tract_features():
    if not ENRICHED_TRACTS_PATH.exists():
        return []

    try:
        with ENRICHED_TRACTS_PATH.open("r", encoding="utf-8") as file:
            geojson = json.load(file)
    except Exception:
        return []

    features = []

    for feature in geojson.get("features", []):
        properties = feature.get("properties", {}) or {}
        geometry = feature.get("geometry")

        geoid = (
            properties.get("tract_geoid")
            or properties.get("GEOID")
            or properties.get("geoid")
            or "Unknown"
        )

        name = (
            properties.get("tract_name")
            or properties.get("NAME")
            or properties.get("name")
            or f"Tract {geoid}"
        )

        properties["tract_geoid"] = str(geoid)
        properties["geoid"] = str(geoid)
        properties["name"] = str(name)
        properties["tract_name"] = str(name)

        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
                "geoid": str(geoid),
                "name": str(name),
            }
        )

    return features


def get_enriched_tract_lookup():
    lookup = {}

    for feature in load_enriched_tract_features():
        lookup[feature["geoid"]] = feature["properties"]

    return lookup


@lru_cache(maxsize=1)
def load_choropleth_metric_catalog():
    fallback_catalog = {
        "public_facing_guidance": (
            "Prioritize normalized rates and percentage-based context for tract comparison."
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
            {
                "key": "poverty_rate",
                "label": "Poverty rate",
                "format": "percent",
                "priority": "vulnerability",
            },
            {
                "key": "median_household_income",
                "label": "Median household income",
                "format": "currency",
                "priority": "context",
            },
        ],
        "shootings": [],
    }

    if not CHOROPLETH_CATALOG_PATH.exists():
        return fallback_catalog

    try:
        with CHOROPLETH_CATALOG_PATH.open("r", encoding="utf-8") as file:
            catalog = json.load(file)
    except Exception:
        return fallback_catalog

    arrests_metrics = []

    for metric in catalog.get("arrests", []):
        key = metric.get("key")

        if key in CHOROPLETH_ALLOWED_METRICS:
            arrests_metrics.append(metric)

    catalog["arrests"] = arrests_metrics or fallback_catalog["arrests"]

    return catalog


@lru_cache(maxsize=1)
def load_neighborhood_context_geojson():
    if not NEIGHBORHOODS_WEB_PATH.exists():
        return {
            "type": "FeatureCollection",
            "features": [],
        }

    try:
        with NEIGHBORHOODS_WEB_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {
            "type": "FeatureCollection",
            "features": [],
        }


def apply_filters(
    df,
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    filtered = df.copy()

    selected_districts = parse_selected_values(districts)
    selected_severities = parse_selected_values(severities)
    selected_offenses = parse_selected_values(offenses)
    selected_arrest_types = parse_selected_values(arrest_types)
    selected_beats = parse_selected_values(beats)
    selected_tract_geoids = [
        normalize_tract_geoid(geoid)
        for geoid in parse_selected_values(tract_geoids)
    ]

    if selected_districts:
        filtered = filtered[
            filtered["District"].fillna("").astype(str).isin(selected_districts)
        ]

    if selected_severities:
        filtered = filtered[
            filtered["severity_label"].fillna("").astype(str).isin(selected_severities)
        ]

    if selected_offenses:
        filtered = filtered[
            filtered["Description"].fillna("").astype(str).isin(selected_offenses)
        ]

    if selected_arrest_types:
        filtered = filtered[
            filtered["Arrest Type"].fillna("").astype(str).isin(selected_arrest_types)
        ]

    if selected_beats:
        filtered = filtered[
            filtered["Beat"].fillna("").astype(str).isin(selected_beats)
        ]

    if selected_tract_geoids:
        filtered = filtered[
            filtered["tract_geoid"].apply(normalize_tract_geoid).isin(selected_tract_geoids)
        ]

    if start_date:
        start_timestamp = pd.to_datetime(start_date, errors="coerce")
        if not pd.isna(start_timestamp):
            filtered = filtered[filtered["event_date"] >= start_timestamp]

    if end_date:
        end_timestamp = pd.to_datetime(end_date, errors="coerce")
        if not pd.isna(end_timestamp):
            filtered = filtered[filtered["event_date"] <= end_timestamp]

    return filtered


def get_filtered_arrests(
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = load_arrest_data()

    if df.empty:
        return df

    return apply_filters(
        df,
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )


def get_top_value(df, column_name):
    if column_name not in df.columns or df.empty:
        return "Not available"

    values = df[column_name].dropna().astype(str)

    if values.empty:
        return "Not available"

    return str(values.value_counts().idxmax())


def count_active_hotspot_areas(df):
    if df.empty or "latitude" not in df.columns or "longitude" not in df.columns:
        return 0

    valid_points = df[["latitude", "longitude"]].dropna().copy()

    if valid_points.empty:
        return 0

    cell_size = 0.0125

    valid_points["lat_bin"] = (valid_points["latitude"] / cell_size).round() * cell_size
    valid_points["lon_bin"] = (valid_points["longitude"] / cell_size).round() * cell_size

    grouped = (
        valid_points
        .groupby(["lat_bin", "lon_bin"])
        .size()
        .reset_index(name="count")
    )

    if grouped.empty:
        return 0

    max_count = grouped["count"].max()
    hotspot_threshold = max(3, math.ceil(max_count * 0.60))

    return int((grouped["count"] >= hotspot_threshold).sum())


def get_population_for_geoids(geoids=None):
    selected_geoids = {str(geoid).zfill(11) for geoid in geoids or [] if str(geoid).strip()}
    total_population = 0.0

    for tract in load_enriched_tract_features():
        geoid = str(tract.get("geoid") or "").zfill(11)

        if selected_geoids and geoid not in selected_geoids:
            continue

        population = safe_float((tract.get("properties") or {}).get("total_population"))

        if population:
            total_population += population

    return total_population


def calculate_recent_activity_trend(df, reference_date=None):
    if df.empty or "event_date" not in df.columns:
        return {
            "label": "Stable",
            "symbol": "→",
            "percent_change": 0.0,
            "current_count": 0,
            "previous_count": 0,
        }

    valid_dates = df["event_date"].dropna()

    if valid_dates.empty:
        return {
            "label": "Stable",
            "symbol": "→",
            "percent_change": 0.0,
            "current_count": 0,
            "previous_count": 0,
        }

    latest_date = pd.to_datetime(reference_date, errors="coerce") if reference_date is not None else valid_dates.max()

    if pd.isna(latest_date):
        latest_date = valid_dates.max()

    current_start = latest_date - pd.Timedelta(days=29)
    previous_start = current_start - pd.Timedelta(days=30)
    previous_end = current_start - pd.Timedelta(days=1)

    current_count = int(
        ((df["event_date"] >= current_start) & (df["event_date"] <= latest_date)).sum()
    )

    previous_count = int(
        ((df["event_date"] >= previous_start) & (df["event_date"] <= previous_end)).sum()
    )

    if previous_count == 0:
        percent_change = 100.0 if current_count > 0 else 0.0
    else:
        percent_change = round(
            ((current_count - previous_count) / previous_count) * 100,
            1,
        )

    if percent_change > 10:
        label = "Increasing"
        symbol = "↑"
    elif percent_change < -10:
        label = "Decreasing"
        symbol = "↓"
    else:
        label = "Stable"
        symbol = "→"

    return {
        "label": label,
        "symbol": symbol,
        "percent_change": percent_change,
        "current_count": current_count,
        "previous_count": previous_count,
    }


def build_summary(df, baseline_total=None, rate_population=None, trend_reference_date=None):
    total_records = len(df)

    if baseline_total is None:
        baseline_total = total_records

    if rate_population is None:
        rate_population = get_population_for_geoids()

    felony_count = int((df["severity_label"] == "Felony").sum()) if not df.empty else 0
    misdemeanor_count = int((df["severity_label"] == "Misdemeanor").sum()) if not df.empty else 0

    weekend_count = 0
    night_count = 0

    if not df.empty and "event_weekday" in df.columns:
        weekend_count = int(df["event_weekday"].isin(["Saturday", "Sunday"]).sum())

    if not df.empty and "time_period" in df.columns:
        night_count = int((df["time_period"] == "Night").sum())

    active_hotspot_areas = count_active_hotspot_areas(df)
    recent_activity_trend = calculate_recent_activity_trend(
        df,
        reference_date=trend_reference_date,
    )

    return {
        "total_records": total_records,
        "baseline_total_records": baseline_total,
        "arrest_activity_share": pct(total_records, baseline_total),
        "felony_count": felony_count,
        "misdemeanor_count": misdemeanor_count,
        "felony_share": pct(felony_count, total_records),
        "misdemeanor_share": pct(misdemeanor_count, total_records),
        "felony_to_misdemeanor_ratio": ratio(felony_count, misdemeanor_count),
        "weekend_count": weekend_count,
        "weekend_share": pct(weekend_count, total_records),
        "night_count": night_count,
        "night_share": pct(night_count, total_records),
        "active_hotspot_areas": active_hotspot_areas,
        "arrest_rate_per_1000_population": rate_per_1000(total_records, rate_population),
        "arrest_rate_population": int(rate_population or 0),
        "recent_activity_trend_label": recent_activity_trend["label"],
        "recent_activity_trend_symbol": recent_activity_trend["symbol"],
        "recent_activity_trend_pct": recent_activity_trend["percent_change"],
        "recent_current_count": recent_activity_trend["current_count"],
        "recent_previous_count": recent_activity_trend["previous_count"],
        "top_district": get_top_value(df, "District"),
        "top_arrest_type": get_top_value(df, "Arrest Type"),
        "top_description": get_top_value(df, "Description"),
        "top_season": get_top_value(df, "season"),
        "top_time_period": get_top_value(df, "time_period"),
    }


def make_records_from_counts(series, label_name, count_name="count", limit=None):
    counts = (
        series
        .fillna("Unknown")
        .astype(str)
        .value_counts()
    )

    if limit:
        counts = counts.head(limit)

    records = counts.reset_index()
    records.columns = [label_name, count_name]

    return records.to_dict(orient="records")


def build_query_context(
    districts=None,
    severities=None,
    offenses=None,
    arrest_types=None,
    beats=None,
    tract_geoids=None,
):
    return {
        "districts": parse_selected_values(districts),
        "severities": parse_selected_values(severities),
        "offenses": parse_selected_values(offenses),
        "arrest_types": parse_selected_values(arrest_types),
        "beats": parse_selected_values(beats),
        "tract_geoids": parse_selected_values(tract_geoids),
    }


def build_dynamic_tract_summary_lookup(df, baseline_total=None):
    if df.empty or "tract_geoid" not in df.columns:
        return {}

    working = df[
        df["tract_geoid"].notna()
        & (df["tract_geoid"].astype(str) != "Not assigned")
    ].copy()

    if working.empty:
        return {}

    if baseline_total is None:
        baseline_total = len(working)

    working["is_felony"] = working["severity_label"] == "Felony"
    working["is_misdemeanor"] = working["severity_label"] == "Misdemeanor"
    working["is_weekend"] = working["event_weekday"].isin(["Saturday", "Sunday"])
    working["is_evening_night"] = working["time_period"].isin(["Evening", "Night"])
    working["is_night"] = working["time_period"] == "Night"

    grouped = (
        working
        .groupby("tract_geoid")
        .agg(
            total_arrests=("tract_geoid", "size"),
            felony_count=("is_felony", "sum"),
            misdemeanor_count=("is_misdemeanor", "sum"),
            weekend_count=("is_weekend", "sum"),
            evening_night_count=("is_evening_night", "sum"),
            night_count=("is_night", "sum"),
            tract_name=("tract_name", "first"),
            tract_area_sq_mi=("tract_area_sq_mi", "first"),
        )
        .reset_index()
    )

    enriched_lookup = get_enriched_tract_lookup()

    lookup = {}

    for _, row in grouped.iterrows():
        geoid = str(row["tract_geoid"])
        enriched = enriched_lookup.get(geoid, {})

        population = safe_float(enriched.get("total_population"))
        area_sq_mi = safe_float(row.get("tract_area_sq_mi")) or safe_float(enriched.get("tract_area_sq_mi")) or 0.0

        total_arrests = int(row["total_arrests"])
        felony_count = int(row["felony_count"])
        misdemeanor_count = int(row["misdemeanor_count"])
        weekend_count = int(row["weekend_count"])
        evening_night_count = int(row["evening_night_count"])
        night_count = int(row["night_count"])

        lookup[geoid] = {
            "total_arrests": total_arrests,
            "felony_count": felony_count,
            "misdemeanor_count": misdemeanor_count,
            "weekend_count": weekend_count,
            "evening_night_count": evening_night_count,
            "night_count": night_count,
            "felony_share": pct(felony_count, total_arrests),
            "misdemeanor_share": pct(misdemeanor_count, total_arrests),
            "weekend_activity_share": pct(weekend_count, total_arrests),
            "evening_night_activity_share": pct(evening_night_count, total_arrests),
            "night_share": pct(night_count, total_arrests),
            "arrest_activity_share": pct(total_arrests, baseline_total),
            "arrests_per_1000_population": rate_per_1000(total_arrests, population),
            "felony_arrests_per_1000_population": rate_per_1000(felony_count, population),
            "activity_density": round(total_arrests / area_sq_mi, 2) if area_sq_mi else 0.0,
            "tract_name": safe_string(row.get("tract_name")),
            "tract_area_sq_mi": area_sq_mi,
        }

    return lookup


def get_metric_value(properties, dynamic_summary, metric):
    geoid = str(properties.get("tract_geoid") or properties.get("geoid") or "")

    if metric == "no_high_school_diploma_rate":
        high_school_or_higher_rate = safe_float(properties.get("high_school_or_higher_rate"))

        if high_school_or_higher_rate is None:
            return 0.0

        return max(0.0, round(100.0 - high_school_or_higher_rate, 1))

    if metric in STATIC_ENRICHED_METRICS:
        return safe_float(properties.get(metric)) or 0.0

    if geoid in dynamic_summary:
        return dynamic_summary[geoid].get(metric, 0.0)

    return safe_float(properties.get(metric)) or 0.0


def build_choropleth_geojson(df, metric="total_arrests"):
    if metric not in CHOROPLETH_ALLOWED_METRICS:
        metric = "total_arrests"

    tract_features = load_enriched_tract_features()
    dynamic_summary = build_dynamic_tract_summary_lookup(
        df,
        baseline_total=len(df),
    )

    features = []

    for tract in tract_features:
        geoid = tract["geoid"]
        properties = dict(tract["properties"])

        dynamic_values = dynamic_summary.get(geoid, {})

        for key, value in dynamic_values.items():
            properties[key] = value

        properties["geoid"] = geoid
        properties["tract_geoid"] = geoid
        properties["name"] = tract["name"]
        properties["tract_name"] = tract["name"]

        selected_metric_value = get_metric_value(properties, dynamic_summary, metric)

        properties["selected_metric"] = metric
        properties["selected_metric_value"] = selected_metric_value
        properties["tract_context"] = (
            "Census tract intersecting Durham municipal boundary. "
            "Full tract geometry preserved."
        )

        features.append(
            {
                "type": "Feature",
                "geometry": tract["geometry"],
                "properties": properties,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@app.get("/", response_class=HTMLResponse)
def read_home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Durham Risk Intelligence Dashboard",
        "version": "0.3.6",
    }


@app.get("/dashboard", response_class=HTMLResponse)
def read_dashboard(request: Request):
    df = load_arrest_data()
    summary = build_summary(df)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "total_records": summary["total_records"],
            "felony_count": summary["felony_count"],
            "misdemeanor_count": summary["misdemeanor_count"],
            "top_district": summary["top_district"],
            "top_arrest_type": summary["top_arrest_type"],
            "top_description": summary["top_description"],
            "data_source": get_data_source(),
        },
    )


@app.get("/api/filter-options")
def api_filter_options():
    df = load_arrest_data()

    if df.empty:
        return {
            "status": "error",
            "message": "No arrest data found.",
            "expected_files": [
                str(PROCESSED_ARRESTS_PATH),
                str(ENRICHED_TRACTS_PATH),
                str(FULL_ARRESTS_PATH),
                str(SAMPLE_ARRESTS_PATH),
            ],
        }

    min_date = None
    max_date = None

    if "event_date" in df.columns:
        valid_dates = df["event_date"].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().strftime("%Y-%m-%d")
            max_date = valid_dates.max().strftime("%Y-%m-%d")

    return {
        "status": "success",
        "data_source": get_data_source(),
        "records_in_study_area": len(df),
        "date_range": {
            "min": min_date,
            "max": max_date,
        },
        "enriched_tract_layer": str(ENRICHED_TRACTS_PATH),
    }


@app.get("/api/choropleth-metrics")
def api_choropleth_metrics():
    catalog = load_choropleth_metric_catalog()

    return {
        "status": "success",
        "default_metric": "arrests_per_1000_population",
        "catalog": catalog,
        "active_event_layer": "arrests",
        "available_event_layers": {
            "arrests": True,
            "shootings": any(
                metric.get("available", False)
                for metric in catalog.get("shootings", [])
                if isinstance(metric, dict)
            ),
        },
    }


@app.get("/api/neighborhoods")
def api_neighborhoods():
    geojson = load_neighborhood_context_geojson()

    return {
        "status": "success",
        "role": "context_layer",
        "statistical_layer": "census_tracts",
        "geojson": geojson,
    }


@app.post("/api/spatial-selection")
async def api_spatial_selection(request: Request):
    payload = await request.json()
    coordinates = payload.get("coordinates", [])
    target_layer = str(payload.get("target_layer") or "tracts").lower()

    if target_layer not in {"points", "tracts", "neighborhoods"}:
        target_layer = "tracts"

    if not isinstance(coordinates, list) or len(coordinates) < 3:
        return {
            "status": "error",
            "message": "Selection polygon requires at least three coordinates.",
        }

    polygon_points = []

    for coordinate in coordinates:
        if not isinstance(coordinate, list) or len(coordinate) < 2:
            continue

        lon = safe_float(coordinate[0])
        lat = safe_float(coordinate[1])

        if lon is None or lat is None:
            continue

        polygon_points.append((lon, lat))

    if len(polygon_points) < 3:
        return {
            "status": "error",
            "message": "Selection polygon coordinates were invalid.",
        }

    if polygon_points[0] != polygon_points[-1]:
        polygon_points.append(polygon_points[0])

    selection_polygon = Polygon(polygon_points)

    if selection_polygon.is_empty or not selection_polygon.is_valid:
        return {
            "status": "error",
            "message": "Selection polygon is empty or invalid.",
        }

    selected_tract_geoids = set()

    if target_layer == "tracts":
        for feature in load_enriched_tract_features():
            geometry = feature.get("geometry")

            if not geometry:
                continue

            try:
                tract_geometry = shape(geometry)
            except Exception:
                continue

            if tract_geometry.intersects(selection_polygon):
                selected_tract_geoids.add(str(feature["geoid"]))

    arrests = load_arrest_data()

    if not arrests.empty and {"longitude", "latitude"}.issubset(arrests.columns):
        arrest_mask = arrests.apply(
            lambda row: selection_polygon.contains(
                Point(float(row["longitude"]), float(row["latitude"]))
            )
            if pd.notna(row.get("longitude")) and pd.notna(row.get("latitude"))
            else False,
            axis=1,
        )
        selected_arrests = arrests[arrest_mask].copy()
    else:
        selected_arrests = pd.DataFrame()

    if target_layer == "points" and not selected_arrests.empty and "tract_geoid" in selected_arrests.columns:
        selected_tract_geoids.update(
            selected_arrests["tract_geoid"]
            .dropna()
            .astype(str)
            .map(lambda value: value.zfill(11))
            .tolist()
        )

    selected_neighborhood_names = set()

    if target_layer == "neighborhoods":
        neighborhoods_geojson = load_neighborhood_context_geojson()

        for feature in neighborhoods_geojson.get("features", []):
            geometry = feature.get("geometry")

            if not geometry:
                continue

            try:
                neighborhood_geometry = shape(geometry)
            except Exception:
                continue

            if not neighborhood_geometry.intersects(selection_polygon):
                continue

            properties = feature.get("properties") or {}
            neighborhood_name = (
                properties.get("neighborhood_name")
                or properties.get("name")
                or properties.get("Name")
            )

            if neighborhood_name:
                selected_neighborhood_names.add(str(neighborhood_name))

    shootings = load_shooting_points()

    if not shootings.empty:
        shooting_mask = shootings.apply(
            lambda row: selection_polygon.contains(
                Point(float(row["longitude"]), float(row["latitude"]))
            )
            if pd.notna(row.get("longitude")) and pd.notna(row.get("latitude"))
            else False,
            axis=1,
        )
        selected_shootings = shootings[shooting_mask].copy()
    else:
        selected_shootings = pd.DataFrame()

    return {
        "status": "success",
        "target_layer": target_layer,
        "tract_geoids": sorted(selected_tract_geoids),
        "tract_count": len(selected_tract_geoids),
        "neighborhood_names": sorted(selected_neighborhood_names),
        "neighborhood_count": len(selected_neighborhood_names),
        "arrest_point_count": int(len(selected_arrests)),
        "shooting_point_count": int(len(selected_shootings)),
    }


@app.get("/api/summary")
def api_summary(
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )

    baseline_df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=None,
        start_date=start_date,
        end_date=end_date,
    )

    selected_tract_geoids = parse_selected_values(tract_geoids)
    rate_population = get_population_for_geoids(selected_tract_geoids or None)
    trend_reference_date = None

    if "event_date" in baseline_df.columns and not baseline_df.empty:
        trend_reference_date = baseline_df["event_date"].dropna().max()

    return {
        "status": "success",
        "summary": build_summary(
            df,
            baseline_total=len(baseline_df),
            rate_population=rate_population,
            trend_reference_date=trend_reference_date,
        ),
        "query_context": build_query_context(
            districts=districts,
            severities=severities,
            offenses=offenses,
            arrest_types=arrest_types,
            beats=beats,
            tract_geoids=tract_geoids,
        ),
    }


@app.get("/api/choropleth")
def api_choropleth(
    metric: str = "total_arrests",
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    if metric not in CHOROPLETH_ALLOWED_METRICS:
        metric = "total_arrests"

    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=None,
        start_date=start_date,
        end_date=end_date,
    )

    choropleth = build_choropleth_geojson(df, metric=metric)

    return {
        "status": "success",
        "metric": metric,
        "geojson": choropleth,
        "query_context": build_query_context(
            districts=districts,
            severities=severities,
            offenses=offenses,
            arrest_types=arrest_types,
            beats=beats,
            tract_geoids=tract_geoids,
        ),
    }


@app.get("/api/records")
def api_records(
    limit: int = 25,
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )

    if df.empty:
        return {
            "status": "success",
            "limit": limit,
            "records": [],
            "records_returned": 0,
            "total_matching_records": 0,
        }

    columns = [
        "Arrest Number",
        "Arrest Date",
        "Arrest Time",
        "Arrest Type",
        "Description",
        "severity_label",
        "District",
        "Beat",
        "Tract",
        "tract_geoid",
        "tract_name",
        "Location of Arrest",
    ]

    available_columns = [column for column in columns if column in df.columns]

    records = (
        df[available_columns]
        .head(limit)
        .fillna("Not available")
        .to_dict(orient="records")
    )

    return {
        "status": "success",
        "limit": limit,
        "records": records,
        "records_returned": len(records),
        "total_matching_records": len(df),
    }


@app.get("/api/map-points")
def api_map_points(
    limit: int = 3000,
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )

    if df.empty:
        return {
            "status": "success",
            "limit": limit,
            "points_returned": 0,
            "points": [],
        }

    points = []

    for _, row in df.head(limit).iterrows():
        lat = safe_float(row.get("latitude"))
        lon = safe_float(row.get("longitude"))

        if lat is None or lon is None:
            continue

        points.append(
            {
                "latitude": lat,
                "longitude": lon,
                "description": safe_string(row.get("Description")),
                "arrest_date": safe_string(row.get("Arrest Date")),
                "arrest_time": safe_string(row.get("Arrest Time")),
                "severity": safe_string(row.get("severity_label")),
                "district": safe_string(row.get("District")),
                "beat": safe_string(row.get("Beat")),
                "tract": safe_string(row.get("tract_geoid")),
                "tract_name": safe_string(row.get("tract_name")),
                "arrest_type": safe_string(row.get("Arrest Type")),
                "location": safe_string(row.get("Location of Arrest")),
            }
        )

    return {
        "status": "success",
        "limit": limit,
        "points_returned": len(points),
        "points": points,
    }


def get_hex_center(lon, lat, size):
    q = (math.sqrt(3) / 3 * lon - 1 / 3 * lat) / size
    r = (2 / 3 * lat) / size

    rq = round(q)
    rr = round(r)

    center_lon = size * math.sqrt(3) * (rq + rr / 2)
    center_lat = size * 1.5 * rr

    return center_lon, center_lat


@app.get("/api/map-aggregation")
def api_map_aggregation(
    mode: str = "hex",
    limit: int = 8000,
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )

    if df.empty:
        return {
            "status": "success",
            "mode": mode,
            "cells": [],
        }

    valid_points = (
        df[["latitude", "longitude"]]
        .dropna()
        .head(limit)
        .copy()
    )

    if valid_points.empty:
        return {
            "status": "success",
            "mode": mode,
            "cells": [],
        }

    hex_size = 0.014

    centers = valid_points.apply(
        lambda row: get_hex_center(row["longitude"], row["latitude"], hex_size),
        axis=1,
    )

    valid_points["lon_bin"] = [center[0] for center in centers]
    valid_points["lat_bin"] = [center[1] for center in centers]

    grouped = (
        valid_points
        .groupby(["lat_bin", "lon_bin"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    max_count = int(grouped["count"].max()) if not grouped.empty else 0

    cells = []

    for _, row in grouped.iterrows():
        lat = float(row["lat_bin"])
        lon = float(row["lon_bin"])
        count = int(row["count"])

        cells.append(
            {
                "latitude": lat,
                "longitude": lon,
                "count": count,
                "max_count": max_count,
                "cell_size": hex_size,
                "intensity": round(count / max_count, 3) if max_count else 0,
            }
        )

    return {
        "status": "success",
        "mode": mode,
        "cells": cells,
        "max_count": max_count,
        "total_points_aggregated": len(valid_points),
    }


@app.get("/api/by-district")
def api_by_district(
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )

    if df.empty:
        return {"status": "success", "records": []}

    records = make_records_from_counts(df["District"], "district")

    return {"status": "success", "records": records}


@app.get("/api/by-severity")
def api_by_severity(
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )

    if df.empty:
        return {"status": "success", "records": []}

    records = make_records_from_counts(df["severity_label"], "severity")

    return {"status": "success", "records": records}


@app.get("/api/top-offenses")
def api_top_offenses(
    limit: int = 10,
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )

    if df.empty:
        return {"status": "success", "limit": limit, "records": []}

    records = make_records_from_counts(df["Description"], "offense", limit=limit)

    return {"status": "success", "limit": limit, "records": records}


@app.get("/api/by-hour")
def api_by_hour(
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )

    if df.empty or "event_hour" not in df.columns:
        return {"status": "success", "records": []}

    hours = df["event_hour"].dropna().astype(int)

    hourly_counts = (
        hours
        .value_counts()
        .reindex(range(24), fill_value=0)
        .reset_index()
    )

    hourly_counts.columns = ["hour", "count"]

    hourly_counts["hour_label"] = hourly_counts["hour"].apply(
        lambda hour: pd.Timestamp(
            year=2000,
            month=1,
            day=1,
            hour=hour,
        ).strftime("%I %p").lstrip("0")
    )

    records = hourly_counts[["hour", "hour_label", "count"]].to_dict(orient="records")

    return {"status": "success", "records": records}


@app.get("/api/by-month")
def api_by_month(
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )

    if df.empty or "event_month" not in df.columns:
        return {"status": "success", "records": []}

    month_order = list(range(1, 13))

    monthly_counts = (
        df["event_month"]
        .dropna()
        .astype(int)
        .value_counts()
        .reindex(month_order, fill_value=0)
        .reset_index()
    )

    monthly_counts.columns = ["month", "count"]

    monthly_counts["month_label"] = monthly_counts["month"].apply(
        lambda month: pd.Timestamp(year=2000, month=month, day=1).strftime("%b")
    )

    records = monthly_counts[["month", "month_label", "count"]].to_dict(orient="records")

    return {"status": "success", "records": records}


@app.get("/api/by-weekday")
def api_by_weekday(
    districts: Optional[str] = None,
    severities: Optional[str] = None,
    offenses: Optional[str] = None,
    arrest_types: Optional[str] = None,
    beats: Optional[str] = None,
    tract_geoids: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    df = get_filtered_arrests(
        districts=districts,
        severities=severities,
        offenses=offenses,
        arrest_types=arrest_types,
        beats=beats,
        tract_geoids=tract_geoids,
        start_date=start_date,
        end_date=end_date,
    )

    if df.empty or "event_weekday" not in df.columns:
        return {"status": "success", "records": []}

    weekday_order = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]

    weekday_counts = (
        df["event_weekday"]
        .dropna()
        .astype(str)
        .value_counts()
        .reindex(weekday_order, fill_value=0)
        .reset_index()
    )

    weekday_counts.columns = ["weekday", "count"]

    records = weekday_counts.to_dict(orient="records")

    return {"status": "success", "records": records}
