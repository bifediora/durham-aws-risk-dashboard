from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

FULL_ARRESTS_PATH = PROJECT_ROOT / "data" / "arrests.xlsx"
SAMPLE_ARRESTS_PATH = PROJECT_ROOT / "data" / "sample_arrests.csv"

TRACTS_PATH = PROJECT_ROOT / "app" / "static" / "geojson" / "durham_city_intersecting_tracts.geojson"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "arrests_with_tract_join.csv"

SOURCE_CRS = "EPSG:2264"
WEB_CRS = "EPSG:4326"


def load_arrest_data():
    if FULL_ARRESTS_PATH.exists():
        print(f"Loading full arrest dataset: {FULL_ARRESTS_PATH}")
        return pd.read_excel(FULL_ARRESTS_PATH)

    if SAMPLE_ARRESTS_PATH.exists():
        print(f"Loading sample arrest dataset: {SAMPLE_ARRESTS_PATH}")
        return pd.read_csv(SAMPLE_ARRESTS_PATH)

    raise FileNotFoundError(
        "No arrest dataset found. Expected data/arrests.xlsx or data/sample_arrests.csv"
    )


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


def normalize_arrest_attributes(df):
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

    return df


def prepare_arrest_points(df):
    if "X" not in df.columns or "Y" not in df.columns:
        raise ValueError("Arrest data must include X and Y coordinate columns.")

    working = df.copy()

    working["X"] = pd.to_numeric(working["X"], errors="coerce")
    working["Y"] = pd.to_numeric(working["Y"], errors="coerce")

    working["_source_row_id"] = range(len(working))

    valid_coordinates = working["X"].notna() & working["Y"].notna()

    points = gpd.GeoDataFrame(
        working[valid_coordinates].copy(),
        geometry=gpd.points_from_xy(
            working.loc[valid_coordinates, "X"],
            working.loc[valid_coordinates, "Y"],
        ),
        crs=SOURCE_CRS,
    )

    print(f"Total records loaded: {len(working):,}")
    print(f"Records with valid X/Y coordinates: {len(points):,}")
    print(f"Records without valid X/Y coordinates: {(~valid_coordinates).sum():,}")

    return working, points


def prepare_tracts():
    if not TRACTS_PATH.exists():
        raise FileNotFoundError(
            f"Missing tract GeoJSON: {TRACTS_PATH}. "
            "Create durham_city_intersecting_tracts.geojson first."
        )

    tracts = gpd.read_file(TRACTS_PATH)

    if tracts.crs is None:
        tracts = tracts.set_crs(WEB_CRS)

    tracts = tracts.to_crs(SOURCE_CRS)

    if "GEOID" in tracts.columns:
        geoid_column = "GEOID"
    elif "GEOID20" in tracts.columns:
        geoid_column = "GEOID20"
    elif "geoid" in tracts.columns:
        geoid_column = "geoid"
    else:
        raise ValueError("Could not find a GEOID column in the tract layer.")

    if "NAMELSAD" in tracts.columns:
        name_column = "NAMELSAD"
    elif "NAME" in tracts.columns:
        name_column = "NAME"
    elif "name" in tracts.columns:
        name_column = "name"
    else:
        name_column = geoid_column

    tracts = tracts[[geoid_column, name_column, "geometry"]].copy()

    tracts = tracts.rename(
        columns={
            geoid_column: "tract_geoid",
            name_column: "tract_name",
        }
    )

    tracts["tract_geoid"] = tracts["tract_geoid"].astype(str)
    tracts["tract_name"] = tracts["tract_name"].astype(str)

    tracts["tract_area_sq_m"] = tracts.geometry.area
    tracts["tract_area_sq_mi"] = tracts["tract_area_sq_m"] / 2_589_988.110336

    print(f"Intersecting census tracts loaded: {len(tracts):,}")
    print(f"Tract CRS after projection: {tracts.crs}")

    return tracts


def spatial_join_points_to_tracts(points, tracts):
    print("")
    print("Running spatial join...")
    print("Join rule: point must intersect tract polygon.")
    print("This assigns points inside polygons and points exactly on tract boundaries.")

    joined = gpd.sjoin(
        points,
        tracts,
        how="left",
        predicate="intersects",
    )

    duplicate_count = int(joined["_source_row_id"].duplicated().sum())

    if duplicate_count > 0:
        print(f"Duplicate tract matches found: {duplicate_count:,}")
        print("Resolving duplicates by keeping the smallest tract area match per point.")

        joined = (
            joined
            .sort_values(["_source_row_id", "tract_area_sq_m"])
            .drop_duplicates(subset=["_source_row_id"], keep="first")
            .copy()
        )
    else:
        print("Duplicate tract matches found: 0")

    return joined


def add_lat_lon(joined_points):
    points_web = joined_points.to_crs(WEB_CRS)

    joined_points = joined_points.copy()
    joined_points["longitude"] = points_web.geometry.x
    joined_points["latitude"] = points_web.geometry.y

    return joined_points


def build_tract_join():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_df = load_arrest_data()
    raw_df = normalize_arrest_attributes(raw_df)

    full_df, points = prepare_arrest_points(raw_df)
    tracts = prepare_tracts()

    joined = spatial_join_points_to_tracts(points, tracts)
    joined = add_lat_lon(joined)

    joined_columns = [
        "_source_row_id",
        "tract_geoid",
        "tract_name",
        "tract_area_sq_mi",
        "longitude",
        "latitude",
    ]

    joined_lookup = joined[joined_columns].copy()

    output = full_df.merge(
        joined_lookup,
        on="_source_row_id",
        how="left",
    )

    output["tract_geoid"] = output["tract_geoid"].fillna("Not assigned")
    output["tract_name"] = output["tract_name"].fillna("Not assigned")
    output["tract_area_sq_mi"] = pd.to_numeric(
        output["tract_area_sq_mi"],
        errors="coerce",
    )

    output["longitude"] = pd.to_numeric(output["longitude"], errors="coerce")
    output["latitude"] = pd.to_numeric(output["latitude"], errors="coerce")

    output["inside_intersecting_tract"] = output["tract_geoid"] != "Not assigned"

    assigned_count = int(output["inside_intersecting_tract"].sum())
    unassigned_count = int((~output["inside_intersecting_tract"]).sum())

    assigned_with_coordinates = int(
        (
            output["inside_intersecting_tract"]
            & output["longitude"].notna()
            & output["latitude"].notna()
        ).sum()
    )

    total_with_coordinates = int(
        (
            output["longitude"].notna()
            & output["latitude"].notna()
        ).sum()
    )

    output = output.drop(columns=["_source_row_id"])

    output.to_csv(OUTPUT_PATH, index=False)

    print("")
    print("Tract join complete.")
    print(f"Output file: {OUTPUT_PATH}")
    print(f"Output records: {len(output):,}")
    print(f"Assigned to census tract intersecting Durham municipal boundary: {assigned_count:,}")
    print(f"Assigned with valid latitude/longitude: {assigned_with_coordinates:,}")
    print(f"Total records with valid latitude/longitude: {total_with_coordinates:,}")
    print(f"Not assigned to intersecting tract: {unassigned_count:,}")

    if len(output) > 0:
        assigned_share = assigned_count / len(output) * 100
        print(f"Assigned share of total records: {assigned_share:.1f}%")

    if total_with_coordinates > 0:
        assigned_coordinate_share = assigned_with_coordinates / total_with_coordinates * 100
        print(f"Assigned share of records with valid coordinates: {assigned_coordinate_share:.1f}%")

    print("")
    print("Validation:")
    print("inside_intersecting_tract = True means the arrest point intersects one of the full census tract polygons.")
    print("The tract polygons are the full census tracts that intersect the Durham municipal boundary.")
    print("The tract geometries are not clipped to the municipal boundary.")

    print("")
    print("Preview:")
    preview_columns = [
        "Arrest Number",
        "Arrest Date",
        "Description",
        "District",
        "Beat",
        "tract_geoid",
        "tract_name",
        "inside_intersecting_tract",
        "longitude",
        "latitude",
    ]

    available_preview_columns = [
        column for column in preview_columns if column in output.columns
    ]

    print(output[available_preview_columns].head(10))


if __name__ == "__main__":
    build_tract_join()