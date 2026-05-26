from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_NEIGHBORHOODS_PATH = PROJECT_ROOT / "data" / "raw_geo" / "durham-hoods.geojson"
TRACTS_PATH = PROJECT_ROOT / "app" / "static" / "geojson" / "durham_city_intersecting_tracts.geojson"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
PROJECTED_NEIGHBORHOODS_PATH = OUTPUT_DIR / "durham_neighborhoods_projected.geojson"
WEB_NEIGHBORHOODS_PATH = OUTPUT_DIR / "durham_neighborhoods_web.geojson"
SUMMARY_PATH = OUTPUT_DIR / "durham_neighborhoods_inspection_summary.txt"

ENRICHED_TRACT_OUTPUTS = [
    OUTPUT_DIR / "durham_arrests_tract_enriched.geojson",
    OUTPUT_DIR / "durham_arrests_tract_enriched.csv",
    OUTPUT_DIR / "durham_shootings_tract_enriched.geojson",
    OUTPUT_DIR / "durham_shootings_tract_enriched.csv",
    OUTPUT_DIR / "durham_tract_enriched.geojson",
    OUTPUT_DIR / "durham_tract_enriched.csv",
]

WEB_CRS = "EPSG:4326"
PROJECTED_CRS = "EPSG:2264"
OVERLAP_MIN_SQ_FT = 1.0


TIER_1_NAMES = {
    "american tobacco campus",
    "brightleaf at the park",
    "downtown",
    "duke park",
    "forest hills",
    "lakewood park",
    "old east durham",
    "old north durham",
    "southside / st. teresa",
    "trinity park",
    "walltown",
}

TIER_1_CONTAINS = [
    "american tobacco",
    "brightleaf",
]

TIER_2_NAMES = {
    "burch avenue",
    "central park",
    "cleveland-holloway",
    "duke east campus",
    "duke homestead",
    "duke west campus",
    "eastway village",
    "edgemont",
    "golden belt",
    "hope valley",
    "hope valley farms",
    "lakewood park",
    "lyon park",
    "morehead hill",
    "north carolina central university",
    "northgate park",
    "old west durham",
    "parkwood",
    "rockwood",
    "southpoint manor",
    "treyburn",
    "trinity heights",
    "tuscaloosa-lakewood",
    "watts hospital-hillandale",
    "west end",
    "woodcroft",
}


def normalize_geoid(value):
    if pd.isna(value):
        return None

    geoid = str(value).strip()

    if geoid.endswith(".0"):
        geoid = geoid[:-2]

    if not geoid or geoid.lower() in ["nan", "none", "not assigned"]:
        return None

    return geoid.zfill(11)


def log(lines, text=""):
    print(text)
    lines.append(text)


def find_name_column(gdf):
    for column in ["name", "neighborhood", "hood", "Name", "NAME"]:
        if column in gdf.columns:
            return column

    return None


def assign_label_tier(name):
    clean_name = str(name or "").strip().lower()

    if clean_name in TIER_1_NAMES:
        return 1

    if any(fragment in clean_name for fragment in TIER_1_CONTAINS):
        return 1

    if clean_name in TIER_2_NAMES:
        return 2

    return 3


def load_neighborhoods():
    if not RAW_NEIGHBORHOODS_PATH.exists():
        raise FileNotFoundError(f"Missing raw neighborhoods file: {RAW_NEIGHBORHOODS_PATH}")

    neighborhoods = gpd.read_file(RAW_NEIGHBORHOODS_PATH)

    if neighborhoods.crs is None:
        neighborhoods = neighborhoods.set_crs(WEB_CRS)

    name_column = find_name_column(neighborhoods)

    if name_column is None:
        raise ValueError("Could not find a neighborhood name field.")

    neighborhoods = neighborhoods.rename(columns={name_column: "neighborhood_name"})
    neighborhoods["neighborhood_name"] = (
        neighborhoods["neighborhood_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    neighborhoods["label_tier"] = neighborhoods["neighborhood_name"].apply(assign_label_tier)

    neighborhoods = neighborhoods[
        [
            "neighborhood_name",
            "label_tier",
            "geometry",
        ]
    ].copy()

    return neighborhoods


def load_tracts():
    if not TRACTS_PATH.exists():
        raise FileNotFoundError(f"Missing tract layer: {TRACTS_PATH}")

    tracts = gpd.read_file(TRACTS_PATH)

    if tracts.crs is None:
        tracts = tracts.set_crs(WEB_CRS)

    geoid_column = next(
        (
            column
            for column in ["GEOID", "GEOID20", "geoid", "tract_geoid"]
            if column in tracts.columns
        ),
        None,
    )

    if geoid_column is None:
        raise ValueError("Could not find a tract GEOID column.")

    name_column = next(
        (
            column
            for column in ["NAMELSAD", "NAME", "name", "tract_name"]
            if column in tracts.columns
        ),
        geoid_column,
    )

    tracts["tract_geoid"] = tracts[geoid_column].apply(normalize_geoid)
    tracts["tract_name"] = tracts[name_column].fillna("").astype(str)

    return tracts[
        [
            "tract_geoid",
            "tract_name",
            "geometry",
        ]
    ].copy()


def check_pairwise_overlaps(projected_neighborhoods):
    spatial_index = projected_neighborhoods.sindex
    overlap_records = []

    for idx, row in projected_neighborhoods.iterrows():
        geometry = row.geometry

        if geometry is None or geometry.is_empty:
            continue

        candidate_indices = list(spatial_index.intersection(geometry.bounds))

        for other_idx in candidate_indices:
            if other_idx <= idx:
                continue

            other = projected_neighborhoods.iloc[other_idx]
            other_geometry = other.geometry

            if other_geometry is None or other_geometry.is_empty:
                continue

            intersection = geometry.intersection(other_geometry)

            if intersection.is_empty:
                continue

            area_sq_ft = intersection.area

            if area_sq_ft > OVERLAP_MIN_SQ_FT:
                overlap_records.append(
                    {
                        "neighborhood_a": row["neighborhood_name"],
                        "neighborhood_b": other["neighborhood_name"],
                        "area_sq_ft": area_sq_ft,
                        "area_sq_mi": area_sq_ft / 27_878_400,
                    }
                )

    return pd.DataFrame(overlap_records)


def build_tract_neighborhood_assignments(projected_tracts, projected_neighborhoods):
    tract_rows = []

    neighborhoods_for_join = projected_neighborhoods[
        [
            "neighborhood_name",
            "geometry",
        ]
    ].copy()

    for _, tract in projected_tracts.iterrows():
        tract_geometry = tract.geometry

        overlapping = neighborhoods_for_join[
            neighborhoods_for_join.intersects(tract_geometry)
        ].copy()

        intersection_rows = []

        for _, neighborhood in overlapping.iterrows():
            intersection = tract_geometry.intersection(neighborhood.geometry)

            if intersection.is_empty:
                continue

            area_sq_ft = intersection.area

            if area_sq_ft <= OVERLAP_MIN_SQ_FT:
                continue

            intersection_rows.append(
                {
                    "neighborhood_name": neighborhood["neighborhood_name"],
                    "intersection_area_sq_ft": area_sq_ft,
                }
            )

        if not intersection_rows:
            tract_rows.append(
                {
                    "tract_geoid": tract["tract_geoid"],
                    "primary_neighborhood": "Not assigned",
                    "secondary_neighborhoods": "",
                    "neighborhood_overlap_count": 0,
                }
            )
            continue

        intersections = (
            pd.DataFrame(intersection_rows)
            .sort_values("intersection_area_sq_ft", ascending=False)
            .reset_index(drop=True)
        )

        primary = intersections.loc[0, "neighborhood_name"]
        secondary_names = intersections.loc[1:, "neighborhood_name"].tolist()

        tract_rows.append(
            {
                "tract_geoid": tract["tract_geoid"],
                "primary_neighborhood": primary,
                "secondary_neighborhoods": ", ".join(secondary_names),
                "neighborhood_overlap_count": len(intersections),
            }
        )

    return pd.DataFrame(tract_rows)


def add_neighborhood_fields_to_outputs(assignments):
    updated_paths = []

    for path in ENRICHED_TRACT_OUTPUTS:
        if not path.exists():
            continue

        if path.suffix.lower() == ".geojson":
            data = gpd.read_file(path)
            is_geo = True
        else:
            data = pd.read_csv(path, dtype={"tract_geoid": str})
            is_geo = False

        if "tract_geoid" not in data.columns:
            continue

        data = data.drop(
            columns=[
                "primary_neighborhood",
                "secondary_neighborhoods",
                "neighborhood_overlap_count",
            ],
            errors="ignore",
        )

        data["tract_geoid"] = data["tract_geoid"].apply(normalize_geoid)

        enriched = data.merge(
            assignments,
            on="tract_geoid",
            how="left",
            validate="one_to_one",
        )

        enriched["primary_neighborhood"] = enriched["primary_neighborhood"].fillna("Not assigned")
        enriched["secondary_neighborhoods"] = enriched["secondary_neighborhoods"].fillna("")
        enriched["neighborhood_overlap_count"] = (
            pd.to_numeric(enriched["neighborhood_overlap_count"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

        if is_geo:
            enriched.to_file(path, driver="GeoJSON")
        else:
            enriched.to_csv(path, index=False)

        updated_paths.append(path)

    return updated_paths


def write_summary(
    lines,
    raw_neighborhoods,
    projected_neighborhoods,
    web_neighborhoods,
    projected_tracts,
    overlap_df,
    assignments,
    updated_paths,
):
    log(lines)
    log(lines, "=" * 80)
    log(lines, "DURHAM NEIGHBORHOOD CONTEXT PROCESSING SUMMARY")
    log(lines, "=" * 80)
    log(lines, f"Input: {RAW_NEIGHBORHOODS_PATH}")
    log(lines, f"Raw CRS: {raw_neighborhoods.crs}")
    log(lines, f"Projected CRS: {projected_neighborhoods.crs}")
    log(lines, f"Web CRS: {web_neighborhoods.crs}")
    log(lines, f"Neighborhood features: {len(raw_neighborhoods):,}")
    log(lines, f"Neighborhood columns: {list(raw_neighborhoods.columns)}")
    log(lines, f"Name field: neighborhood_name")
    log(lines, f"Missing/blank names: {int((raw_neighborhoods['neighborhood_name'] == '').sum()):,}")
    log(lines, f"Duplicate names: {int(raw_neighborhoods['neighborhood_name'].duplicated().sum()):,}")
    log(lines, f"Invalid geometries: {int((~raw_neighborhoods.geometry.is_valid).sum()):,}")
    log(lines, f"Empty/missing geometries: {int((raw_neighborhoods.geometry.is_empty | raw_neighborhoods.geometry.isna()).sum()):,}")
    log(lines, f"Overlap pairs > {OVERLAP_MIN_SQ_FT:.0f} sq ft: {len(overlap_df):,}")

    if not overlap_df.empty:
        total_overlap = overlap_df["area_sq_mi"].sum()
        log(lines, f"Pairwise overlap area total: {total_overlap:.6f} sq mi")
        log(lines, "Largest overlap pairs:")

        for _, row in overlap_df.sort_values("area_sq_ft", ascending=False).head(15).iterrows():
            log(
                lines,
                f"  - {row['neighborhood_a']} / {row['neighborhood_b']}: "
                f"{row['area_sq_ft']:.1f} sq ft ({row['area_sq_mi']:.6f} sq mi)",
            )

    tier_counts = raw_neighborhoods["label_tier"].value_counts().sort_index().to_dict()
    log(lines, f"Label tier counts: {tier_counts}")
    log(lines, "Recommended label visibility: tier 1 at full-city extent; tiers 1-2 at mid zoom; all tiers when zoomed in.")

    log(lines)
    log(lines, f"Census tracts processed: {len(projected_tracts):,}")
    log(lines, f"Primary neighborhood assignments: {int((assignments['primary_neighborhood'] != 'Not assigned').sum()):,}")
    log(lines, f"Tracts with no neighborhood overlap: {int((assignments['neighborhood_overlap_count'] == 0).sum()):,}")
    log(lines, f"Tracts with one neighborhood overlap: {int((assignments['neighborhood_overlap_count'] == 1).sum()):,}")
    log(lines, f"Tracts with multiple neighborhood overlaps: {int((assignments['neighborhood_overlap_count'] > 1).sum()):,}")

    log(lines)
    log(lines, f"Projected output: {PROJECTED_NEIGHBORHOODS_PATH}")
    log(lines, f"Leaflet-ready web output: {WEB_NEIGHBORHOODS_PATH}")
    log(lines, f"Inspection summary: {SUMMARY_PATH}")
    log(lines, "Updated enriched tract outputs:")

    for path in updated_paths:
        log(lines, f"  - {path}")

    log(lines)
    log(lines, "Important interpretation note:")
    log(lines, "Neighborhoods are a context, label, and public-interpretation layer only.")
    log(lines, "Census tracts remain the statistical layer for ACS joins, normalized rates, choropleths, and demographic analytics.")
    log(lines, "Manual visual QA against Durham reference imagery is still recommended before dashboard integration.")

    SUMMARY_PATH.write_text("\n".join(lines))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = []

    raw_neighborhoods = load_neighborhoods()
    web_neighborhoods = raw_neighborhoods.to_crs(WEB_CRS)
    projected_neighborhoods = raw_neighborhoods.to_crs(PROJECTED_CRS)

    projected_neighborhoods.to_file(PROJECTED_NEIGHBORHOODS_PATH, driver="GeoJSON")
    web_neighborhoods.to_file(WEB_NEIGHBORHOODS_PATH, driver="GeoJSON")

    tracts = load_tracts()
    projected_tracts = tracts.to_crs(PROJECTED_CRS)

    overlap_df = check_pairwise_overlaps(projected_neighborhoods)
    assignments = build_tract_neighborhood_assignments(projected_tracts, projected_neighborhoods)
    updated_paths = add_neighborhood_fields_to_outputs(assignments)

    write_summary(
        lines=lines,
        raw_neighborhoods=raw_neighborhoods,
        projected_neighborhoods=projected_neighborhoods,
        web_neighborhoods=web_neighborhoods,
        projected_tracts=projected_tracts,
        overlap_df=overlap_df,
        assignments=assignments,
        updated_paths=updated_paths,
    )


if __name__ == "__main__":
    main()
