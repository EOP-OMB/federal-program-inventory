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
REPO_DISK_DIRECTORY = \
    ""#.//Users/codyreinold/Code/omb/offm/federal-program-inventory/"
EXTRACTED_FILES_DIRECTORY = "extracted/"

# additional programs dataset path
ADDITIONAL_PROGRAMS_DATA_PATH = './extracted/additional-programs.csv'

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
        fiscal_year INTEGER NOT NULL,
        is_actual INTEGER NOT NULL,
        amount REAL NOT NULL,
        PRIMARY KEY (program_id, assistance_type, fiscal_year, is_actual),
        FOREIGN KEY(program_id) REFERENCES program(id)
        FOREIGN KEY(assistance_type) REFERENCES category(id)
    );
    """

PROGRAM_SAM_SPENDING_INSERT_SQL = """
    INSERT INTO program_sam_spending
    VALUES (?, ?, ?, ?, ?)
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
        PRIMARY KEY (program_id, fiscal_year),
        FOREIGN KEY(program_id) REFERENCES program(id)
    );
    """

OTHER_PROGRAM_SPENDING_INSERT_SQL = """
    INSERT INTO other_program_spending
    VALUES (?, ?, ?, ?, ?);
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
                                     o.get("assistanceType", ""), row["year"],
                                     1, row["actual"], row["actual"]])
                    if row.get("estimate"):
                        cur.execute(PROGRAM_SAM_SPENDING_INSERT_SQL,
                                    [d["programNumber"],
                                     o.get("assistanceType", ""), row["year"],
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
    conn.commit()


# load category and sub-category values, including program mapping,
# from CSV exported from SAM.gov PDF
def load_category_and_sub_category():
    category_insert_sql = "INSERT INTO category VALUES (?, ?, ?, ?)"
    program_to_category_insert_sql = """INSERT INTO program_to_category
                                     VALUES (?, ?, ?)"""
    categories = set()
    sub_categories = set()
    programs_to_sub_categories = set()
    with open(REPO_DISK_DIRECTORY + EXTRACTED_FILES_DIRECTORY
              + "program-to-function-sub-function.csv", encoding="utf-8") as f:
        for row in csv.reader(f):
            categories.add(row[1])
            sub_categories.add((row[1], row[2]))
            programs_to_sub_categories.add((row[0], row[1], row[2]))
        for c in categories:
            cur.execute(category_insert_sql, [convert_to_url_string(c),
                        "category", c, None])
        for sc in sub_categories:
            cur.execute(category_insert_sql, [convert_to_url_string(
                        sc[0]+sc[1]), "category", sc[1],
                        convert_to_url_string(sc[0])])
        for p in programs_to_sub_categories:
            cur.execute(program_to_category_insert_sql, [p[0],
                        convert_to_url_string(p[1]+p[2]), "category"])
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
    df = df.rename(columns = {'type':'program_to_category.category_type', 
                             '`': 'program.id', 
                             'name': 'program.name'})

    agency_names = df[df.agency.notnull()]['agency'].unique().tolist() + df[df.subagency.notnull()]['subagency'].unique().tolist()
    agency_names.append('Internal Revenue Service (IRS)') if 'Internal Revenue Service (IRS)' not in agency_names else agency_names
    
    try:
        cur.execute(f"SELECT * FROM agency WHERE agency_name in {tuple(agency_names)};")
    except Exception as e:
        print(str(e))
        print(f"ERROR - Unable to query for agency_name ID's")
        return
        
    response = cur.fetchall()
    agency_id_map = {val[1]: val[0] for val in response}

    df.insert(df.shape[1], 'category.type', 'category')
    df.insert(df.shape[1], 'program.agency_id', None)
    df.insert(df.shape[1], 'category.name', None)
    df.insert(df.shape[1], 'category.id', None)
    df.insert(df.shape[1], 'category.parent_id', None)
    
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
    
    unique_categories = []
    
    for ind, record in df.iterrows():
        if not pd.isna(record.category):
            parent_category_entry = {
                'id': convert_to_url_string(record.category),
                'type': 'category',
                'name': record.category,
                'parent_id': None
            }
            if not any(c['id'] == parent_category_entry['id'] for c in unique_categories):
                unique_categories.append(parent_category_entry)
    
    for ind, record in df.iterrows():
        if not pd.isna(record.category) and not pd.isna(record.subcategory):
            subcategory_entry = {
                'id': convert_to_url_string(record.category + record.subcategory),
                'type': 'category',
                'name': record.subcategory,
                'parent_id': convert_to_url_string(record.category)
            }
            if not any(c['id'] == subcategory_entry['id'] for c in unique_categories):
                unique_categories.append(subcategory_entry)

    for category in unique_categories:
        category_query = f"INSERT INTO category (id, type, name, parent_id) VALUES (?, ?, ?, ?);"
        category_values = tuple([category['id'], category['type'], 
                               category['name'], category['parent_id']])
        try:
            cur.execute(category_query, category_values)
        except Exception as e:
            print(str(e))
            print(f"ERROR - Category Insert Error\n{category_query}")
    
    for ind, record in df[df['program.id'].notnull()].iterrows():
        program_query = f"""INSERT INTO program 
        (id, agency_id, name, popular_name, objective, sam_url, usaspending_awards_hash, usaspending_awards_url, grants_url, program_type) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        program_values = tuple([record['program.id'], int(record['program.agency_id']), 
                              record['program.name'], None, record['program.objective'], 
                              None, None, None, None, record['program_to_category.category_type']])
        try:
            cur.execute(program_query, program_values)
        except Exception as e:
            print(str(e))
            print(f"ERROR - {ind}\n{program_query} ")
        
        program_to_category_query = f"""INSERT INTO program_to_category (program_id, category_id, category_type) VALUES (?, ?, ?);"""
        program_to_category_values = tuple([record['program.id'], record['category.id'], 'category'])
        try:
            cur.execute(program_to_category_query, program_to_category_values)
        except Exception as e:
            print(str(e))
            print(f"ERROR - {ind}\n{program_to_category_query} ")

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
                0 if pd.isna(record[columns[0]]) or record[columns[0]] == 0 else record[columns[0]],
                0 if pd.isna(record[columns[1]]) or record[columns[1]] == 0 else record[columns[1]],
                'additional-programs.csv'
            ])

    conn.commit()
      
# uncomment the necessary functions to database with data
#
# load_usaspending_initial_files()
# load_usaspending_delta_files()
# transform_and_insert_usaspending_aggregation_data()
# load_agency()
load_sam_category()
load_sam_programs()
load_category_and_sub_category()
load_additional_programs()

# close the db connection
conn.close()
