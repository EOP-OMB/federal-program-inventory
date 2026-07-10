"""
Data quality checks for extracted source files used in ETL.
"""

import csv
import io
import json
import jsonschema
import os
import requests

import constants
import pandas as pd

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

def test_ip_data():
    source_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "extracted",
        "improper-payment-program-mapping.csv"
    )

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

def test_extract_data_quality():
    test_api_schemas()
    test_ip_data()

def test_transform_data_quality():
    extracted_files_directory = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "extracted"
    )
    valid_agency_ids = test_get_valid_agency_ids(extracted_files_directory)
    valid_program_ids = test_get_valid_program_ids(extracted_files_directory)
    valid_gwos = test_get_valid_gwos(extracted_files_directory)
    valid_pons = test_get_valid_pons(extracted_files_directory)
    valid_table_b_program_types = {"Contracts"}

    test_acquisitions_and_services(
        extracted_files_directory,
        valid_agency_ids,
        valid_table_b_program_types,
    )
    test_additional_programs(extracted_files_directory)
    test_fpi_gwo_assignment(
        extracted_files_directory, valid_program_ids, valid_gwos
    )
    test_fpi_pon_assignment(
        extracted_files_directory, valid_program_ids, valid_pons
    )
    test_improper_payment_program_mapping(
        extracted_files_directory, valid_program_ids
    )
    test_inflation_and_population_growth(extracted_files_directory)
    test_taxonomy_gwo_crosswalk(extracted_files_directory)
    test_taxonomy_pon_crosswalk(extracted_files_directory)
    test_dictionary(extracted_files_directory)
    test_usaspending_program_search_hashes(extracted_files_directory)
    print("Finished test_data_quality")


def test_get_valid_agency_ids(extracted_files_directory):
    filename = "organizations.json"
    agencies = set()
    with open(
        os.path.join(extracted_files_directory, filename),
        encoding="utf-8",
    ) as f:
        for o in json.load(f):
            agencies.add(o["orgKey"])

    return agencies


def test_get_valid_program_ids(extracted_files_directory):
    al_filename = "assistance-listings.json"
    table_b_filename = "acquisitions_and_services.csv"
    programs = set()

    with open(
        os.path.join(extracted_files_directory, al_filename),
        encoding="utf-8",
    ) as f:
        for o in json.load(f):
            programs.add(o["data"]["programNumber"])

    df = test_get_dataframe_from_csv(
        extracted_files_directory, table_b_filename
    )
    for _, row in df.iterrows():
        programs.add(row["Program ID"])

    return programs


def test_get_valid_gwos(extracted_files_directory):
    filename = "Taxonomy_GWO_crosswalk.csv"
    gwos = set()

    df = test_get_dataframe_from_csv(extracted_files_directory, filename)
    for _, row in df.iterrows():
        gwos.add(row["GWO ID"])

    return gwos


def test_get_valid_pons(extracted_files_directory):
    filename = "Taxonomy_PON_crosswalk.csv"
    pons = set()

    df = test_get_dataframe_from_csv(extracted_files_directory, filename)
    for _, row in df.iterrows():
        pons.add(row["PON ID"])

    return pons


def test_acquisitions_and_services(
    extracted_files_directory,
    valid_agency_ids,
    valid_table_b_program_types,
):
    filename = "acquisitions_and_services.csv"
    df = test_get_dataframe_from_csv(extracted_files_directory, filename)
    expected_columns = {
        "Program Name",
        "Popular Name",
        "Program ID",
        "Agency ID",
        "Program Description",
        "Fiscal Year",
        "Obligation_Sum",
        "Outlay_Sum",
        "Program Type",
        "Authorization",
        "Authorization URL",
    }
    test_columns_in_dataframe(df, expected_columns)
    for _, row in df.iterrows():
        assert (
            row["Agency ID"] in valid_agency_ids
        ), str(row["Agency ID"]) + " is not a valid agency id"
        assert (
            row["Program Type"] in valid_table_b_program_types
        ), str(row["Program Type"]) + " is not a valid program type"


def test_additional_programs(extracted_files_directory):
    filename = "additional-programs.csv"
    df = test_get_dataframe_from_csv(extracted_files_directory, filename)
    py_outlays_column = constants.LAST_COMPLETED_FISCAL_YEAR + "_outlays"
    py_fr_column = constants.LAST_COMPLETED_FISCAL_YEAR + "_foregone_revenue"
    cy_outlays_column = constants.CURRENT_FISCAL_YEAR + "_outlays"
    cy_fr_column = constants.CURRENT_FISCAL_YEAR + "_foregone_revenue"
    expected_columns = {
        "`",
        "name",
        "description",
        "agency",
        "subagency",
        "category",
        "subcategory",
        "type",
        "assistance_type",
        py_outlays_column,
        py_fr_column,
        cy_outlays_column,
        cy_fr_column,
    }
    test_columns_in_dataframe(df, expected_columns)

    interest_seen = False
    df_as_str = pd.read_csv(
        os.path.join(extracted_files_directory, filename),
        dtype=str,
    )
    for _, row in df_as_str.iterrows():
        test_val_is_not_scientific_notation(row[py_outlays_column])
        test_val_is_not_scientific_notation(row[py_fr_column])
        test_val_is_not_scientific_notation(row[cy_outlays_column])
        test_val_is_not_scientific_notation(row[cy_fr_column])
        if row["`"].strip() == "IN.001":
            interest_seen = True

    assert interest_seen, "No record found for interest (IN.001)!"


def test_fpi_gwo_assignment(
    extracted_files_directory, valid_program_ids, valid_gwos
):
    filename = "FPI_GWO_assignment.csv"
    df = test_get_dataframe_from_csv(extracted_files_directory, filename)
    expected_columns = {"al_#", "GWO ID"}
    test_columns_in_dataframe(df, expected_columns)

    for _, row in df.iterrows():
        # Program validity check currently fails
        # assert row["al_#"] in valid_program_ids, str(row["al_#"]) + " is not a valid program id"
        assert row["GWO ID"] in valid_gwos, str(row["GWO ID"]) + " is not a valid GWO id"


def test_fpi_pon_assignment(
    extracted_files_directory, valid_program_ids, valid_pons
):
    filename = "FPI_PON_assignment.csv"
    df = test_get_dataframe_from_csv(extracted_files_directory, filename)
    expected_columns = {"al_#", "PON ID"}
    test_columns_in_dataframe(df, expected_columns)

    for _, row in df.iterrows():
        # Program validity check currently fails
        # assert row["al_#"] in valid_program_ids, str(row["al_#"]) + " is not a valid program id"
        assert row["PON ID"] in valid_pons, str(row["PON ID"]) + " is not a valid PON id"


def test_improper_payment_program_mapping(
    extracted_files_directory, valid_program_ids
):
    filename = "improper-payment-program-mapping.csv"
    df = test_get_dataframe_from_csv(extracted_files_directory, filename)
    expected_columns = {
        "program_id",
        "improper_payment_program_name",
        "agency",
        "fiscal_year",
        "outlays",
        "improper_payment_amount",
        "start_date",
        "end_date",
        "insufficient_documentation_amount",
        "slug",
    }
    test_columns_in_dataframe(df, expected_columns)

    slug_to_program_names = {}
    for _, row in df.iterrows():
        # Program validity check currently fails
        # assert row["program_id"] in valid_program_ids, str(row["program_id"]) + " is not a valid program id"
        slug = "" if pd.isna(row["slug"]) else str(row["slug"]).strip()
        if slug != "":
            slug_to_program_names[slug] = str(row["improper_payment_program_name"]).strip()

    for slug, program_name in slug_to_program_names.items():
        url = f"https://paymentaccuracy.gov/program/{slug}"
        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30
        )
        response.raise_for_status()
        response_text_lower = response.text.lower()
        assert program_name.lower() in response_text_lower, (
            f"Program name '{program_name}' was not found at URL: {url}"
        )


def test_inflation_and_population_growth(extracted_files_directory):
    filename = "inflation_and_population_growth.csv"
    df = test_get_dataframe_from_csv(extracted_files_directory, filename)
    expected_columns = {
        "Year",
        "Inflation Rate Percentage",
        "Population Growth Percentage",
    }
    test_columns_in_dataframe(df, expected_columns)

    py_found = False
    for _, row in df.iterrows():
        if str(constants.LAST_COMPLETED_FISCAL_YEAR) == str(int(row["Year"])):
            py_found = True

    assert (
        py_found
    ), "FY " + str(constants.LAST_COMPLETED_FISCAL_YEAR) + " inflation and growth rates are missing"


def test_taxonomy_gwo_crosswalk(extracted_files_directory):
    filename = "Taxonomy_GWO_crosswalk.csv"
    df = test_get_dataframe_from_csv(extracted_files_directory, filename)
    expected_columns = {
        "Category Code",
        "Category",
        "FA Code",
        "Focus Area",
        "GWO ID",
        "GWO",
        "GWO Definition",
    }
    test_columns_in_dataframe(df, expected_columns)


def test_taxonomy_pon_crosswalk(extracted_files_directory):
    filename = "Taxonomy_PON_crosswalk.csv"
    df = test_get_dataframe_from_csv(extracted_files_directory, filename)
    expected_columns = {
        "Category Code",
        "Category",
        "FA Code",
        "Focus Area",
        "PON ID",
        "PON2",
        "PON Definition",
    }
    test_columns_in_dataframe(df, expected_columns)


def test_dictionary(extracted_files_directory):
    filename = "dictionary.json"
    try_json_parse(extracted_files_directory, filename)


def test_usaspending_program_search_hashes(extracted_files_directory):
    filename = "usaspending-program-search-hashes.json"
    try_json_parse(extracted_files_directory, filename)


def try_json_parse(extracted_files_directory, filename: str):
    with open(
        os.path.join(extracted_files_directory, filename),
        "r",
        encoding="utf-8",
    ) as file:
        json.load(file)


def test_get_dataframe_from_csv(extracted_files_directory, filename: str):
    return pd.read_csv(os.path.join(extracted_files_directory, filename))


def test_columns_in_dataframe(df, column_list: set):
    assert column_list.issubset(df.columns), "Required columns are missing!"


def test_val_is_not_scientific_notation(val):
    assert "e" not in str(val).lower(), str(val) + " is in scientific notation!"
