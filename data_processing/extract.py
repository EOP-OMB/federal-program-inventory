"""
Extracts program information from various sources (e.g., SAM.gov).
"""

import json
import jsonschema
import os
import sys
import time
import csv
import io
from string import ascii_lowercase
import requests
import pandas as pd
from tabula import read_pdf

# file paths
DISK_DIRECTORY = os.getenv('ETL_EXTRACT_DISK_DIRECTORY')
SOURCE_DIRECTORY = os.getenv('ETL_EXTRACT_SOURCE_DIRECTORY')
EXTRACTED_DIRECTORY = os.getenv('ETL_EXTRACT_EXTRACTED_DIRECTORY')

if (DISK_DIRECTORY is None or
    SOURCE_DIRECTORY is None or
    EXTRACTED_DIRECTORY is None):
    print("Error:  set the following environment variables:")
    print("  ETL_EXTRACT_DISK_DIRECTORY")
    print("  ETL_EXTRACT_SOURCE_DIRECTORY")
    print("  ETL_EXTRACT_EXTRACTED_DIRECTORY")
    sys.exit(1)

def validate_api_schema_get(url, filename):
    schema_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jsonschema")
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    schema = None
    with open(os.path.join(schema_dir, filename), 'r') as file:
        schema = json.load(file)

    jsonschema.validate(instance=response.json(), schema=schema)

    return

def validate_api_schema_post(url, post_data, headers, filename):
    schema_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jsonschema")
    response = requests.post(url, data=post_data, headers=headers, timeout=60)
    response.raise_for_status()

    schema = None
    with open(os.path.join(schema_dir, filename), 'r') as file:
        schema = json.load(file)

    jsonschema.validate(instance=response.json(), schema=schema)

    return

# we rely on undocumented APIs, so this smoke test those APIs for breaking changes
# if any validations fail, this will throw an error
def test_api_schemas():
    validate_api_schema_get(
        "https://sam.gov/api/prod/sgs/v1/search/?index=cfda"
            + "&page=0&mode=search&size=10000&is_active=true",
        "cfda.json"
    )

    validate_api_schema_get(
        "https://sam.gov/api/prod/fac/v1/programs/"
            + "3615edf24a7d47c283ba24536e6cf717",
        "program.json"
    )

    validate_api_schema_get(
        "https://sam.gov/api/prod/fac/v1/programs/dictionaries"
            + "?ids=match_percent,assistance_type,applicant_types,"
            + "assistance_usage_types,beneficiary_types,"
            + "cfr200_requirements&size=&filterElementIds=&keyword=",
        "dictionary.json"
    )

    validate_api_schema_get(
        "https://sam.gov/api/prod/sgs/v1/search/?index=cfda"
            + "&page=0&mode=search&size=10000&is_active=true",
        "organization_hierarchy.json"
    )

    validate_api_schema_get(
        "https://sam.gov/api/prod/federalorganizations/"
            + "v1/organizations/cf361c0196b041b7afa31dadea8d8c33",
        "organization.json"
    )

    validate_api_schema_post(
        "https://api.usaspending.gov/api/v2/autocomplete/cfda/",
        {"search_text": "a", "limit": 10000},
        {},
        "autocomplete.json"
    )

    validate_api_schema_post(
        "https://api.usaspending.gov/api/v2/references/filter/",
        json.dumps(
            {
                "filters": {
                    "keyword": {},
                    "timePeriodType": "fy",
                    "timePeriodFY": [],
                    "timePeriodStart": None,
                    "timePeriodEnd": None,
                    "newAwardsOnly": False,
                    "selectedLocations": {},
                    "locationDomesticForeign": "all",
                    "selectedFundingAgencies": {},
                    "selectedAwardingAgencies": {},
                    "selectedRecipients": [],
                    "recipientDomesticForeign": "all",
                    "recipientType": [],
                    "selectedRecipientLocations": {},
                    "awardType": [],
                    "selectedAwardIDs": {},
                    "awardAmounts": {},
                    "selectedCFDA": {
                        "84.310": {
                            "program_number": "84.310",
                            "identifier": "84.310"
                        }
                    },
                    "naicsCodes": {
                        "require": [],
                        "exclude": [],
                        "counts": []
                    },
                    "pscCodes": {
                        "require": [],
                        "exclude": [],
                        "counts": []
                    },
                    "defCodes": {
                        "require": [],
                        "exclude": [],
                        "counts": []
                    },
                    "pricingType": [],
                    "setAside": [],
                    "extentCompeted": [],
                    "treasuryAccounts": {},
                    "tasCodes": {
                        "require": [],
                        "exclude": [],
                        "counts": []
                    }
                },
                "version": "2020-06-01"
            },
            separators=(",", ":")
        ),
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; "
                        + "rv:122.0) Gecko/20100101 Firefox/122.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "X-Requested-With": "USASpendingFrontend",
            "Origin": "https://www.usaspending.gov",
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": "https://www.usaspending.gov/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        },
        "filter.json"
    )

    print("API schemas pass")

    return

def test_ip_data():
    source_path = DISK_DIRECTORY + EXTRACTED_DIRECTORY \
                  + "improper-payment-program-mapping.csv"

    if not os.path.exists(source_path):
        raise FileNotFoundError(
            "Expected mapping CSV not found at "
            + source_path
            + ". Run extract_ip_data() first, or ensure extracted seed data is present."
        )

    with open(source_path, "r", encoding="utf-8", newline="") as f:
        expected_reader = csv.reader(f)
        expected_columns = next(expected_reader, None)

    if not expected_columns:
        raise ValueError("Expected columns file is empty or missing header row.")

    response = requests.get(
        "https://paymentaccuracy.gov/assets/files/improper-payment-program-mapping.csv",
        timeout=60
    )
    response.raise_for_status()

    response_reader = csv.reader(io.StringIO(response.text))
    response_columns = next(response_reader, None)

    if not response_columns:
        raise ValueError("Response CSV is empty or missing header row.")

    missing_columns = [
        column for column in expected_columns if column not in response_columns
    ]
    if missing_columns:
        raise ValueError(
            "Response CSV is missing expected columns: "
            + ", ".join(missing_columns)
        )

    expected_column_count = len(response_columns)
    for row_index, row in enumerate(response_reader, start=2):
        # Ignore completely blank lines.
        if not any(str(cell).strip() for cell in row):
            continue
        if len(row) != expected_column_count:
            raise ValueError(
                "Row "
                + str(row_index)
                + " has "
                + str(len(row))
                + " columns; expected "
                + str(expected_column_count)
                + "."
            )

    print("IP data csv pass")

    return

def extract_assistance_listing():
    """Extracts assistance listings from SAM.gov and saves them as JSON."""
    # run an empty search on SAM.gov to get all IDs
    r = requests.get("https://sam.gov/api/prod/sgs/v1/search/?index=cfda"
                     + "&page=0&mode=search&size=10000&is_active=true",
                     timeout=60)

    # extract the SAM.gov ID for each assistance listing from the
    # search response
    listing_ids = []
    for listing in r.json()["_embedded"]["results"]:
        listing_ids.append(listing["_id"])

    # extract the JSON data for each assistance listing
    listings_json_list = []
    for listing_id in listing_ids:
        tries = 0
        status_code = 000
        try_again = False
        while (try_again and tries < 5) or (status_code != 200 and tries < 5):
            try_again = False
            tries += 1
            try:
                lr = requests.get("https://sam.gov/api/prod/fac/v1/programs/"
                                  + listing_id, timeout=60)
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ReadTimeout):
                print("Error: Connection / Timeout #" + str(tries) + " // "
                      + str(listing_id))
                status_code = 000
                time.sleep(tries)
            else:
                status_code = r.status_code
                if status_code == 200 and len(lr.text) > 0:
                    listings_json_list.append(lr.text)
                elif len(lr.text) == 0:
                    try_again = True
                    print("Error: No Content " + " // " + str(listing_id))

    # save the JSON
    with open(DISK_DIRECTORY + EXTRACTED_DIRECTORY
              + "assistance-listings.json", "w", encoding="utf-8") as f:
        f.write("["+",".join(listings_json_list)+"]")
    print("Extract Assistance Listings Complete")

def extract_ip_data():
    """Downloads the latest ALN-to-FPI mappings from paymentaccuracy.gov"""
    r = requests.get("https://paymentaccuracy.gov/assets/files/" +
                     "improper-payment-program-mapping.csv",
                     timeout=60)

    # save the csv
    with open(DISK_DIRECTORY + EXTRACTED_DIRECTORY +
              "improper-payment-program-mapping.csv", "w",
              encoding="utf-8") as f:
        f.write(r.text)
    print("Extract IP Data Complete")

def extract_dictionary():
    """Extracts an id-to-value mapping from SAM.gov for common picklists,
    such as applicant type, and saves them as JSON."""
    # extract the standard SAM.gov dictionary
    r = requests.get("https://sam.gov/api/prod/fac/v1/programs/dictionaries"
                     + "?ids=match_percent,assistance_type,applicant_types,"
                     + "assistance_usage_types,beneficiary_types,"
                     + "cfr200_requirements&size=&filterElementIds=&keyword=",
                     timeout=60)

    # save the JSON
    with open(DISK_DIRECTORY + EXTRACTED_DIRECTORY + "dictionary.json", "w",
              encoding="utf-8") as f:
        f.write(r.text)
    print("Extract Dictionary Complete")


def extract_organizations():
    """Extracts agencies from SAM.gov and saves them as JSON."""
    # run an empty search on SAM.gov to get all IDs
    r = requests.get("https://sam.gov/api/prod/sgs/v1/search/?index=cfda"
                     + "&page=0&mode=search&size=10000&is_active=true",
                     timeout=60)

    # extract the organization IDs for each assistance listing from the
    # search response
    organization_ids_set = set()
    for listing in r.json()["_embedded"]["results"]:
        if listing.get("organizationHierarchy"):
            for organization in listing["organizationHierarchy"]:
                organization_ids_set.add(organization["organizationId"])

    # extract the JSON data for each organization
    organizations_json_list = []
    for organization_id in organization_ids_set:
        lr = requests.get("https://sam.gov/api/prod/federalorganizations/"
                          + "v1/organizations/" + organization_id, timeout=60)
        org = lr.json()
        organizations_json_list.append(json.dumps(org["_embedded"][0]["org"]))

    # save the JSON
    with open(DISK_DIRECTORY + EXTRACTED_DIRECTORY + "organizations.json", "w",
              encoding="utf-8") as f:
        f.write("["+",".join(organizations_json_list)+"]")
    print("Extract Organizations Complete")


def extract_usaspending_award_hashes():
    """Extracts a hash, used for linking to USASpending.gov search results,
    for each assistance listing number."""
    programs: set = set()
    with open(DISK_DIRECTORY + EXTRACTED_DIRECTORY
              + "assistance-listings.json", encoding="utf-8") as f:
        assistance_listings_list = json.load(f)
        for l in assistance_listings_list:
            programs.add(str(l["data"]["programNumber"]))

    # function to extract the JSON data from USASpending.gov for each
    # assistance listing
    def query_usaspending_cfda(q):
        status_code = 000
        while status_code != 200:
            lr = requests.post(
                "https://api.usaspending.gov/api/v2/autocomplete/cfda/",
                data={"search_text": q, "limit": 10000}, timeout=60)
            status_code = lr.status_code
            if status_code == 200:
                return lr.json()

    # extracting by first letter allows us to significantly reduce the number
    # of calls to USASpending.gov API
    listings_json: list = []
    for c in ascii_lowercase:
        results = query_usaspending_cfda(c)
        if "results" in results:
            for r in results["results"]:
                if r["program_number"] in programs:
                    # USASpending.gov API requires this added attribute
                    r["identifier"] = r["program_number"]
                    programs.discard(r["program_number"])
                    listings_json.append(r)
                    print("AL Count: " + str(len(listings_json)))

    for p in programs:
        results = query_usaspending_cfda(p)
        if "results" in results:
            for r in results["results"]:
                if r["program_number"] == p:
                    # USASpending.gov API requires this added attribute
                    r["identifier"] = r["program_number"]
                    programs.discard(r["program_number"])
                    listings_json.append(r)
                    print("AL Count: " + str(len(listings_json)))
                else:
                    print("AL FAIL: " + p)

    # extract the hash for each program search results
    i = 0
    hashes: dict = {}
    for json_l in listings_json:
        tries = 0
        status_code = 000

        # emulate the headers of USASpending.gov frontend, to maximize
        # the success rate when hitting the API
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; "
                          + "rv:122.0) Gecko/20100101 Firefox/122.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "X-Requested-With": "USASpendingFrontend",
            "Origin": "https://www.usaspending.gov",
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": "https://www.usaspending.gov/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }

        # per USASpending.gov API documentation, the below are required,
        # even if empty
        obj = {
            "filters": {
                "keyword": {},
                "timePeriodType": "fy",
                "timePeriodFY": [],
                "timePeriodStart": None,
                "timePeriodEnd": None,
                "newAwardsOnly": False,
                "selectedLocations": {},
                "locationDomesticForeign": "all",
                "selectedFundingAgencies": {},
                "selectedAwardingAgencies": {},
                "selectedRecipients": [],
                "recipientDomesticForeign": "all",
                "recipientType": [],
                "selectedRecipientLocations": {},
                "awardType": [],
                "selectedAwardIDs": {},
                "awardAmounts": {},
                "selectedCFDA": {
                    json_l["program_number"]: json_l  # extracted program json
                },
                "naicsCodes": {
                    "require": [],
                    "exclude": [],
                    "counts": []
                },
                "pscCodes": {
                    "require": [],
                    "exclude": [],
                    "counts": []
                },
                "defCodes": {
                    "require": [],
                    "exclude": [],
                    "counts": []
                },
                "pricingType": [],
                "setAside": [],
                "extentCompeted": [],
                "treasuryAccounts": {},
                "tasCodes": {
                    "require": [],
                    "exclude": [],
                    "counts": []
                }
            },
            "version": "2020-06-01"
        }
        while status_code != 200 and tries < 5:
            tries += 1
            try:
                r = requests.post(
                    "https://api.usaspending.gov/api/v2/references/filter/",
                    data=json.dumps(obj, separators=(",", ":")),
                    headers=headers, timeout=60)
            except requests.exceptions.ReadTimeout:
                print("Read Timeout: " + str(tries) + " // "
                      + str(json_l["program_number"]))
                status_code = 000
                time.sleep(30)
            except requests.exceptions.ConnectionError:
                print("Connection Error: " + str(tries) + " // "
                      + str(json_l["program_number"]))
                status_code = 000
                time.sleep(tries)
            else:
                status_code = r.status_code
                if status_code == 200:
                    d = r.json()
                    hashes[json_l["program_number"]] = d["hash"]
                    i += 1
                    print("Hashes: " + str(i))

    # save the JSON of the hashes to be used by later scripts
    with open(DISK_DIRECTORY + EXTRACTED_DIRECTORY
              + "usaspending-program-search-hashes.json", "w",
              encoding="utf-8") as f:
        f.write(json.dumps(hashes))
    print("Extract USASpending.gov Hashes Complete")

def clean_json_data(filename):
    """Cleans and standardizes JSON data by fixing common errors and 
    standardizing text formatting.
    """
    import json
    
    # Define text corrections
    corrections = {
        'lndian': 'Indian',
    }
    
    def clean_text(text):
        """Helper function to clean individual text values."""
        if not isinstance(text, str):
            return text
        for wrong, right in corrections.items():
            text = text.replace(wrong, right)
        return text
    
    def clean_dict(d):
        """Recursively clean all string values in a dictionary."""
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [clean_dict(item) for item in d]
        elif isinstance(d, str):
            return clean_text(d)
        return d
    
    # Read the JSON file
    input_file = DISK_DIRECTORY + EXTRACTED_DIRECTORY + filename
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Clean the data
    cleaned_data = clean_dict(data)
    
    # Save cleaned data back to file
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2)
        
    print(f"Clean {filename} Complete")
    
def clean_all_data():
    """Cleans all extracted JSON data files."""
    clean_json_data("assistance-listings.json")
    clean_json_data("dictionary.json")
    print("All Data Cleaning Complete")

# Prior to running this script, data must be downloaded from USASpending.gov
# at: https://www.usaspending.gov/download_center/award_data_archive
# This data is processed in the transformation stage of the process.
def main():
    test_api_schemas()
    test_ip_data()
    extract_assistance_listing()
    extract_dictionary()
    extract_ip_data()
    clean_all_data()
    extract_organizations()
    extract_usaspending_award_hashes()
if __name__ == "__main__":
    main()