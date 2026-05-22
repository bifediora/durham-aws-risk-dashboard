import os
import requests
from dotenv import load_dotenv


def main():
    """
    Simple Census API test.

    This script:
    1. Loads your Census API key from the .env file
    2. Sends a small ACS 5-year request for Durham County census tracts
    3. Prints the first few rows returned by the API
    """

    load_dotenv()

    api_key = os.getenv("CENSUS_API_KEY")

    if not api_key:
        raise ValueError(
            "CENSUS_API_KEY was not found. Check that your .env file is in the project root."
        )

    base_url = "https://api.census.gov/data/2024/acs/acs5"

    params = {
        "get": "NAME,B01003_001E",
        "for": "tract:*",
        "in": "state:37 county:063",
        "key": api_key,
    }

    response = requests.get(base_url, params=params, timeout=30)

    if response.status_code != 200:
        print("Request failed.")
        print("Status code:", response.status_code)
        print("Response text:", response.text)
        return

    data = response.json()

    print("Census API request successful.")
    print()
    print("Column names:")
    print(data[0])
    print()
    print("First 5 records:")
    for row in data[1:6]:
        print(row)


if __name__ == "__main__":
    main()