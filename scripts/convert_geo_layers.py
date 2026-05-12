from pathlib import Path

import geopandas as gpd


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_GEO_DIR = BASE_DIR / "data" / "raw_geo"
OUTPUT_DIR = BASE_DIR / "app" / "static" / "geojson"

COUNTY_BOUNDARY_FILE = RAW_GEO_DIR / "DCo_Boundary_1632930722800117369.gpkg"
POLICE_BEATS_FILE = RAW_GEO_DIR / "Police_7537918827030012087.gpkg"

COUNTY_OUTPUT_FILE = OUTPUT_DIR / "durham_county_boundary.geojson"
POLICE_BEATS_OUTPUT_FILE = OUTPUT_DIR / "police_beats.geojson"


def convert_layer_to_geojson(input_path, layer_name, output_path):
    print(f"Reading: {input_path}")
    print(f"Layer: {layer_name}")

    gdf = gpd.read_file(input_path, layer=layer_name)

    print(f"Original CRS: {gdf.crs}")
    print(f"Feature count: {len(gdf)}")

    if gdf.crs is None:
        raise ValueError(f"No CRS found for {input_path}")

    gdf = gdf.to_crs(epsg=4326)

    print(f"Converted CRS: {gdf.crs}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GeoJSON")

    print(f"Saved: {output_path}")
    print("-" * 60)


def main():
    convert_layer_to_geojson(
        input_path=COUNTY_BOUNDARY_FILE,
        layer_name="DCo_Boundary",
        output_path=COUNTY_OUTPUT_FILE,
    )

    convert_layer_to_geojson(
        input_path=POLICE_BEATS_FILE,
        layer_name="Police_Beats",
        output_path=POLICE_BEATS_OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()
