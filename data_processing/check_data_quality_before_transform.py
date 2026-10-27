#!/usr/bin/env python3
"""
Data quality checks for extracted CSV files.

Writes finding files to an output directory (the current directory by default):

- alns_possibly_truncated.csv
- amounts_with_scientific_notation.csv
- files_with_incorrect_headers.csv
- files_with_incorrect_column_count.csv
- invalid_gwos.csv
- invalid_pons.csv
- excessive_pon_assignments.csv
- invalid_alns.csv
- missing_inflation_year.csv
- missing_additional_program_prefixes.csv
- duplicate_ids.csv
- invalid_agencies.csv
- invalid_program_types.csv

Truncation, scientific-notation, file-structure, invalid GWO, PON, agency, or program type, missing inflation-year, duplicate-id, and excessive PON assignment findings are also appended to blockers.txt.
An unexpected error is appended to blockers.txt and does not stop the caller.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import constants

EXTRACTED_DIR = Path(__file__).resolve().parent / "extracted"
GWO_ASSIGNMENT_FILENAME = "FPI_GWO_assignment.csv"
PON_ASSIGNMENT_FILENAME = "FPI_PON_assignment.csv"
GWO_CROSSWALK_FILENAME = "Taxonomy_GWO_crosswalk.csv"
PON_CROSSWALK_FILENAME = "Taxonomy_PON_crosswalk.csv"
ASSISTANCE_LISTINGS_FILENAME = "assistance-listings.json"
ADDITIONAL_PROGRAMS_FILENAME = "additional-programs.csv"
ACQUISITIONS_FILENAME = "acquisitions_and_services.csv"
USASPENDING_HASHES_FILENAME = "usaspending-program-search-hashes.json"
INFLATION_FILENAME = "inflation_and_population_growth.csv"
ORGANIZATIONS_FILENAME = "organizations.json"
IP_DATA_FILENAME = "improper-payment-program-mapping.csv"
TRUNCATED_ALN_FILENAMES = (
    "acquisitions_and_services.csv",
    "additional-programs.csv",
    GWO_ASSIGNMENT_FILENAME,
    PON_ASSIGNMENT_FILENAME,
)
# Headers that store an Assistance Listing Number or other FPI program id.
ALN_COLUMN_NAMES = {"al_#", "Program ID", "program_id", "`"}
OUTPUT_FILENAMES = (
    "alns_possibly_truncated.csv",
    "amounts_with_scientific_notation.csv",
    "files_with_incorrect_headers.csv",
    "files_with_incorrect_column_count.csv",
    "invalid_gwos.csv",
    "invalid_pons.csv",
    "excessive_pon_assignments.csv",
    "invalid_alns.csv",
    "missing_inflation_year.csv",
    "missing_additional_program_prefixes.csv",
    "duplicate_ids.csv",
    "invalid_agencies.csv",
    "invalid_program_types.csv",
    "blockers.txt",
)
VALID_PROGRAM_TYPES = {"Contracts"}
REQUIRED_ADDITIONAL_PROGRAM_PREFIXES = ("IN.", "TC.")
MAX_PON_ASSIGNMENTS = 3
# Columns that form a unique id in each extracted file.
DUPLICATE_ID_COLUMNS = (
    (ADDITIONAL_PROGRAMS_FILENAME, ("`",)),
    (ACQUISITIONS_FILENAME, ("Program ID", "Fiscal Year")),
    (GWO_ASSIGNMENT_FILENAME, ("al_#",)),
    (PON_ASSIGNMENT_FILENAME, ("al_#", "PON ID")),
    (IP_DATA_FILENAME, (
        "program_id",
        "improper_payment_program_name",
        "agency",
        "fiscal_year",
    )),
    (INFLATION_FILENAME, ("Year",)),
    (GWO_CROSSWALK_FILENAME, ("GWO ID",)),
    (PON_CROSSWALK_FILENAME, ("PON ID",)),
)
# Baseline column headers for each extracted CSV, in order.
EXPECTED_CSV_HEADERS = {
    "FPI_GWO_assignment.csv": (
        "al_#",
        "GWO ID",
    ),
    "FPI_PON_assignment.csv": (
        "al_#",
        "PON ID",
    ),
    "Taxonomy_GWO_crosswalk.csv": (
        "Category Code",
        "Category",
        "FA Code",
        "Focus Area",
        "GWO ID",
        "GWO",
        "GWO Definition",
    ),
    "Taxonomy_PON_crosswalk.csv": (
        "PON ID",
        "Category Code",
        "Category",
        "FA Code",
        "Focus Area",
        "PON2",
        "PON Definition",
    ),
    "acquisitions_and_services.csv": (
        "Program Name",
        "Popular Name",
        "Program ID",
        "Agency CGAC",
        "Agency ID",
        "Subagency FPDS Code",
        "Agency Name ",
        "Subagency Name ",
        "Program Description",
        "Fiscal Year",
        "Obligation_Sum",
        "Outlay_Sum",
        "Program Type",
        "Count of Contracts",
        "Authorization",
        "Authorization URL",
        "Top Awardee 1",
        "Top Awardee 1 Obligation Amt",
        "Top Awardee 2",
        "Top Awardee 2 Obligation Amt",
        "Top Awardee 3",
        "Top Awardee 3 Obligation Amt",
    ),
    "additional-programs.csv": (
        "`",
        "name",
        "description",
        "agency",
        "subagency",
        "category",
        "subcategory",
        "type",
        "assistance_type",
        "authorization",
        "authorization_url",
        "2022_outlays",
        "2022_foregone_revenue",
        "2023_outlays",
        "2023_foregone_revenue",
        "2024_outlays",
        "2024_foregone_revenue",
        "2025_outlays",
        "2025_foregone_revenue",
        "2026_outlays",
        "2026_foregone_revenue",
    ),
    "improper-payment-program-mapping.csv": (
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
    ),
    "inflation_and_population_growth.csv": (
        "Year",
        "Inflation Rate Percentage",
        "Population Growth Percentage",
    ),
}


def main(output_directory="."):
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        run_checks(output_dir)
    except Exception as error:
        message = f"BLOCKED:  {type(error).__name__}: {error}"
        print(message)
        append_blocker(output_dir, message)


def run_checks(output_dir):
    invalid_gwos = find_invalid_ids(
        EXTRACTED_DIR / GWO_ASSIGNMENT_FILENAME,
        "GWO ID",
        EXTRACTED_DIR / GWO_CROSSWALK_FILENAME,
        "GWO ID",
    )
    if len(invalid_gwos) > 0:
        write_single_column_csv(output_dir / "invalid_gwos.csv", "GWO ID", invalid_gwos)
        invalid_gwo_message = (
            f"BLOCKED:  {len(invalid_gwos)} GWOs are not in the GWO taxonomy"
        )
        print(invalid_gwo_message)
        append_blocker(output_dir, invalid_gwo_message)

    invalid_pons = find_invalid_ids(
        EXTRACTED_DIR / PON_ASSIGNMENT_FILENAME,
        "PON ID",
        EXTRACTED_DIR / PON_CROSSWALK_FILENAME,
        "PON ID",
    )
    if len(invalid_pons) > 0:
        write_single_column_csv(output_dir / "invalid_pons.csv", "PON ID", invalid_pons)
        invalid_pon_message = (
            f"BLOCKED:  {len(invalid_pons)} PONs are not in the PON taxonomy"
        )
        print(invalid_pon_message)
        append_blocker(output_dir, invalid_pon_message)

    excessive_pon_assignments = find_excessive_pon_assignments(EXTRACTED_DIR)
    if len(excessive_pon_assignments) > 0:
        write_rows(
            output_dir / "excessive_pon_assignments.csv",
            ["aln", "pon"],
            excessive_pon_assignments,
        )
        program_count = len({row[0] for row in excessive_pon_assignments})
        excessive_pon_message = (
            f"BLOCKED:  {program_count} programs have more than "
            f"{MAX_PON_ASSIGNMENTS} PON assignments"
        )
        print(excessive_pon_message)
        append_blocker(output_dir, excessive_pon_message)

    invalid_alns = find_invalid_alns(EXTRACTED_DIR)
    if len(invalid_alns) > 0:
        write_rows(
            output_dir / "invalid_alns.csv",
            ["invalid_aln", "filename"],
            invalid_alns,
        )
        invalid_aln_message = (
            f"{len(invalid_alns)} ALNs are not valid"
        )
        print(invalid_aln_message)

    if missing_last_completed_fiscal_year(EXTRACTED_DIR):
        write_single_column_csv(
            output_dir / "missing_inflation_year.csv",
            "year",
            [constants.LAST_COMPLETED_FISCAL_YEAR],
        )
        missing_year_message = (
            "BLOCKED:  "
            + constants.LAST_COMPLETED_FISCAL_YEAR
            + " is missing from inflation_and_population_growth.csv"
        )
        print(missing_year_message)
        append_blocker(output_dir, missing_year_message)

    missing_prefixes = find_missing_additional_program_prefixes(EXTRACTED_DIR)
    if len(missing_prefixes) > 0:
        write_single_column_csv(
            output_dir / "missing_additional_program_prefixes.csv",
            "prefix",
            missing_prefixes,
        )
        for prefix in missing_prefixes:
            missing_prefix_message = (
                "BLOCKED:  additional-programs.csv has no "
                + prefix
                + " program"
            )
            print(missing_prefix_message)
            append_blocker(output_dir, missing_prefix_message)

    duplicate_ids = find_duplicate_ids(EXTRACTED_DIR)
    if len(duplicate_ids) > 0:
        write_rows(
            output_dir / "duplicate_ids.csv",
            ["id", "row numbers", "file"],
            duplicate_ids,
        )
        duplicate_message = f"BLOCKED:  {len(duplicate_ids)} duplicate ids"
        print(duplicate_message)
        append_blocker(output_dir, duplicate_message)

    invalid_agencies = find_invalid_agency_ids(EXTRACTED_DIR)
    if len(invalid_agencies) > 0:
        write_rows(
            output_dir / "invalid_agencies.csv",
            ["row", "value", "filename"],
            invalid_agencies,
        )
        invalid_agency_message = (
            f"BLOCKED:  {len(invalid_agencies)} agency ids are not valid"
        )
        print(invalid_agency_message)
        append_blocker(output_dir, invalid_agency_message)

    invalid_program_types = find_invalid_program_types(EXTRACTED_DIR)
    if len(invalid_program_types) > 0:
        write_rows(
            output_dir / "invalid_program_types.csv",
            ["row", "value", "filename"],
            invalid_program_types,
        )
        invalid_program_type_message = (
            f"BLOCKED:  {len(invalid_program_types)} program types are not valid"
        )
        print(invalid_program_type_message)
        append_blocker(output_dir, invalid_program_type_message)

    truncated = find_truncated_alns(EXTRACTED_DIR)
    if len(truncated) > 0:
        write_rows(
            output_dir / "alns_possibly_truncated.csv",
            ["aln", "row number", "filename"],
            truncated,
        )
        truncated_message = f"BLOCKED:  {len(truncated)} ALNs may be truncated"
        print(truncated_message)
        append_blocker(output_dir, truncated_message)

    scientific = find_scientific_notation(EXTRACTED_DIR)
    if len(scientific) > 0:
        write_rows(
            output_dir / "amounts_with_scientific_notation.csv",
            ["amount", "row number", "column number", "filename"],
            scientific,
        )
        scientific_message = (
            f"BLOCKED:  {len(scientific)} amounts used scientific notation"
        )
        print(scientific_message)
        append_blocker(output_dir, scientific_message)

    check_csv_file_structure(EXTRACTED_DIR, output_dir)
    report_output_files(output_dir)


def load_assistance_listing_alns(extracted_dir):
    alns = set()
    path = extracted_dir / ASSISTANCE_LISTINGS_FILENAME
    with path.open(encoding="utf-8") as handle:
        for listing in json.load(handle):
            program_number = listing.get("data", {}).get("programNumber")
            if program_number is None:
                continue
            aln = str(program_number).strip()
            if aln:
                alns.add(aln)
    return alns


def find_invalid_program_types(extracted_dir):
    path = extracted_dir / ACQUISITIONS_FILENAME
    header, rows = read_csv(path)
    index = header.index("Program Type")
    findings = []
    for row_number, row in rows:
        value = cell_at(row, index)
        if value not in VALID_PROGRAM_TYPES:
            findings.append([row_number, value, ACQUISITIONS_FILENAME])
    return findings


def find_invalid_agency_ids(extracted_dir):
    valid_agency_ids = load_valid_agency_ids(extracted_dir)
    path = extracted_dir / ACQUISITIONS_FILENAME
    header, rows = read_csv(path)
    index = header.index("Agency ID")
    findings = []
    for row_number, row in rows:
        value = cell_at(row, index)
        if value not in valid_agency_ids:
            findings.append([row_number, value, ACQUISITIONS_FILENAME])
    return findings


def load_valid_agency_ids(extracted_dir):
    with (extracted_dir / ORGANIZATIONS_FILENAME).open(encoding="utf-8") as handle:
        organizations = json.load(handle)
    return {
        str(organization["orgKey"]).strip()
        for organization in organizations
        if str(organization.get("orgKey", "")).strip()
    }


def find_duplicate_ids(extracted_dir):
    findings = []
    for filename, columns in DUPLICATE_ID_COLUMNS:
        path = extracted_dir / filename
        if not path.is_file():
            continue
        header, rows = read_csv(path)
        indexes = [header.index(column) for column in columns]
        row_numbers_by_key = {}
        for row_number, row in rows:
            key = tuple(cell_at(row, index) for index in indexes)
            row_numbers_by_key.setdefault(key, []).append(str(row_number))
        for key, row_numbers in row_numbers_by_key.items():
            if len(row_numbers) > 1:
                findings.append([
                    "-".join(key),
                    ";".join(row_numbers),
                    filename,
                ])
    findings.sort(key=lambda row: (row[2], row[0], row[1]))
    return findings


def find_missing_additional_program_prefixes(extracted_dir):
    program_ids = load_column_values(
        extracted_dir / ADDITIONAL_PROGRAMS_FILENAME,
        "`",
    )
    missing = []
    for prefix in REQUIRED_ADDITIONAL_PROGRAM_PREFIXES:
        if not any(program_id.startswith(prefix) for program_id in program_ids):
            missing.append(prefix)
    return missing


def missing_last_completed_fiscal_year(extracted_dir):
    path = extracted_dir / INFLATION_FILENAME
    if not path.is_file():
        return True
    years = load_column_values(path, "Year")
    return constants.LAST_COMPLETED_FISCAL_YEAR not in years


def find_invalid_alns(extracted_dir):
    valid_alns = load_valid_alns(extracted_dir)
    findings = []
    for filename in (GWO_ASSIGNMENT_FILENAME, PON_ASSIGNMENT_FILENAME):
        for aln in load_column_values(extracted_dir / filename, "al_#"):
            if aln not in valid_alns:
                findings.append([aln, filename])
    with (extracted_dir / USASPENDING_HASHES_FILENAME).open(encoding="utf-8") as handle:
        hashes = json.load(handle)
    for aln in hashes:
        value = str(aln).strip()
        if value and value not in valid_alns:
            findings.append([value, USASPENDING_HASHES_FILENAME])
    findings.sort(key=lambda row: (row[1], row[0]))
    return findings


def load_valid_alns(extracted_dir):
    valid_alns = load_assistance_listing_alns(extracted_dir)
    valid_alns.update(
        load_column_values(extracted_dir / ADDITIONAL_PROGRAMS_FILENAME, "`")
    )
    valid_alns.update(
        load_column_values(extracted_dir / ACQUISITIONS_FILENAME, "Program ID")
    )
    return valid_alns


def find_excessive_pon_assignments(extracted_dir):
    path = extracted_dir / PON_ASSIGNMENT_FILENAME
    header, rows = read_csv(path)
    try:
        aln_index = header.index("al_#")
        pon_index = header.index("PON ID")
    except ValueError:
        raise ValueError(
            f"No al_# or PON ID column found in {path.name}"
        ) from None
    assignments_by_aln = {}
    for _row_number, row in rows:
        aln = cell_at(row, aln_index)
        pon = cell_at(row, pon_index)
        if not aln or not pon:
            continue
        assignments_by_aln.setdefault(aln, []).append(pon)
    findings = []
    for aln in sorted(assignments_by_aln):
        pons = assignments_by_aln[aln]
        if len(pons) > MAX_PON_ASSIGNMENTS:
            findings.extend([aln, pon] for pon in pons)
    return findings


def find_invalid_ids(assignment_path, assignment_column, taxonomy_path, taxonomy_column):
    valid_ids = load_column_values(taxonomy_path, taxonomy_column)
    assigned_ids = load_column_values(assignment_path, assignment_column)
    return sorted(assigned_ids - valid_ids)


def load_column_values(path, column_name):
    header, rows = read_csv(path)
    try:
        index = header.index(column_name)
    except ValueError:
        raise ValueError(f"No {column_name} column found in {path.name}") from None
    values = set()
    for _row_number, row in rows:
        value = cell_at(row, index)
        if value:
            values.add(value)
    return values


def find_truncated_alns(extracted_dir):
    findings = []
    for filename in TRUNCATED_ALN_FILENAMES:
        path = extracted_dir / filename
        for row_number, row, indexes in iter_aln_cells(path):
            for index in indexes:
                value = cell_at(row, index)
                if not value:
                    continue
                suffix = value.rsplit(".", 1)[-1]
                if len(suffix) < 3:
                    findings.append([value, row_number, filename])
    return findings


def find_scientific_notation(extracted_dir):
    findings = []
    for path in sorted(extracted_dir.glob("*.csv")):
        for row_number, row in iter_data_rows(path):
            for column_number, cell in enumerate(row, start=1):
                value = cell.strip()
                if "e" not in value.lower():
                    continue
                if not is_numeric(value):
                    continue
                findings.append([value, row_number, column_number, path.name])
    return findings


def find_incorrect_headers(extracted_dir):
    findings = []
    for path in sorted(extracted_dir.glob("*.csv")):
        header, _rows = read_csv(path)
        expected = EXPECTED_CSV_HEADERS.get(path.name)
        if expected is None or tuple(header) != tuple(expected):
            findings.append([
                format_headers(header),
                format_headers(expected or ()),
                path.name,
            ])
    return findings


def find_incorrect_column_counts(extracted_dir):
    findings = []
    for path in sorted(extracted_dir.glob("*.csv")):
        expected = EXPECTED_CSV_HEADERS.get(path.name)
        if expected is None:
            continue
        expected_count = len(expected)
        _header, rows = read_csv(path)
        for row_number, row in rows:
            actual_count = len(row)
            if actual_count != expected_count:
                findings.append([
                    row_number,
                    actual_count,
                    expected_count,
                    path.name,
                ])
    return findings


def check_csv_file_structure(extracted_dir, output_dir):
    header_mismatches = find_incorrect_headers(extracted_dir)
    if len(header_mismatches) > 0:
        write_rows(
            output_dir / "files_with_incorrect_headers.csv",
            ["actual headers", "expected headers", "filename"],
            header_mismatches,
        )
        header_message = (
            f"BLOCKED:  {len(header_mismatches)} files have wrong headers"
        )
        print(header_message)
        append_blocker(output_dir, header_message)

    column_mismatches = find_incorrect_column_counts(extracted_dir)
    if len(column_mismatches) > 0:
        write_rows(
            output_dir / "files_with_incorrect_column_count.csv",
            ["row", "actual column count", "expected column count", "filename"],
            column_mismatches,
        )
        file_count = len({finding[3] for finding in column_mismatches})
        column_message = (
            f"BLOCKED:  {file_count} files have wrong column count"
        )
        print(column_message)
        append_blocker(output_dir, column_message)


def format_headers(headers):
    return ",".join(headers)


def iter_aln_cells(path):
    header, rows = read_csv(path)
    indexes = [
        index
        for index, name in enumerate(header)
        if name.strip() in ALN_COLUMN_NAMES
    ]
    if not indexes:
        return
    for row_number, row in rows:
        yield row_number, row, indexes


def iter_data_rows(path):
    _header, rows = read_csv(path)
    yield from rows


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return [], []
        rows = [
            (row_number, row)
            for row_number, row in enumerate(reader, start=2)
        ]
    return header, rows


def cell_at(row, index):
    if index >= len(row):
        return ""
    return row[index].strip()


def is_numeric(value):
    try:
        float(value)
    except ValueError:
        return False
    return True


def write_single_column_csv(path, column_name, values):
    write_rows(path, [column_name], [[value] for value in values])


def write_rows(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def append_blocker(output_dir, message):
    with (output_dir / "blockers.txt").open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def report_output_files(output_dir):
    output_paths = [
        output_dir / name
        for name in OUTPUT_FILENAMES
        if (output_dir / name).is_file()
    ]
    if not output_paths:
        print("Data quality checks complete: no issues found")
        return
    print(f"Data quality checks complete: issues saved to {output_dir}")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run data quality tests on extracted CSV files."
    )
    parser.add_argument(
        "output_directory",
        nargs="?",
        default=".",
        help="Directory for output files (default: current directory)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args.output_directory)
