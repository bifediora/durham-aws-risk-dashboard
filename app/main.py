from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pyproj import Transformer


app = FastAPI(
    title="Durham Risk Intelligence Dashboard",
    description="A cloud hosted dashboard prototype for public safety risk intelligence.",
    version="0.2.3",
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "sample_arrests.csv"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

coordinate_transformer = Transformer.from_crs(
    "EPSG:2264",
    "EPSG:4326",
    always_xy=True,
)


def load_arrest_data():
    if not DATA_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(DATA_PATH)


def get_top_value(df, column_name):
    if column_name not in df.columns or df.empty:
        return "Not available"

    values = df[column_name].dropna()

    if values.empty:
        return "Not available"

    return str(values.value_counts().idxmax())


def count_matching_values(df, column_name, matching_value):
    if column_name not in df.columns or df.empty:
        return 0

    return int(
        df[column_name]
        .fillna("")
        .astype(str)
        .str.upper()
        .eq(matching_value.upper())
        .sum()
    )


def safe_string(value):
    if pd.isna(value):
        return "Not available"

    return str(value)


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


def is_within_durham_area(lat, lon):
    if lat is None or lon is None:
        return False

    min_lat = 35.80
    max_lat = 36.30
    min_lon = -79.15
    max_lon = -78.65

    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


@app.get("/", response_class=HTMLResponse)
def read_home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Durham Risk Intelligence Dashboard",
        "version": "0.2.3",
    }


@app.get("/dashboard", response_class=HTMLResponse)
def read_dashboard(request: Request):
    df = load_arrest_data()

    total_records = len(df)

    felony_count = count_matching_values(df, "F/M", "F")
    misdemeanor_count = count_matching_values(df, "F/M", "M")

    top_district = get_top_value(df, "District")
    top_arrest_type = get_top_value(df, "Arrest Type")
    top_description = get_top_value(df, "Description")

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "total_records": total_records,
            "felony_count": felony_count,
            "misdemeanor_count": misdemeanor_count,
            "top_district": top_district,
            "top_arrest_type": top_arrest_type,
            "top_description": top_description,
        },
    )


@app.get("/api/summary")
def api_summary():
    df = load_arrest_data()

    if df.empty:
        return {
            "status": "error",
            "message": "No sample arrest data found.",
            "expected_file": str(DATA_PATH),
        }

    return {
        "status": "success",
        "total_records": len(df),
        "felony_count": count_matching_values(df, "F/M", "F"),
        "misdemeanor_count": count_matching_values(df, "F/M", "M"),
        "top_district": get_top_value(df, "District"),
        "top_arrest_type": get_top_value(df, "Arrest Type"),
        "top_description": get_top_value(df, "Description"),
    }


@app.get("/api/records")
def api_records(limit: int = 5):
    df = load_arrest_data()

    if df.empty:
        return {
            "status": "error",
            "message": "No sample arrest data found.",
            "expected_file": str(DATA_PATH),
        }

    records = df.head(limit).fillna("Not available").to_dict(orient="records")

    return {
        "status": "success",
        "limit": limit,
        "records": records,
    }


@app.get("/api/map-points")
def api_map_points(limit: int = 250):
    df = load_arrest_data()

    if df.empty:
        return {
            "status": "error",
            "message": "No sample arrest data found.",
            "expected_file": str(DATA_PATH),
        }

    required_columns = ["X", "Y"]

    missing_columns = [
        column_name for column_name in required_columns if column_name not in df.columns
    ]

    if missing_columns:
        return {
            "status": "error",
            "message": "Missing required coordinate columns.",
            "missing_columns": missing_columns,
        }

    points = []
    excluded_points = 0

    for _, row in df.head(limit).iterrows():
        lon, lat = convert_xy_to_lon_lat(row.get("X"), row.get("Y"))

        if not is_within_durham_area(lat, lon):
            excluded_points += 1
            continue

        points.append(
            {
                "latitude": lat,
                "longitude": lon,
                "description": safe_string(row.get("Description")),
                "arrest_date": safe_string(row.get("Arrest Date")),
                "arrest_time": safe_string(row.get("Arrest Time")),
                "severity": safe_string(row.get("F/M")),
                "district": safe_string(row.get("District")),
                "beat": safe_string(row.get("Beat")),
                "tract": safe_string(row.get("Tract")),
            }
        )

    return {
        "status": "success",
        "limit": limit,
        "points_returned": len(points),
        "excluded_points": excluded_points,
        "points": points,
    }


@app.get("/api/by-district")
def api_by_district():
    df = load_arrest_data()

    if df.empty:
        return {
            "status": "error",
            "message": "No sample arrest data found.",
            "expected_file": str(DATA_PATH),
        }

    if "District" not in df.columns:
        return {
            "status": "error",
            "message": "Missing required column: District",
        }

    counts = (
        df["District"]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .reset_index()
    )

    counts.columns = ["district", "count"]

    return {
        "status": "success",
        "records": counts.to_dict(orient="records"),
    }


@app.get("/api/by-severity")
def api_by_severity():
    df = load_arrest_data()

    if df.empty:
        return {
            "status": "error",
            "message": "No sample arrest data found.",
            "expected_file": str(DATA_PATH),
        }

    if "F/M" not in df.columns:
        return {
            "status": "error",
            "message": "Missing required column: F/M",
        }

    severity_labels = {
        "F": "Felony",
        "M": "Misdemeanor",
    }

    counts = (
        df["F/M"]
        .fillna("Unknown")
        .astype(str)
        .str.upper()
        .map(lambda value: severity_labels.get(value, value))
        .value_counts()
        .reset_index()
    )

    counts.columns = ["severity", "count"]

    return {
        "status": "success",
        "records": counts.to_dict(orient="records"),
    }


@app.get("/api/top-offenses")
def api_top_offenses(limit: int = 10):
    df = load_arrest_data()

    if df.empty:
        return {
            "status": "error",
            "message": "No sample arrest data found.",
            "expected_file": str(DATA_PATH),
        }

    if "Description" not in df.columns:
        return {
            "status": "error",
            "message": "Missing required column: Description",
        }

    counts = (
        df["Description"]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .head(limit)
        .reset_index()
    )

    counts.columns = ["offense", "count"]

    return {
        "status": "success",
        "limit": limit,
        "records": counts.to_dict(orient="records"),
    }


@app.get("/api/by-hour")
def api_by_hour():
    df = load_arrest_data()

    if df.empty:
        return {
            "status": "error",
            "message": "No sample arrest data found.",
            "expected_file": str(DATA_PATH),
        }

    if "Arrest Time" not in df.columns:
        return {
            "status": "error",
            "message": "Missing required column: Arrest Time",
        }

    arrest_times = pd.to_datetime(
        df["Arrest Time"],
        errors="coerce",
    )

    hours = arrest_times.dt.hour.dropna().astype(int)

    if hours.empty:
        return {
            "status": "success",
            "records": [],
            "message": "No valid arrest time values found.",
        }

    hourly_counts = (
        hours
        .value_counts()
        .reindex(range(24), fill_value=0)
        .reset_index()
    )

    hourly_counts.columns = ["hour", "count"]

    hourly_counts["hour_label"] = hourly_counts["hour"].apply(
        lambda hour: pd.Timestamp(year=2000, month=1, day=1, hour=hour).strftime("%I %p").lstrip("0")
    )

    records = hourly_counts[["hour", "hour_label", "count"]].to_dict(orient="records")

    return {
        "status": "success",
        "records": records,
    }
