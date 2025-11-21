"""
Transform extracted program information and store the transformed
information in a SQLite database for generation of markdown files.
"""

import csv
import json
import os
import sqlite3
import constants
import pandas as pd

# temporary (large) database file paths
TEMP_DB_DISK_DIRECTORY = "./Volumes/CER01/"
TEMP_DB_FILE_PATH = "temp_data.db"

# transformed database, for use in the load / generate stage
TRANSFORMED_FILES_DIRECTORY = "transformed/"
TRANSFORMED_DB_FILE_PATH = "transformed_data.db"

# usaspending file paths; these riles are not stored in the primary
# report because of the files sizes and limits of LFS
USASPENDING_DISK_DIRECTORY = "./Volumes/CER01/"
ASSISTANCE_EXTRACTED_FILES_DIRECTORY = "extracted/assistance"
ASSISTANCE_DELTA_FILES_DIRECTORY = "extracted/delta/assistance"
CONTRACT_EXTRACTED_FILES_DIRECTORY = "extracted/contract"
CONTRACT_DELTA_FILES_DIRECTORY = "extracted/delta/contract"

# extracted file paths
REPO_DISK_DIRECTORY = ""
EXTRACTED_FILES_DIRECTORY = "extracted/"

# additional programs dataset path
ADDITIONAL_PROGRAMS_DATA_PATH = REPO_DISK_DIRECTORY \
                                + EXTRACTED_FILES_DIRECTORY \
                                + "additional-programs.csv"

USASPENDING_ASSISTANCE_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS usaspending_assistance;
    """

USASPENDING_ASSISTANCE_CREATE_TABLE_SQL = """
    CREATE TABLE usaspending_assistance (
        assistance_transaction_unique_key NOT NULL PRIMARY KEY,
        assistance_award_unique_key, federal_action_obligation,
        total_outlayed_amount_for_overall_award, action_date_fiscal_year,
        prime_award_transaction_place_of_performance_cd_current,
        cfda_number, assistance_type_code
    );
    """

USASPENDING_CONTRACT_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS usaspending_contract;
    """

USASPENDING_CONTRACT_CREATE_TABLE_SQL = """
    CREATE TABLE usaspending_contract (
        contract_transaction_unique_key NOT NULL PRIMARY KEY,
        contract_award_unique_key, federal_action_obligation,
        total_outlayed_amount_for_overall_award, action_date_fiscal_year,
        funding_agency_code, funding_agency_name, funding_sub_agency_code,
        funding_sub_agency_name, funding_office_code, funding_office_name,
        prime_award_transaction_place_of_performance_cd_current,
        award_type_code
    );
    """

USASPENDING_ASSISTANCE_INSERT_SQL = """
    INSERT INTO usaspending_assistance
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """

USASPENDING_CONTRACT_INSERT_SQL = """
    INSERT INTO usaspending_contract VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

USASPENDING_ASSISTANCE_DELETE_SQL = """
    DELETE FROM usaspending_assistance
    WHERE assistance_transaction_unique_key = ?;
    """

USASPENDING_CONTRACT_DELETE_SQL = """
    DELETE FROM usaspending_contract
    WHERE contract_transaction_unique_key = ?;
    """

ATTACH_TEMPORARY_DB_TO_TRANSFORMED_DB_SQL = f"""
    ATTACH DATABASE '{TEMP_DB_DISK_DIRECTORY}{TEMP_DB_FILE_PATH}' AS temp_db;
    """

AGENCY_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS agency;
    """

AGENCY_CREATE_TABLE_SQL = """
    CREATE TABLE agency (
        id INTEGER NOT NULL PRIMARY KEY, agency_name TEXT,
        tier_1_agency_id INTEGER, tier_2_agency_id INTEGER,
        is_cfo_act_agency INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(tier_1_agency_id) REFERENCES agency(id),
        FOREIGN KEY(tier_2_agency_id) REFERENCES agency(id)
    );
    """

AGENCY_INSERT_SQL = """
    INSERT INTO agency
    VALUES (?, ?, ?, ?, ?);
    """

CATEGORY_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS category;
    """

CATEGORY_CREATE_TABLE_SQL = """
    CREATE TABLE category (
        id TEXT NOT NULL,
        type TEXT NOT NULL,
        name TEXT NOT NULL,
        parent_id TEXT,
        PRIMARY KEY(id, type),
        FOREIGN KEY(parent_id, type) REFERENCES category(id, type)
    );
    """

CATEGORY_FIND_SQL = """
    SELECT id FROM category WHERE type = ? AND name = ?
"""

CATEGORY_INSERT_SQL = """
    INSERT INTO category
    VALUES (?, ?, ?, ?);
    """

PROGRAM_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS program;
    """

PROGRAM_CREATE_TABLE_SQL = """
    CREATE TABLE program (
        id TEXT NOT NULL PRIMARY KEY,
        agency_id INTEGER,
        name TEXT,
        popular_name TEXT,
        objective TEXT,
        sam_url TEXT,
        usaspending_awards_hash TEXT,
        usaspending_awards_url TEXT,
        grants_url TEXT,
        program_type TEXT,
        is_subpart_f BOOLEAN,
        rules_regulations TEXT,
        FOREIGN KEY(agency_id) REFERENCES agency(id)
    );
    """

PROGRAM_INSERT_SQL = """
    INSERT INTO program
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

PROGRAM_AUTHORIZATION_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS program_authorization;
    """

PROGRAM_AUTHORIZATION_CREATE_TABLE_SQL = """
    CREATE TABLE program_authorization (
        program_id TEXT NOT NULL,
        text TEXT,
        url TEXT,
        FOREIGN KEY(program_id) REFERENCES program(id)
    );
    """

PROGRAM_AUTHORIZATION_INSERT_SQL = """
    INSERT INTO program_authorization
    VALUES (?, ?, ?);
    """

PROGRAM_RESULT_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS program_result;
    """

PROGRAM_RESULT_CREATE_TABLE_SQL = """
    CREATE TABLE program_result (
        program_id TEXT NOT NULL,
        fiscal_year INTEGER NOT NULL,
        result TEXT NOT NULL,
        PRIMARY KEY (program_id, fiscal_year),
        FOREIGN KEY(program_id) REFERENCES program(id)
    );
    """

PROGRAM_RESULT_INSERT_SQL = """
    INSERT INTO program_result VALUES (?, ?, ?);
    """

PROGRAM_SAM_SPENDING_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS program_sam_spending;
    """

PROGRAM_SAM_SPENDING_CREATE_TABLE_SQL = """
    CREATE TABLE program_sam_spending (
        program_id TEXT NOT NULL,
        assistance_type TEXT,
        category_type TEXT,
        fiscal_year INTEGER NOT NULL,
        is_actual INTEGER NOT NULL,
        amount REAL NOT NULL,
        PRIMARY KEY (program_id, assistance_type, fiscal_year, is_actual),
        FOREIGN KEY(program_id) REFERENCES program(id)
        FOREIGN KEY(assistance_type, category_type) REFERENCES category(id, type)
    );
    """

PROGRAM_SAM_SPENDING_INSERT_SQL = """
    INSERT INTO program_sam_spending
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT DO UPDATE SET amount=amount+?;
    """

PROGRAM_TO_CATEGORY_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS program_to_category;
    """

PROGRAM_TO_CATEGORY_CREATE_TABLE_SQL = """
    CREATE TABLE program_to_category (
        program_id TEXT NOT NULL,
        category_id TEXT NOT NULL,
        category_type TEXT NOT NULL,
        PRIMARY KEY (program_id, category_id, category_type),
        FOREIGN KEY(program_id) REFERENCES program(id)
        FOREIGN KEY(category_id, category_type) REFERENCES category(id, type)
    );
    """

PROGRAM_TO_CATEGORY_INSERT_SQL = """
    INSERT INTO program_to_category
    VALUES (?, ?, ?) ON CONFLICT DO NOTHING;
    """

TAXONOMY_CATEGORY_CREATE_TABLE_SQL = """
    CREATE TABLE taxonomy_category (
        id TEXT NOT NULL PRIMARY KEY,
        category TEXT NOT NULL UNIQUE
    )
"""

TAXONOMY_CATEGORY_INSERT_TABLE_SQL = """
    INSERT INTO taxonomy_category
    -- dash is later used as a delimiter between category and focus area
    VALUES (?, REPLACE(?,'-','–')) ON CONFLICT DO NOTHING;
"""

TAXONOMY_CATEGORY_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS taxonomy_category;
    """

TAXONOMY_FOCUS_AREA_CREATE_TABLE_SQL = """
    CREATE TABLE taxonomy_focus_area (
        id TEXT NOT NULL PRIMARY KEY,
        focus_area TEXT NOT NULL UNIQUE,
        category_id TEXT NOT NULL,
        FOREIGN KEY(category_id) REFERENCES taxonomy_category(id)
    )
"""

TAXONOMY_FOCUS_AREA_INSERT_TABLE_SQL = """
    INSERT INTO taxonomy_focus_area
    -- dash is later used as a delimiter between category and focus area
    VALUES (?, REPLACE(?,'-','–'), ?) ON CONFLICT DO NOTHING;
"""

TAXONOMY_FOCUS_AREA_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS taxonomy_focus_area;
    """

GWO_CREATE_TABLE_SQL = """
    CREATE TABLE gwo (
        id TEXT NOT NULL PRIMARY KEY,
        gwo TEXT NOT NULL,
        gwo_definition TEXT NOT NULL,
        focus_area_id TEXT NOT NULL,
        FOREIGN KEY(focus_area_id) REFERENCES focus_area(id)
    );
"""

GWO_INSERT_TABLE_SQL = """
    INSERT INTO gwo
    VALUES (?, ?, ?, ?);
"""

GWO_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS gwo;
    """

PON_CREATE_TABLE_SQL = """
    CREATE TABLE pon (
        id TEXT NOT NULL PRIMARY KEY,
        pon2 TEXT NOT NULL,
        pon_definition TEXT NOT NULL,
        focus_area_id TEXT NOT NULL,
        FOREIGN KEY(focus_area_id) REFERENCES focus_area(id)
    );
"""

PON_INSERT_TABLE_SQL = """
    INSERT INTO pon
    VALUES (?, ?, ?, ?);
"""

PON_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS pon;
    """

PROGRAM_TO_GWO_CREATE_TABLE_SQL = """
    CREATE TABLE program_to_gwo (
        program_id TEXT NOT NULL,
        gwo_id TEXT NOT NULL,
        FOREIGN KEY(program_id) REFERENCES program(id)
        FOREIGN KEY(gwo_id) REFERENCES gwo(id)
    );
"""

PROGRAM_TO_GWO_INSERT_TABLE_SQL = """
    INSERT INTO program_to_gwo
    VALUES (?, ?);
"""

PROGRAM_TO_GWO_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS program_to_gwo;
    """

PROGRAM_TO_PON_CREATE_TABLE_SQL = """
    CREATE TABLE program_to_pon (
        program_id TEXT NOT NULL,
        pon_id TEXT NOT NULL,
        FOREIGN KEY(program_id) REFERENCES program(id)
        FOREIGN KEY(pon_id) REFERENCES pon(id)
    );
"""

PROGRAM_TO_PON_INSERT_TABLE_SQL = """
    INSERT INTO program_to_pon
    VALUES (?, ?);
"""

PROGRAM_TO_PON_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS program_to_pon;
    """

PROGRAM_TAXONOMY_LOOKUP_DROP_VIEW_SQL = """
    DROP VIEW IF EXISTS program_taxonomy_lookup;
"""

PROGRAM_TAXONOMY_LOOKUP_CREATE_VIEW_SQL = """
    CREATE VIEW program_taxonomy_lookup AS
        SELECT
            program.id AS program_id,
            taxonomy_focus_area.id AS taxonomy_focus_area_id,
            taxonomy_category.id AS taxonomy_category_id
        FROM program
        JOIN program_to_gwo ON program.id = program_to_gwo.program_id
        JOIN gwo on program_to_gwo.gwo_id = gwo.id
        JOIN taxonomy_focus_area ON gwo.focus_area_id = taxonomy_focus_area.id
        JOIN taxonomy_category ON taxonomy_focus_area.category_id = taxonomy_category.id
    UNION
        SELECT DISTINCT
            other_program_spending.program_id,
            other_program_spending.focus_area_id AS taxonomy_focus_area_id,
            taxonomy_category.id AS taxonomy_category_id
        FROM other_program_spending
        JOIN taxonomy_focus_area ON other_program_spending.focus_area_id = taxonomy_focus_area.id
        JOIN taxonomy_category ON taxonomy_focus_area.category_id = taxonomy_category.id
"""

USASPENDING_ASSISTANCE_OBLIGATION_AGGEGATION_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS usaspending_assistance_obligation_aggregation;
    """

USASPENDING_ASSISTANCE_OBLIGATION_AGGEGATION_CREATE_TABLE_SQL = """
    CREATE TABLE usaspending_assistance_obligation_aggregation (
        cfda_number TEXT NOT NULL,
        action_date_fiscal_year INT NOT NULL,
        assistance_type_code INT NOT NULL,
        congressional_district TEXT,
        obligations REAL NOT NULL,
        FOREIGN KEY(cfda_number) REFERENCES program(id)
    );
    """

USASPENDING_ASSISTANCE_OBLIGATION_AGGEGATION_SELECT_AND_INSERT_SQL = """
    INSERT INTO usaspending_assistance_obligation_aggregation (cfda_number,
        action_date_fiscal_year, assistance_type_code, congressional_district,
        obligations)
    SELECT
        cfda_number, action_date_fiscal_year, assistance_type_code,
        prime_award_transaction_place_of_performance_cd_current AS
        congressional_district, SUM(federal_action_obligation) AS obligations
    FROM temp_db.usaspending_assistance
    GROUP BY
        cfda_number, action_date_fiscal_year, assistance_type_code,
        congressional_district;
    """

USASPENDING_ASSISTANCE_OUTLAY_AGGEGATION_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS usaspending_assistance_outlay_aggregation;
    """

USASPENDING_ASSISTANCE_OUTLAY_AGGEGATION_CREATE_TABLE_SQL = """
    CREATE TABLE usaspending_assistance_outlay_aggregation (
        cfda_number TEXT NOT NULL,
        award_first_fiscal_year INT NOT NULL,
        outlay REAL NOT NULL,
        obligation REAL NOT NULL,
        FOREIGN KEY(cfda_number) REFERENCES program(id)
    );
    """

# At this time, only the total of outlayed funds per award is available from
# USASpending.gov. This means it is not possible to aggregate outlays in the
# same way that obligations are aggregated (i.e., by transaction action date).
# Because of this, outlays must be aggregated by a consistent date figure, to
# ensure they're not double counted and can be displayed consistently.
# Aggregating by period of performance is not possible, as not all awards have
# period of performance start dates. As a result, in this query outlays and
# obligations are aggregated based on the first transaction action date for
# each award. This means that obligation figures will be different between this
# query and the query used to power the primary display, but this methodology
# allows for a more consistent comparison between obligated and outlayed funds,
# by year.
USASPENDING_ASSISTANCE_OUTLAY_AGGEGATION_SELECT_AND_INSERT_SQL = """
    INSERT INTO usaspending_assistance_outlay_aggregation (cfda_number,
        award_first_fiscal_year, outlay, obligation)
    SELECT
        cfda_number, award_first_fiscal_year, SUM(award_outlay) AS outlay,
        SUM(award_obligation) as obligation
    FROM (
        SELECT
            cfda_number, assistance_award_unique_key,
            MIN(action_date_fiscal_year) AS award_first_fiscal_year,
            total_outlayed_amount_for_overall_award AS award_outlay,
            SUM(federal_action_obligation) AS award_obligation
        FROM temp_db.usaspending_assistance
        GROUP BY cfda_number, assistance_award_unique_key
    )
    GROUP BY cfda_number, award_first_fiscal_year;
    """

USASPENDING_ASSISTANCE_OUTLAY_AGGREGATION_DIRECT_INSERT_SQL = """
    INSERT INTO usaspending_assistance_outlay_aggregation
    VALUES (?, ?, ?, ?);
"""

OTHER_PROGRAM_SPENDING_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS other_program_spending;
    """

OTHER_PROGRAM_SPENDING_CREATE_TABLE_SQL = """
    CREATE TABLE other_program_spending (
        program_id TEXT NOT NULL,
        fiscal_year INTEGER NOT NULL,
        outlays REAL,
        forgone_revenue REAL,
        source TEXT NOT NULL,
        focus_area_id TEXT NOT NULL,
        PRIMARY KEY (program_id, fiscal_year),
        FOREIGN KEY(program_id) REFERENCES program(id)
        FOREIGN KEY(focus_area_id) REFERENCES focus_area(id)
    );
    """

OTHER_PROGRAM_SPENDING_INSERT_SQL = """
    INSERT INTO other_program_spending
    VALUES (?, ?, ?, ?, ?, ?);
    """

IMPROPER_PAYMENT_MAPPING_DROP_TABLE_SQL = """
    DROP TABLE IF EXISTS improper_payment_mapping;
"""

IMPROPER_PAYMENT_MAPPING_CREATE_TABLE_SQL = """
    CREATE TABLE improper_payment_mapping (
        program_id TEXT NOT NULL,
        improper_payment_program_name TEXT,
        outlays DECIMAL,
        improper_payment_amount DECIMAL,
        insufficient_documentation_amount DECIMAL,
        high_priority_program INTEGER,
        FOREIGN KEY(program_id) REFERENCES program(id)
    );
"""

# establish a database connection to store temporary working data
temp_conn = sqlite3.connect(TEMP_DB_DISK_DIRECTORY + TEMP_DB_FILE_PATH)
temp_cur = temp_conn.cursor()

# establish a database connection to store transformed data that is used
# in the load / generate stage
conn = sqlite3.connect(TRANSFORMED_FILES_DIRECTORY + TRANSFORMED_DB_FILE_PATH)
cur = conn.cursor()

# attach the temporary database to the transformed database, to allow for
# efficient transferring of data
cur.execute(ATTACH_TEMPORARY_DB_TO_TRANSFORMED_DB_SQL)
conn.commit()


def convert_to_url_string(s):
    """Converts a string (e.g., category name) to a URL-safe string"""
    return "".join(c if c.isalnum() else "-" for c in s.lower())


def load_usaspending_initial_files():
    """Loads non-delta USASpending.gov CSV files into a SQLite Database for
    further transformation."""

    # create assistance table for USASpending.gov data
    temp_cur.execute(USASPENDING_ASSISTANCE_DROP_TABLE_SQL)
    temp_cur.execute(USASPENDING_ASSISTANCE_CREATE_TABLE_SQL)
    temp_conn.commit()

    # create contracts table for USASpending.gov data
    temp_cur.execute(USASPENDING_CONTRACT_DROP_TABLE_SQL)
    temp_cur.execute(USASPENDING_CONTRACT_CREATE_TABLE_SQL)
    temp_conn.commit()

    # load assistance data; the list is sorted to ensure files are processed
    # in chronological order
    for file in sorted(os.listdir(USASPENDING_DISK_DIRECTORY
                                  + ASSISTANCE_EXTRACTED_FILES_DIRECTORY)):
        print(file)
        if file[0] != ".":
            with open(USASPENDING_DISK_DIRECTORY
                      + ASSISTANCE_EXTRACTED_FILES_DIRECTORY + file, "r",
                      encoding="latin-1") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    temp_cur.execute(USASPENDING_ASSISTANCE_INSERT_SQL, [
                        r["assistance_transaction_unique_key"],
                        r["assistance_award_unique_key"],
                        r["federal_action_obligation"],
                        r["total_outlayed_amount_for_overall_award"],
                        r["action_date_fiscal_year"],
                        r["prime_award_transaction_place_of_"
                            + "performance_cd_current"],
                        r["cfda_number"],
                        r["assistance_type_code"]
                    ])
                temp_conn.commit()

    # load contract data; the list is sorted to ensure files are processed
    # in chronological order
    for file in sorted(os.listdir(USASPENDING_DISK_DIRECTORY
                       + CONTRACT_EXTRACTED_FILES_DIRECTORY)):
        print(file)
        if file[0] != ".":
            with open(USASPENDING_DISK_DIRECTORY
                      + CONTRACT_EXTRACTED_FILES_DIRECTORY
                      + file, "r", encoding="latin-1") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    temp_cur.execute(USASPENDING_CONTRACT_INSERT_SQL, [
                        r["contract_transaction_unique_key"],
                        r["contract_award_unique_key"],
                        r["federal_action_obligation"],
                        r["total_outlayed_amount_for_overall_award"],
                        r["action_date_fiscal_year"],
                        r["funding_agency_code"],
                        r["funding_agency_name"],
                        r["funding_sub_agency_code"],
                        r["funding_sub_agency_name"],
                        r["funding_office_code"],
                        r["funding_office_name"],
                        r["prime_award_transaction_place_of_"
                            + "performance_cd_current"],
                        r["award_type_code"]
                    ])
                temp_conn.commit()


def load_usaspending_delta_files():
    """Loads delta USASpending.gov CSV files into a SQLite Database for
    further transformation."""
    # load assistance data; the list is sorted to ensure files are processed
    # in chronological order
    for file in sorted(os.listdir(USASPENDING_DISK_DIRECTORY
                                  + ASSISTANCE_DELTA_FILES_DIRECTORY)):
        print(file)
        if file[0] != ".":
            with open(USASPENDING_DISK_DIRECTORY
                      + ASSISTANCE_DELTA_FILES_DIRECTORY
                      + file, "r", encoding="latin-1") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    temp_cur.execute(USASPENDING_ASSISTANCE_DELETE_SQL,
                                     [r["assistance_transaction_unique_key"]])
                    # if "C" (change) or "" (add), insert new DB row
                    if r["correction_delete_ind"] in ["", "C"]:
                        temp_cur.execute(USASPENDING_ASSISTANCE_INSERT_SQL, [
                            r["assistance_transaction_unique_key"],
                            r["assistance_award_unique_key"],
                            r["federal_action_obligation"],
                            r["total_outlayed_amount_for_overall_award"],
                            r["action_date_fiscal_year"],
                            r["prime_award_transaction_place_of_"
                                + "performance_cd_current"],
                            r["cfda_number"],
                            r["assistance_type_code"],
                        ])
                temp_conn.commit()

    # load contract data; the list is sorted to ensure files are processed
    # in chronological order
    for file in sorted(os.listdir(USASPENDING_DISK_DIRECTORY
                                  + CONTRACT_DELTA_FILES_DIRECTORY)):
        print(file)
        if file[0] != ".":
            with open(USASPENDING_DISK_DIRECTORY
                      + CONTRACT_DELTA_FILES_DIRECTORY
                      + file, "r", encoding="latin-1") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    temp_cur.execute(USASPENDING_CONTRACT_DELETE_SQL,
                                     [r["contract_transaction_unique_key"]])
                    temp_conn.commit()
                    # if "C" (change) or "" (add), insert new DB row
                    if r["correction_delete_ind"] in ["", "C"]:
                        temp_cur.execute(USASPENDING_CONTRACT_INSERT_SQL, [
                            r["contract_transaction_unique_key"],
                            r["contract_award_unique_key"],
                            r["federal_action_obligation"],
                            r["total_outlayed_amount_for_overall_award"],
                            r["action_date_fiscal_year"],
                            r["funding_agency_code"],
                            r["funding_agency_name"],
                            r["funding_sub_agency_code"],
                            r["funding_sub_agency_name"],
                            r["funding_office_code"],
                            r["funding_office_name"],
                            r["prime_award_transaction_place_of_"
                                + "performance_cd_current"],
                            r["award_type_code"]
                        ])
                temp_conn.commit()


def transform_and_insert_usaspending_aggregation_data():
    """Queries USASpending.gov data in the temporary database and inserts the
    results into the transformed database."""
    cur.execute(USASPENDING_ASSISTANCE_OBLIGATION_AGGEGATION_DROP_TABLE_SQL)
    cur.execute(USASPENDING_ASSISTANCE_OBLIGATION_AGGEGATION_CREATE_TABLE_SQL)
    cur.execute(
        USASPENDING_ASSISTANCE_OBLIGATION_AGGEGATION_SELECT_AND_INSERT_SQL)
    conn.commit()

    cur.execute(USASPENDING_ASSISTANCE_OUTLAY_AGGEGATION_DROP_TABLE_SQL)
    cur.execute(USASPENDING_ASSISTANCE_OUTLAY_AGGEGATION_CREATE_TABLE_SQL)
    cur.execute(USASPENDING_ASSISTANCE_OUTLAY_AGGEGATION_SELECT_AND_INSERT_SQL)
    conn.commit()


def load_agency():
    """Transforms the SAM.gov agency data and inserts the cleaned data into
    the transformed database."""
    cur.execute(AGENCY_DROP_TABLE_SQL)
    cur.execute(AGENCY_CREATE_TABLE_SQL)
    conn.commit()
    with open(REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY
              + "organizations.json", encoding="utf-8") as f:
        for o in json.load(f):
            name = o.get("agencyName", o["name"])
            if name in constants.AGENCY_DISPLAY_NAMES:
                name = constants.AGENCY_DISPLAY_NAMES[name]
            is_cfo_act = (name in constants.CFO_ACT_AGENCY_NAMES
                          and o["orgKey"] == o["l1OrgKey"])
            cur.execute(AGENCY_INSERT_SQL, [o["orgKey"], name, o["l1OrgKey"],
                        o.get("l2OrgKey", None), is_cfo_act])
        conn.commit()


def load_sam_category():
    """Transforms the SAM.gov assistance type, applicant type, and beneficiary
    type data and inserts the cleaned data into the transformed database."""
    cur.execute(CATEGORY_DROP_TABLE_SQL)
    cur.execute(CATEGORY_CREATE_TABLE_SQL)
    with open(REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY
              + "dictionary.json", encoding="utf-8") as f:
        for i in json.load(f)["_embedded"]["jSONObjectList"]:
            if i["id"] == "assistance_type":
                for e in i["elements"]:
                    e["value"] = constants.ASSISTANCE_TYPE_DISPLAY_NAMES[
                        e["value"]]
                    cur.execute(CATEGORY_INSERT_SQL, [e["element_id"],
                                "assistance", e["value"], None])
                    for s in e["elements"]:
                        cur.execute(CATEGORY_INSERT_SQL, [s["element_id"],
                                    "assistance", s["value"], e["element_id"]])
            if i["id"] == "applicant_types":
                for e in i["elements"]:
                    cur.execute(CATEGORY_INSERT_SQL, [e["element_id"],
                                "applicant", e["value"], None])
            if i["id"] == "beneficiary_types":
                for e in i["elements"]:
                    cur.execute(CATEGORY_INSERT_SQL, [e["element_id"],
                                "beneficiary", e["value"], None])
        conn.commit()


# load assistance listing values from SAM.gov
def load_sam_programs():
    """Transforms the SAM.gov assistance listing data and inserts the cleaned
    data into the transformed database."""
    cur.execute(PROGRAM_DROP_TABLE_SQL)
    cur.execute(PROGRAM_CREATE_TABLE_SQL)
    cur.execute(PROGRAM_AUTHORIZATION_DROP_TABLE_SQL)
    cur.execute(PROGRAM_AUTHORIZATION_CREATE_TABLE_SQL)
    cur.execute(PROGRAM_RESULT_DROP_TABLE_SQL)
    cur.execute(PROGRAM_RESULT_CREATE_TABLE_SQL)
    cur.execute(PROGRAM_SAM_SPENDING_DROP_TABLE_SQL)
    cur.execute(PROGRAM_SAM_SPENDING_CREATE_TABLE_SQL)
    cur.execute(PROGRAM_TO_CATEGORY_DROP_TABLE_SQL)
    cur.execute(PROGRAM_TO_CATEGORY_CREATE_TABLE_SQL)
    with open(REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY
              + "usaspending-program-search-hashes.json",
              encoding="utf-8") as f:
        usaspending_hashes = json.load(f)
    with open(REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY
              + "assistance-listings.json", encoding="utf-8") as f:
        for listing in json.load(f):
            d = listing["data"]
            # if the program has an alternative "popular name"
            popular_name = None
            if len(d.get("alternativeNames", [])) > 0 \
                    and len(d["alternativeNames"][0]) > 0:
                popular_name = d["alternativeNames"][0]
            cur.execute(PROGRAM_INSERT_SQL, [d["programNumber"],
                        d["organizationId"], d["title"], popular_name,
                        d["objective"],
                        "https://sam.gov/fal/" + listing["id"] + "/view",
                        usaspending_hashes.get(d["programNumber"], ""),
                        "https://www.usaspending.gov/search/?hash="
                        + usaspending_hashes.get(d["programNumber"], ""),
                        "https://grants.gov/search-grants?cfda="
                        + d["programNumber"],
                        "assistance_listing",
                        any(item.get("code")=="subpartF" and item.get("isSelected") is True
                            for item in d["compliance"]["CFR200Requirements"]["questions"]),
                        d["compliance"]["documents"].get("description")
                        ])
            # if the program has any results
            if d["financial"]["accomplishments"].get("list", False):
                if len(d["financial"]["accomplishments"]["list"]) > 0:
                    for a in d["financial"]["accomplishments"]["list"]:
                        if a.get("fiscalYear", False):
                            cur.execute(PROGRAM_RESULT_INSERT_SQL,
                                        [d["programNumber"], a["fiscalYear"],
                                         a["description"]])
            # if the program has any authorizations
            if d["authorizations"].get("list", False):
                for auth_dict in d["authorizations"].get("list", False):
                    auths = []
                    url = None
                    if auth_dict["authorizationTypes"]["act"] is not None \
                            and auth_dict.get("act", False):
                        act_title = auth_dict["act"].get("title", "").strip() \
                            if auth_dict["act"].get("title", "") \
                            is not None else ""
                        act_part = auth_dict["act"].get("part", "").strip() \
                            if auth_dict["act"].get("part", "") \
                            is not None else ""
                        act_section = auth_dict["act"].get("section", "") \
                            .strip() if auth_dict["act"].get("section", "") \
                            is not None else ""
                        act_description = auth_dict["act"] \
                            .get("description", "").strip() \
                            if auth_dict["act"].get("description", "") \
                            is not None else ""
                        if len(act_title + act_part + act_section
                               + act_description) > 0:
                            auths.append(", ".join([p for p in [act_title,
                                                                act_part,
                                                                act_section,
                                                                act_description
                                                                ]
                                                    if len(p) > 0]))
                    if auth_dict["authorizationTypes"]["statute"] is not None \
                            and auth_dict.get("statute", False):
                        statute_volume = auth_dict["statute"] \
                            .get("volume", "").strip() \
                            if auth_dict["statute"].get("volume", "") \
                            is not None else ""
                        statute_page = auth_dict["statute"].get("page", "") \
                            .strip() if auth_dict["statute"].get("page", "") \
                            is not None else ""
                        if len(statute_volume + statute_page) > 0:
                            auths.append(" Stat. ".join([p for p in [
                                            statute_volume, statute_page]
                                            if len(p) > 0]))
                            if not url and statute_volume.isnumeric() \
                                    and statute_page.isnumeric():
                                url = "https://www.govinfo.gov/link/statute/" \
                                      + statute_volume + "/" + statute_page
                    if auth_dict["authorizationTypes"]["publicLaw"] \
                            is not None and auth_dict.get("publicLaw", False):
                        pl_congress_code = auth_dict["publicLaw"] \
                            .get("congressCode", "").strip() \
                            if auth_dict["publicLaw"] \
                            .get("congressCode", "") is not None else ""
                        pl_number = auth_dict["publicLaw"] \
                            .get("number",  "").strip() \
                            if auth_dict["publicLaw"].get("number", "") \
                            is not None else ""
                        if len(pl_congress_code + pl_number) > 0:
                            auths.append("Pub. L. " + ", ".join(
                                [p for p in [pl_congress_code, pl_number]
                                 if len(p) > 0]))
                            if not url and pl_congress_code.isnumeric() \
                                    and pl_number.isnumeric():
                                url = "https://www.govinfo.gov/link/plaw/" \
                                      + pl_congress_code + "/public/" \
                                      + pl_number
                    if auth_dict["authorizationTypes"]["USC"] is not None \
                            and auth_dict.get("USC", False):
                        usc_title = auth_dict["USC"].get("title", "").strip() \
                                if auth_dict["USC"].get("title", "") \
                                is not None else ""
                        usc_section = auth_dict["USC"] \
                            .get("section", "").strip() if auth_dict["USC"] \
                            .get("section", "") is not None else ""
                        if len(usc_title + usc_section) > 0:
                            auths.append(usc_title + " U.S.C. &sect; "
                                         + usc_section)
                            if not url:
                                if usc_title.isnumeric() \
                                        and usc_section.isnumeric():
                                    url = "https://www.govinfo.gov/link/" \
                                          + f"uscode/{usc_title}/{usc_section}"
                                elif usc_title.isnumeric() \
                                        and len(usc_section) > 0:
                                    # many agencies provide a sub-section
                                    # or range in their "USC Section"; for
                                    # compatibility with GovInfo link
                                    # service, a single numeric section
                                    # number needs to be extracted
                                    extracted_num = ""
                                    for letter in usc_section:
                                        if not letter .isnumeric():
                                            break
                                        extracted_num += letter
                                    if len(extracted_num) > 0:
                                        url = "https://www.govinfo.gov/link/" \
                                              + "uscode/" + usc_title + "/" \
                                              + extracted_num
                    if auth_dict["authorizationTypes"]["executiveOrder"] \
                            is not None and auth_dict.get("executiveOrder",
                                                          False):
                        eo_title = auth_dict["executiveOrder"] \
                            .get("title", "").strip() \
                            if auth_dict["executiveOrder"].get("title", "") \
                            is not None else ""
                        eo_part = auth_dict["executiveOrder"] \
                            .get("part", "").strip() \
                            if auth_dict["executiveOrder"].get("part", "") \
                            is not None else ""
                        eo_section = auth_dict["executiveOrder"] \
                            .get("section", "").strip() \
                            if auth_dict["executiveOrder"].get("section", "") \
                            is not None else ""
                        eo_description = auth_dict["executiveOrder"] \
                            .get("description", "").strip() \
                            if auth_dict["executiveOrder"] \
                            .get("description", "") is not None else ""
                        if len(eo_title + eo_part + eo_section
                               + eo_description) > 0:
                            auths.append(", ".join([p for p in
                                                    [eo_title, eo_part,
                                                     eo_section,
                                                     eo_description]
                                                    if len(p) > 0]))

                    text = '. '.join(auths) + ('.' if not ''.join(auths)
                                               .endswith('.') else '')
                    cur.execute(PROGRAM_AUTHORIZATION_INSERT_SQL,
                                [d["programNumber"], text, url])
            # if the program has any spending information
            for o in listing["data"]["financial"]["obligations"]:
                for row in o.get("values", []):
                    if row.get("actual"):
                        cur.execute(PROGRAM_SAM_SPENDING_INSERT_SQL,
                                    [d["programNumber"],
                                     o.get("assistanceType", ""), 'assistance', row["year"],
                                     1, row["actual"], row["actual"]])
                    if row.get("estimate"):
                        cur.execute(PROGRAM_SAM_SPENDING_INSERT_SQL,
                                    [d["programNumber"],
                                     o.get("assistanceType", ""), 'assistance', row["year"],
                                     0, row["estimate"], row["estimate"]])
            # if the program has assistance types
            for e in listing["data"]["financial"]["obligations"]:
                if e.get("assistanceType", False):
                    cur.execute(PROGRAM_TO_CATEGORY_INSERT_SQL, [
                        d["programNumber"], e["assistanceType"], "assistance"])
            # if the program has beneficiary types
            for e in listing["data"]["eligibility"]["beneficiary"]["types"]:
                cur.execute(PROGRAM_TO_CATEGORY_INSERT_SQL, [
                    d["programNumber"], e, "beneficiary"])
            # if the program has applicant types
            for e in listing["data"]["eligibility"]["applicant"]["types"]:
                cur.execute(PROGRAM_TO_CATEGORY_INSERT_SQL, [
                    d["programNumber"], e, "applicant"])

    load_acquisitions_and_services()
    conn.commit()


def load_additional_programs():
    if not os.path.exists(ADDITIONAL_PROGRAMS_DATA_PATH):
        print(f"{ADDITIONAL_PROGRAMS_DATA_PATH} - Not Found")
        return

    cur.execute(OTHER_PROGRAM_SPENDING_DROP_TABLE_SQL)
    cur.execute(OTHER_PROGRAM_SPENDING_CREATE_TABLE_SQL)

    df = pd.read_csv(ADDITIONAL_PROGRAMS_DATA_PATH)
    # Strip whitespace from all string columns
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    df = df.rename(columns={
        'type': 'program_to_category.category_type',
        '`': 'program.id',
        'name': 'program.name'
    })

    agency_names = df[df.agency.notnull()]['agency'].unique().tolist() + df[df.subagency.notnull()]['subagency'].unique().tolist()
    agency_names.append('Internal Revenue Service (IRS)') if 'Internal Revenue Service (IRS)' not in agency_names else agency_names

    try:
        cur.execute(f"SELECT * FROM agency WHERE agency_name in {tuple(agency_names)};")
    except Exception as e:
        print(str(e))
        print(f"ERROR - Unable to query for agency_name IDs")
        return

    response = cur.fetchall()
    agency_id_map = {val[1]: val[0] for val in response}

    df.insert(df.shape[1], 'category.type', 'category')
    df.insert(df.shape[1], 'program.agency_id', None)
    df.insert(df.shape[1], 'category.name', None)
    df.insert(df.shape[1], 'category.id', None)
    df.insert(df.shape[1], 'category.parent_id', None)
    df.insert(df.shape[1], 'focus_area.id', None)

    for ind, record in df.iterrows():
        if not pd.isna(record.subagency):
            df.at[ind, 'program.agency_id'] = agency_id_map[record.subagency]
        elif not pd.isna(record.agency):
            df.at[ind, 'program.agency_id'] = agency_id_map[record.agency]
        if not pd.isna(record.subcategory):
            df.at[ind, 'category.id'] = convert_to_url_string(record.category + record.subcategory)
            df.at[ind, 'category.parent_id'] = convert_to_url_string(record.category)
            df.at[ind, 'category.name'] = record.subcategory
        elif not pd.isna(record.category):
            df.at[ind, 'category.id'] = convert_to_url_string(record.category)
            df.at[ind, 'category.parent_id'] = None
            df.at[ind, 'category.name'] = record.category

    df['program.objective'] = df['description'].apply(lambda x: x if not pd.isna(x) else None)

    # Insert categories into the database
    category_lookup = {}
    category_counter = 0
    focus_area_lookup = {}
    focus_area_counter = 0
    for ind, record in df.iterrows():
        if (record.category not in category_lookup):
            category_lookup[record.category] = 'ADDITIONAL_' + str(category_counter)
            cur.execute("""
                INSERT INTO taxonomy_category
                -- dash is later used as a delimiter between category and focus area
                VALUES (?, REPLACE(?,'-','–'));
            """, (category_lookup[record.category], record.category))
            category_counter = category_counter + 1
        if (record.subcategory not in focus_area_lookup):
            focus_area_lookup[record.subcategory] = 'ADDITIONAL_' + str(focus_area_counter)
            cur.execute(TAXONOMY_FOCUS_AREA_INSERT_TABLE_SQL, (focus_area_lookup[record.subcategory], record.subcategory, category_lookup[record.category]))
            focus_area_counter = focus_area_counter + 1
    conn.commit()

    # Insert assistance types
    assistance_entries = [
        {'id': 'interest', 'type': 'assistance', 'name': 'Interest', 'parent_id': None},
        {'id': 'tax_expenditure', 'type': 'assistance', 'name': 'Tax Expenditures', 'parent_id': None},
        {'id': 'acquisition_contract', 'type': 'assistance', 'name': 'Acquisition Contract', 'parent_id': None},
        {'id': 'government_service', 'type': 'assistance', 'name': 'Government Service', 'parent_id': None}
    ]
    for entry in assistance_entries:
        try:
            cur.execute(
                "INSERT INTO category (id, type, name, parent_id) VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING;",
                (entry['id'], entry['type'], entry['name'], entry['parent_id'])
            )
        except Exception as e:
            print(str(e))
            print(f"ERROR - Assistance Category Insert Error")

    # Insert programs and map to categories
    for ind, record in df[df['program.id'].notnull()].iterrows():
        program_query = """
            INSERT INTO program
            (id, agency_id, name, popular_name, objective, sam_url, usaspending_awards_hash, usaspending_awards_url, grants_url, program_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        program_values = (
            record['program.id'],
            record['program.agency_id'],
            record['program.name'],
            None,
            record['program.objective'],
            None,
            None,
            None,
            None,
            record['program_to_category.category_type']
        )
        try:
            cur.execute(program_query, program_values)
        except Exception as e:
            print(str(e))
            print("ERROR - Program Insert Error")

        # Map assistance types
        if not pd.isna(record['assistance_type']):
            assistance_value = record['assistance_type']
            category_id = 'interest' if assistance_value == 'Interest' else 'tax_expenditure' if assistance_value == 'Tax Expenditures' else None

            if category_id:
                try:
                    cur.execute(
                        "INSERT INTO program_to_category (program_id, category_id, category_type) VALUES (?, ?, ?) ON CONFLICT DO NOTHING;",
                        (record['program.id'], category_id, 'assistance')
                    )
                except Exception as e:
                    print(str(e))
                    print("ERROR - Program to Assistance Mapping Error")

        # Map focus area
        df.at[ind, 'focus_area.id'] = focus_area_lookup[record.subcategory]

    # Insert spending data into the other_program_spending table
    fiscal_years = {}
    for col in df.columns:
        if '_outlays' in col:
            year = col.split('_')[0]
            fiscal_years[year] = [f'{year}_outlays', f'{year}_foregone_revenue']

    for ind, record in df[df['program.id'].notnull()].iterrows():
        for year, columns in fiscal_years.items():
            cur.execute(OTHER_PROGRAM_SPENDING_INSERT_SQL, [
                record['program.id'],
                int(year),
                0 if pd.isna(record[columns[0]]) else record[columns[0]],
                0 if pd.isna(record[columns[1]]) else record[columns[1]],
                'additional-programs.csv',
                record['focus_area.id']
            ])

    conn.commit()

def load_improper_payment_mapping():
    """Loads improper payment mapping data from CSV into the database."""
    cur.execute(IMPROPER_PAYMENT_MAPPING_DROP_TABLE_SQL)
    cur.execute(IMPROPER_PAYMENT_MAPPING_CREATE_TABLE_SQL)
    
    file_path = REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY + "improper-payment-program-mapping.csv"
    
    if not os.path.exists(file_path):
        print(f"{file_path} - Not Found")
        return
        
    df = pd.read_csv(file_path)
    
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # Clean monetary columns - remove $ and commas, convert to float
    money_columns = ['outlays', 'improper_payment_amount', 'insufficient_documentation_amount']
    for col in money_columns:
        # Handle potential NaN/empty values
        df[col] = df[col].fillna('0')
        df[col] = df[col].str.replace('$', '').str.replace(',', '').astype(float)
    
    # Convert boolean to integer
    df['high_priority_program'] = df['high_priority_program'].astype(int)
    
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO improper_payment_mapping 
            (program_id, improper_payment_program_name, outlays, 
             improper_payment_amount, insufficient_documentation_amount, 
             high_priority_program)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row['program_id'],
            row['improper_payment_program_name'],
            row['outlays'],
            row['improper_payment_amount'],
            row['insufficient_documentation_amount'],
            row['high_priority_program']
        ))
    
    conn.commit()
    print("Successfully loaded improper payment mapping data")

def load_acquisitions_and_services():
    """Loads programs derived from contracts."""
    file_path = REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY + "acquisitions_and_services.csv"
    df = pd.read_csv(file_path)

    latest_fiscal_year = df["Fiscal Year"].max()
    beneficiary_id_counter = 1
    applicants_id_counter = 1
    for _, row in df.iterrows():
        # Only import program data for latest year
        if row["Fiscal Year"] < latest_fiscal_year:
            continue

        beneficiary_id = None
        if row["Beneficiary"] is not None and row["Beneficiary"] != "":
            cur.execute(CATEGORY_FIND_SQL, ["beneficiary", row["Beneficiary"]])
            response = cur.fetchall()
            if (len(response) == 0):
                beneficiary_id = str(row["Program ID"]) + "_B_" + str(beneficiary_id_counter)
                cur.execute(CATEGORY_INSERT_SQL, [
                    beneficiary_id,
                    "beneficiary",
                    row["Beneficiary"],
                    None
                ])
                beneficiary_id_counter += 1
            else:
                beneficiary_id = response[0][0]

        applicant_id = None
        if row["Eligible applicants"] is not None and row["Eligible applicants"] != "":
            cur.execute(CATEGORY_FIND_SQL, ["applicant", row["Eligible applicants"]])
            response = cur.fetchall()
            if (len(response) == 0):
                applicant_id = str(row["Program ID"]) + "_A_" + str(applicants_id_counter)
                cur.execute(CATEGORY_INSERT_SQL, [
                    applicant_id,
                    "applicant",
                    row["Eligible applicants"],
                    None
                ])
                applicants_id_counter += 1
            else:
                applicant_id = response[0][0]

        cur.execute(PROGRAM_INSERT_SQL, [
            row["Program ID"],
            row["Agency ID"],
            row["Program Name"],
            row["Popular Name"],
            row["Program Objective"],
            None,
            row["USASpending hash"],
            None,
            None,
            str(row["Program Type"]).lower().replace(' ','_'),
            0,
            row["Associated Rules and Regulations"]
        ])

        if beneficiary_id is not None:
            cur.execute(PROGRAM_TO_CATEGORY_INSERT_SQL, [
                row["Program ID"],
                beneficiary_id,
                "beneficiary"
            ])

        if applicant_id is not None:
            cur.execute(PROGRAM_TO_CATEGORY_INSERT_SQL, [
                row["Program ID"],
                applicant_id,
                "applicant"
            ])

        cur.execute(PROGRAM_AUTHORIZATION_INSERT_SQL, [
            row["Program ID"],
            row["Authorizing Statues"],
            None
        ])

        # Add category mapping to utilize existing "Program Type" filter in the UI
        category_id = 'acquisition_contract'
        if row["Program Type"].lower() == 'government service':
            category_id = 'government_service'
        cur.execute(
            "INSERT INTO program_to_category (program_id, category_id, category_type) VALUES (?, ?, ?) ON CONFLICT DO NOTHING;",
            (row["Program ID"], category_id, 'assistance')
        )

        # Taxonomy joins assumed to happen via GWO / PON assignment files

    for _, row in df.iterrows():
        cur.execute(USASPENDING_ASSISTANCE_OUTLAY_AGGREGATION_DIRECT_INSERT_SQL, [
            row["Program ID"],
            row["Fiscal Year"],
            row["Outlay_Sum (USASpending.gov)"],
            row["Obligation_Sum (USASpending.gov)"]
        ])

def load_taxonomy_and_assignments():
    """Loads taxonomy categories, focus areas, gwos, pons, and assignments."""
    cur.execute(PROGRAM_TAXONOMY_LOOKUP_DROP_VIEW_SQL)
    cur.execute(PROGRAM_TO_GWO_DROP_TABLE_SQL)
    cur.execute(PROGRAM_TO_PON_DROP_TABLE_SQL)
    cur.execute(GWO_DROP_TABLE_SQL)
    cur.execute(PON_DROP_TABLE_SQL)
    cur.execute(TAXONOMY_FOCUS_AREA_DROP_TABLE_SQL)
    cur.execute(TAXONOMY_CATEGORY_DROP_TABLE_SQL)

    cur.execute(TAXONOMY_CATEGORY_CREATE_TABLE_SQL)
    cur.execute(TAXONOMY_FOCUS_AREA_CREATE_TABLE_SQL)
    cur.execute(GWO_CREATE_TABLE_SQL)
    cur.execute(PON_CREATE_TABLE_SQL)
    cur.execute(PROGRAM_TO_GWO_CREATE_TABLE_SQL)
    cur.execute(PROGRAM_TO_PON_CREATE_TABLE_SQL)
    cur.execute(PROGRAM_TAXONOMY_LOOKUP_CREATE_VIEW_SQL)

    file_path = REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY + "Taxonomy_GWO_crosswalk.csv"
    df = pd.read_csv(file_path)

    for _, row in df.iterrows():
        cur.execute(TAXONOMY_CATEGORY_INSERT_TABLE_SQL, [
            row['Category Code'],
            row['Category']
        ])

        cur.execute(TAXONOMY_FOCUS_AREA_INSERT_TABLE_SQL, [
            row['FA Code'],
            row['Focus Area'],
            row['Category Code']
        ])

        cur.execute(GWO_INSERT_TABLE_SQL, [
            row['GWO ID'],
            row['GWO'],
            row['GWO Definition'],
            row['FA Code']
        ])

    file_path = REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY + "Taxonomy_PON_crosswalk.csv"
    df = pd.read_csv(file_path)

    for _, row in df.iterrows():
        cur.execute(TAXONOMY_CATEGORY_INSERT_TABLE_SQL, [
            row['Category Code'],
            row['Category']
        ])

        cur.execute(TAXONOMY_FOCUS_AREA_INSERT_TABLE_SQL, [
            row['FA Code'],
            row['Focus Area'],
            row['Category Code']
        ])

        cur.execute(PON_INSERT_TABLE_SQL, [
            row['PON ID'],
            row['PON2'],
            row['PON Definition'],
            row['FA Code']
        ])

    file_path = REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY + "FPI_GWO_assignment.csv"
    df = pd.read_csv(file_path)

    for _, row in df.iterrows():
        cur.execute(PROGRAM_TO_GWO_INSERT_TABLE_SQL, [
            row['al_#'],
            row['GWO ID']
        ])

    file_path = REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY + "FPI_PON_assignment.csv"
    df = pd.read_csv(file_path)

    for _, row in df.iterrows():
        cur.execute(PROGRAM_TO_PON_INSERT_TABLE_SQL, [
            row['al_#'],
            row['PON ID']
        ])

    conn.commit()
    print("Successfully loaded taxonomy and assignments")

# uncomment the necessary functions to database with data
#
# load_usaspending_initial_files()
# load_usaspending_delta_files()
# transform_and_insert_usaspending_aggregation_data()
# load_agency()
# load_sam_category()
# load_sam_programs()
# load_taxonomy_and_assignments()
# load_additional_programs()
# load_improper_payment_mapping()

# close the db connection
conn.close()
