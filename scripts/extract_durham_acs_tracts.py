from pathlib import Path
import os
import sys

import pandas as pd
import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "acs_durham_tract_demographics.csv"

# Compatibility output for later enrichment workflow
COMPAT_OUTPUT_PATH = OUTPUT_DIR / "durham_acs_tract_demographics.csv"

ACS_YEAR = "2024"
ACS_ENDPOINT = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"

STATE_FIPS = "37"
COUNTY_FIPS = "063"

# Census API limit is 50 variables per request.
# NAME counts as one variable, so each batch should contain 49 ACS variables max.
MAX_ACS_VARIABLES_PER_BATCH = 49


ACS_VARIABLES = {
    # Core population
    "B01003_001E": "total_population",
    "B01002_001E": "median_age",

    # Sex composition
    "B01001_002E": "male_population",
    "B01001_026E": "female_population",

    # Male age groups
    "B01001_003E": "male_under_5",
    "B01001_004E": "male_5_to_9",
    "B01001_005E": "male_10_to_14",
    "B01001_006E": "male_15_to_17",
    "B01001_020E": "male_65_to_66",
    "B01001_021E": "male_67_to_69",
    "B01001_022E": "male_70_to_74",
    "B01001_023E": "male_75_to_79",
    "B01001_024E": "male_80_to_84",
    "B01001_025E": "male_85_plus",

    # Female age groups
    "B01001_027E": "female_under_5",
    "B01001_028E": "female_5_to_9",
    "B01001_029E": "female_10_to_14",
    "B01001_030E": "female_15_to_17",
    "B01001_044E": "female_65_to_66",
    "B01001_045E": "female_67_to_69",
    "B01001_046E": "female_70_to_74",
    "B01001_047E": "female_75_to_79",
    "B01001_048E": "female_80_to_84",
    "B01001_049E": "female_85_plus",

    # Income
    "B19013_001E": "median_household_income",

    # Poverty
    "B17001_001E": "poverty_status_population",
    "B17001_002E": "poverty_count",

    # Employment
    "B23025_003E": "civilian_labor_force",
    "B23025_005E": "unemployed_count",

    # Race and ethnicity
    "B03002_001E": "race_ethnicity_total",
    "B03002_003E": "white_non_hispanic",
    "B03002_004E": "black_non_hispanic",
    "B03002_005E": "american_indian_alaska_native_non_hispanic",
    "B03002_006E": "asian_non_hispanic",
    "B03002_007E": "native_hawaiian_pacific_islander_non_hispanic",
    "B03002_008E": "other_race_non_hispanic",
    "B03002_009E": "two_or_more_races_non_hispanic",
    "B03002_012E": "hispanic_or_latino",

    # Housing occupancy and vacancy
    "B25002_001E": "total_housing_units",
    "B25002_002E": "occupied_housing_units",
    "B25002_003E": "vacant_housing_units",

    # Housing tenure
    "B25003_001E": "occupied_units_tenure_total",
    "B25003_002E": "owner_occupied_units",
    "B25003_003E": "renter_occupied_units",

    # Educational attainment, population 25+
    "B15003_001E": "education_population_25_plus",
    "B15003_017E": "high_school_diploma",
    "B15003_018E": "ged_or_alternative",
    "B15003_019E": "some_college_less_than_1_year",
    "B15003_020E": "some_college_1_or_more_years",
    "B15003_021E": "associates_degree",
    "B15003_022E": "bachelors_degree",
    "B15003_023E": "masters_degree",
    "B15003_024E": "professional_degree",
    "B15003_025E": "doctorate_degree",
}


def load_api_key():
    load_dotenv(ENV_PATH)

    api_key = os.getenv("CENSUS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "CENSUS_API_KEY was not found. Confirm your .env file is in the project root "
            "and contains CENSUS_API_KEY=your_actual_api_key_here"
        )

    return api_key


def chunk_list(values, chunk_size):
    values = list(values)

    for start_index in range(0, len(values), chunk_size):
        yield values[start_index:start_index + chunk_size]


def fetch_acs_batch(api_key, variable_batch, batch_number, total_batches):
    requested_variables = ["NAME"] + variable_batch

    params = {
        "get": ",".join(requested_variables),
        "for": "tract:*",
        "in": f"state:{STATE_FIPS} county:{COUNTY_FIPS}",
        "key": api_key,
    }

    print("")
    print(f"Requesting ACS batch {batch_number} of {total_batches}...")
    print(f"Variables requested in this batch: {len(requested_variables)}")

    response = requests.get(ACS_ENDPOINT, params=params, timeout=60)

    if response.status_code != 200:
        print("Census API request failed.")
        print(f"Status code: {response.status_code}")
        print(response.text)
        sys.exit(1)

    data = response.json()

    if not data or len(data) < 2:
        raise RuntimeError(f"Census API returned no tract records for batch {batch_number}.")

    headers = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=headers)

    print(f"Batch {batch_number} successful. Rows returned: {len(df):,}")

    return df


def fetch_acs_data(api_key):
    variable_codes = list(ACS_VARIABLES.keys())
    batches = list(chunk_list(variable_codes, MAX_ACS_VARIABLES_PER_BATCH))

    print("Requesting ACS data...")
    print(f"Endpoint: {ACS_ENDPOINT}")
    print(f"Total ACS variables requested: {len(variable_codes)}")
    print(f"Geography: state {STATE_FIPS}, county {COUNTY_FIPS}, tract:*")
    print(f"Number of API batches: {len(batches)}")

    merged_df = None

    for batch_index, variable_batch in enumerate(batches, start=1):
        batch_df = fetch_acs_batch(
            api_key=api_key,
            variable_batch=variable_batch,
            batch_number=batch_index,
            total_batches=len(batches),
        )

        join_columns = ["NAME", "state", "county", "tract"]

        if merged_df is None:
            merged_df = batch_df
        else:
            merged_df = merged_df.merge(
                batch_df,
                on=join_columns,
                how="outer",
                validate="one_to_one",
            )

    if merged_df is None or merged_df.empty:
        raise RuntimeError("No ACS data was returned after batching.")

    print("")
    print("All ACS batches completed successfully.")
    print(f"Merged ACS rows: {len(merged_df):,}")
    print(f"Merged ACS columns: {len(merged_df.columns):,}")

    return merged_df


def normalize_geoid(df):
    df = df.copy()

    df["state"] = df["state"].astype(str).str.zfill(2)
    df["county"] = df["county"].astype(str).str.zfill(3)
    df["tract"] = df["tract"].astype(str).str.zfill(6)

    df["tract_geoid"] = df["state"] + df["county"] + df["tract"]
    df["GEOID"] = df["tract_geoid"]

    return df


def rename_and_convert_columns(df):
    df = df.copy()

    df = df.rename(columns=ACS_VARIABLES)

    numeric_columns = [
        column
        for column in df.columns
        if column not in ["NAME", "state", "county", "tract", "tract_geoid", "GEOID"]
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

        # ACS estimate fields may use large negative sentinel values for
        # unavailable, suppressed, or not applicable estimates.
        # These should be treated as missing, not real values.
        df.loc[df[column] < 0, column] = pd.NA

    return df


def safe_rate(numerator, denominator, multiplier=100):
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return pd.NA

    return round((numerator / denominator) * multiplier, 2)


def calculate_derived_fields(df):
    df = df.copy()

    df["youth_population"] = (
        df["male_under_5"]
        + df["male_5_to_9"]
        + df["male_10_to_14"]
        + df["male_15_to_17"]
        + df["female_under_5"]
        + df["female_5_to_9"]
        + df["female_10_to_14"]
        + df["female_15_to_17"]
    )

    df["senior_population"] = (
        df["male_65_to_66"]
        + df["male_67_to_69"]
        + df["male_70_to_74"]
        + df["male_75_to_79"]
        + df["male_80_to_84"]
        + df["male_85_plus"]
        + df["female_65_to_66"]
        + df["female_67_to_69"]
        + df["female_70_to_74"]
        + df["female_75_to_79"]
        + df["female_80_to_84"]
        + df["female_85_plus"]
    )

    df["high_school_or_higher_count"] = (
        df["high_school_diploma"]
        + df["ged_or_alternative"]
        + df["some_college_less_than_1_year"]
        + df["some_college_1_or_more_years"]
        + df["associates_degree"]
        + df["bachelors_degree"]
        + df["masters_degree"]
        + df["professional_degree"]
        + df["doctorate_degree"]
    )

    df["bachelors_or_higher_count"] = (
        df["bachelors_degree"]
        + df["masters_degree"]
        + df["professional_degree"]
        + df["doctorate_degree"]
    )

    df["male_share"] = df.apply(
        lambda row: safe_rate(row["male_population"], row["total_population"]),
        axis=1,
    )

    df["female_share"] = df.apply(
        lambda row: safe_rate(row["female_population"], row["total_population"]),
        axis=1,
    )

    df["youth_population_share"] = df.apply(
        lambda row: safe_rate(row["youth_population"], row["total_population"]),
        axis=1,
    )

    df["senior_population_share"] = df.apply(
        lambda row: safe_rate(row["senior_population"], row["total_population"]),
        axis=1,
    )

    df["poverty_rate"] = df.apply(
        lambda row: safe_rate(row["poverty_count"], row["poverty_status_population"]),
        axis=1,
    )

    df["unemployment_rate"] = df.apply(
        lambda row: safe_rate(row["unemployed_count"], row["civilian_labor_force"]),
        axis=1,
    )

    df["white_non_hispanic_share"] = df.apply(
        lambda row: safe_rate(row["white_non_hispanic"], row["race_ethnicity_total"]),
        axis=1,
    )

    df["black_non_hispanic_share"] = df.apply(
        lambda row: safe_rate(row["black_non_hispanic"], row["race_ethnicity_total"]),
        axis=1,
    )

    df["american_indian_alaska_native_non_hispanic_share"] = df.apply(
        lambda row: safe_rate(
            row["american_indian_alaska_native_non_hispanic"],
            row["race_ethnicity_total"],
        ),
        axis=1,
    )

    df["asian_non_hispanic_share"] = df.apply(
        lambda row: safe_rate(row["asian_non_hispanic"], row["race_ethnicity_total"]),
        axis=1,
    )

    df["native_hawaiian_pacific_islander_non_hispanic_share"] = df.apply(
        lambda row: safe_rate(
            row["native_hawaiian_pacific_islander_non_hispanic"],
            row["race_ethnicity_total"],
        ),
        axis=1,
    )

    df["other_race_non_hispanic_share"] = df.apply(
        lambda row: safe_rate(row["other_race_non_hispanic"], row["race_ethnicity_total"]),
        axis=1,
    )

    df["two_or_more_races_non_hispanic_share"] = df.apply(
        lambda row: safe_rate(
            row["two_or_more_races_non_hispanic"],
            row["race_ethnicity_total"],
        ),
        axis=1,
    )

    df["hispanic_or_latino_share"] = df.apply(
        lambda row: safe_rate(row["hispanic_or_latino"], row["race_ethnicity_total"]),
        axis=1,
    )

    df["housing_vacancy_rate"] = df.apply(
        lambda row: safe_rate(row["vacant_housing_units"], row["total_housing_units"]),
        axis=1,
    )

    df["owner_occupancy_share"] = df.apply(
        lambda row: safe_rate(row["owner_occupied_units"], row["occupied_units_tenure_total"]),
        axis=1,
    )

    df["renter_occupancy_share"] = df.apply(
        lambda row: safe_rate(row["renter_occupied_units"], row["occupied_units_tenure_total"]),
        axis=1,
    )

    df["high_school_or_higher_rate"] = df.apply(
        lambda row: safe_rate(
            row["high_school_or_higher_count"],
            row["education_population_25_plus"],
        ),
        axis=1,
    )

    df["bachelors_or_higher_rate"] = df.apply(
        lambda row: safe_rate(
            row["bachelors_or_higher_count"],
            row["education_population_25_plus"],
        ),
        axis=1,
    )

    return df


def select_output_columns(df):
    desired_columns = [
        "GEOID",
        "tract_geoid",
        "NAME",
        "state",
        "county",
        "tract",

        "total_population",
        "median_age",
        "median_household_income",

        "male_population",
        "female_population",
        "male_share",
        "female_share",

        "youth_population",
        "senior_population",
        "youth_population_share",
        "senior_population_share",

        "poverty_status_population",
        "poverty_count",
        "poverty_rate",

        "civilian_labor_force",
        "unemployed_count",
        "unemployment_rate",

        "race_ethnicity_total",
        "white_non_hispanic",
        "black_non_hispanic",
        "american_indian_alaska_native_non_hispanic",
        "asian_non_hispanic",
        "native_hawaiian_pacific_islander_non_hispanic",
        "other_race_non_hispanic",
        "two_or_more_races_non_hispanic",
        "hispanic_or_latino",

        "white_non_hispanic_share",
        "black_non_hispanic_share",
        "american_indian_alaska_native_non_hispanic_share",
        "asian_non_hispanic_share",
        "native_hawaiian_pacific_islander_non_hispanic_share",
        "other_race_non_hispanic_share",
        "two_or_more_races_non_hispanic_share",
        "hispanic_or_latino_share",

        "total_housing_units",
        "occupied_housing_units",
        "vacant_housing_units",
        "housing_vacancy_rate",

        "occupied_units_tenure_total",
        "owner_occupied_units",
        "renter_occupied_units",
        "owner_occupancy_share",
        "renter_occupancy_share",

        "education_population_25_plus",
        "high_school_or_higher_count",
        "bachelors_or_higher_count",
        "high_school_or_higher_rate",
        "bachelors_or_higher_rate",
    ]

    existing_columns = [
        column
        for column in desired_columns
        if column in df.columns
    ]

    return df[existing_columns].copy()


def validate_output(df):
    print("")
    print("=" * 80)
    print("ACS DURHAM TRACT DEMOGRAPHICS VALIDATION")
    print("=" * 80)

    print(f"Output records: {len(df):,}")
    print(f"Unique GEOIDs: {df['GEOID'].nunique():,}")
    print(f"Duplicate GEOIDs: {df['GEOID'].duplicated().sum():,}")
    print(f"Missing GEOIDs: {df['GEOID'].isna().sum():,}")

    print("")
    print("First 5 GEOIDs:")
    print(df[["GEOID", "NAME"]].head())

    summary_columns = [
        "total_population",
        "median_household_income",
        "poverty_rate",
        "unemployment_rate",
        "bachelors_or_higher_rate",
        "housing_vacancy_rate",
        "youth_population_share",
        "senior_population_share",
    ]

    existing_summary_columns = [
        column
        for column in summary_columns
        if column in df.columns
    ]

    print("")
    print("Summary statistics:")
    print(df[existing_summary_columns].describe().round(2))

    print("")
    print("Missing value counts:")
    print(df[existing_summary_columns].isna().sum())

    print("")
    print("Output files:")
    print(f"- {OUTPUT_PATH}")
    print(f"- {COMPAT_OUTPUT_PATH}")

    print("=" * 80)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    api_key = load_api_key()

    raw_df = fetch_acs_data(api_key)
    raw_df = normalize_geoid(raw_df)
    clean_df = rename_and_convert_columns(raw_df)
    clean_df = calculate_derived_fields(clean_df)
    output_df = select_output_columns(clean_df)

    output_df.to_csv(OUTPUT_PATH, index=False)
    output_df.to_csv(COMPAT_OUTPUT_PATH, index=False)

    print("")
    print(f"Saved primary ACS output to: {OUTPUT_PATH}")
    print(f"Saved compatibility ACS output to: {COMPAT_OUTPUT_PATH}")

    validate_output(output_df)


if __name__ == "__main__":
    main()