"""
Extracts program information from various sources (e.g., SAM.gov).
"""

import json
import time
from string import ascii_lowercase
import requests
import pandas as pd
from tabula import read_pdf

# file paths
DISK_DIRECTORY = "/Users/codyreinold/Code/omb/offm/will-fpi/"
SOURCE_DIRECTORY = "federal-program-inventory/data_processing/source/"
EXTRACTED_DIRECTORY = "federal-program-inventory/data_processing/extracted/"


def extract_categories_from_pdf(year, debug=False):
    """Extracts the programs in each category / sub-category from the PDF."""
    data_values = read_pdf(
        DISK_DIRECTORY + SOURCE_DIRECTORY + year
        + "-assistance-listing-catalog.pdf",
        output_format="dataframe",
        pandas_options={"header": None},
        pages=["151-210"],
        stream=True,
        multiple_tables=False,
        area=[[55, 60, 735, 90], [55, 310, 735, 340]],
        encoding="utf-8"
    )
    data_values = data_values[0]

    # remove a handful of outliers from page one that precede the template
    # these are valid for 2023 but must be updated for future PDFs
    data_values = data_values.drop(range(0, 19))
    data_values = data_values.drop(56).reset_index(drop=True)

    # load in the 2023 functions list
    functions_df = pd.read_csv(DISK_DIRECTORY + SOURCE_DIRECTORY + year
                               + "-functions-list.csv", header=None)

    # loop through each of the values to assign the full function and
    # sub-function
    parent = ""  # tracks the current function
    child = ""  # tracks the current sub-function
    parent_col = []
    child_col = []
    remove_rows = []
    all_subcategories = []  # tracks the "all subcategories" rows
    function_index = 0
    data_index = 0

    # Two category/subcategory combinations break onto two lines in the
    # PDF and the second line must be ignored in progression of
    # category/subcategory.
    # Education,Resource Development and Support -
    #    General and Special Interest Organizations
    # Education,Resource Development and Support -
    #    Vocational Education and Handicapped Education
    for row in data_values[0]:
        if data_index in [2213, 2364]:  # if row is a two-line sub-function
            parent_col.append("")
            child_col.append("")
            remove_rows.append(data_index)
        elif row[0].isdigit():  # if row is a program number
            parent_col.append(parent)
            if child.startswith("All subcategories"):
                all_subcategories.append([row, parent])
                remove_rows.append(data_index)
            child_col.append(child)
        elif row.isupper():  # if row is a function
            parent_col.append("")
            child_col.append("")
            remove_rows.append(data_index)
        else:  # if row is a sub-function
            r = functions_df.loc[function_index]
            function_index += 1
            if debug is True and not r[1].startswith(row):  # for debug
                print("\n".join([data_index, function_index-1, row, r[1],
                                 parent, "----------"]))
            parent = r[0]
            child = r[1]
            parent_col.append("")
            child_col.append("")
            remove_rows.append(data_index)
        data_index += 1

    # create dict of functions / sub-functions
    functions_dict = {}
    for x in zip(functions_df[0], functions_df[1]):
        if x[0] not in functions_dict:
            functions_dict[x[0]] = []
        if not x[1].startswith("All subcategories"):
            functions_dict[x[0]].append(x[1])

    # loop through those tagged as having all sub-functions apply and
    # insert rows
    new_vals = []
    for val in all_subcategories:
        for subcat in functions_dict[val[1]]:
            new_vals.append(val[0])
            parent_col.append(val[1])
            child_col.append(subcat)

    # append new columns to dataframe
    data_values = pd.concat([data_values, pd.DataFrame(new_vals)],
                            ignore_index=True)
    data_values[1] = parent_col
    data_values[2] = child_col

    # drop the unnecessary rows and convert to csv
    data_values.drop(remove_rows).reset_index(drop=True).to_csv(
        DISK_DIRECTORY + EXTRACTED_DIRECTORY
        + "program-to-function-sub-function.csv", index=False, header=False)

    print("Extract PDF Categories Complete")


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
        while status_code != 200 and tries < 5:
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
                    print("Error: No Content " + " // " + str(listing_id))

    # save the JSON
    with open(DISK_DIRECTORY + EXTRACTED_DIRECTORY
              + "assistance-listings.json", "w", encoding="utf-8") as f:
        f.write("["+",".join(listings_json_list)+"]")
    print("Extract Assistance Listings Complete")


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

# Uncomment the necessary functions to extract new data.
#
# extract_categories_from_pdf("2023")
# extract_assistance_listing()

# extract_dictionary()
# clean_all_data()
# extract_organizations()
# extract_usaspending_award_hashes()

# In addition to functions above, data must be downloaded from USASpending.gov
# at: https://www.usaspending.gov/download_center/award_data_archive
# This data is processed in the transformation stage of the process.
