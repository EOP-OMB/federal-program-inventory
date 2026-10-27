"""Tests for data quality checks before and after transform."""
import csv
import json
import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from data_processing import check_data_quality_after_transform
from data_processing import check_data_quality_before_transform
from data_processing import constants


@pytest.fixture(autouse=True)
def patch_paths():
    """Override conftest autouse stub of exists/makedirs so real I/O works."""
    yield


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


VALID_AGENCY_ID = "100000000"
VALID_PROGRAM_TYPE = "Contracts"


def full_acquisitions_row(
    program_name,
    program_id,
    obligation_sum,
    fiscal_year="",
    agency_id=VALID_AGENCY_ID,
    program_type=VALID_PROGRAM_TYPE,
):
    header = check_data_quality_before_transform.EXPECTED_CSV_HEADERS["acquisitions_and_services.csv"]
    row = [""] * len(header)
    row[0] = program_name
    row[2] = program_id
    row[header.index("Agency ID")] = agency_id
    row[header.index("Fiscal Year")] = fiscal_year
    row[header.index("Obligation_Sum")] = obligation_sum
    row[header.index("Program Type")] = program_type
    return row


def taxonomy_row(filename, column_name, value):
    header = check_data_quality_before_transform.EXPECTED_CSV_HEADERS[filename]
    row = [""] * len(header)
    row[header.index(column_name)] = value
    return row


def full_additional_row(aln, name, outlays):
    header = check_data_quality_before_transform.EXPECTED_CSV_HEADERS["additional-programs.csv"]
    row = [""] * len(header)
    row[0] = aln
    row[1] = name
    row[header.index("2022_outlays")] = outlays
    return row


def populate_extracted(
    extracted_dir,
    acquisitions_rows,
    additional_rows,
    gwo_rows,
    pon_rows,
    taxonomy_gwo_ids=None,
    taxonomy_pon_ids=None,
    inflation_years=None,
):
    extracted_dir.mkdir(parents=True)
    write_csv(
        extracted_dir / "acquisitions_and_services.csv",
        check_data_quality_before_transform.EXPECTED_CSV_HEADERS["acquisitions_and_services.csv"],
        [full_acquisitions_row(*row) for row in acquisitions_rows],
    )
    write_csv(
        extracted_dir / "additional-programs.csv",
        check_data_quality_before_transform.EXPECTED_CSV_HEADERS["additional-programs.csv"],
        [full_additional_row(*row) for row in additional_rows],
    )
    write_csv(
        extracted_dir / "FPI_GWO_assignment.csv",
        check_data_quality_before_transform.EXPECTED_CSV_HEADERS["FPI_GWO_assignment.csv"],
        gwo_rows,
    )
    write_csv(
        extracted_dir / "FPI_PON_assignment.csv",
        check_data_quality_before_transform.EXPECTED_CSV_HEADERS["FPI_PON_assignment.csv"],
        pon_rows,
    )
    write_csv(
        extracted_dir / "Taxonomy_GWO_crosswalk.csv",
        check_data_quality_before_transform.EXPECTED_CSV_HEADERS["Taxonomy_GWO_crosswalk.csv"],
        [
            taxonomy_row("Taxonomy_GWO_crosswalk.csv", "GWO ID", gwo_id)
            for gwo_id in (
                sorted({row[1] for row in gwo_rows if row[1]})
                if taxonomy_gwo_ids is None
                else taxonomy_gwo_ids
            )
        ],
    )
    write_csv(
        extracted_dir / "Taxonomy_PON_crosswalk.csv",
        check_data_quality_before_transform.EXPECTED_CSV_HEADERS["Taxonomy_PON_crosswalk.csv"],
        [
            taxonomy_row("Taxonomy_PON_crosswalk.csv", "PON ID", pon_id)
            for pon_id in (
                sorted({row[1] for row in pon_rows if row[1]})
                if taxonomy_pon_ids is None
                else taxonomy_pon_ids
            )
        ],
    )
    program_ids = [row[1] for row in acquisitions_rows if row[1]]
    program_ids.extend(row[0] for row in additional_rows if row[0])
    if inflation_years is None:
        inflation_years = [constants.LAST_COMPLETED_FISCAL_YEAR]
    write_csv(
        extracted_dir / "inflation_and_population_growth.csv",
        check_data_quality_before_transform.EXPECTED_CSV_HEADERS["inflation_and_population_growth.csv"],
        [[year, "0.02", "0.02"] for year in inflation_years],
    )
    (extracted_dir / "assistance-listings.json").write_text("[]", encoding="utf-8")
    (extracted_dir / "organizations.json").write_text(
        json.dumps([{"orgKey": VALID_AGENCY_ID}]),
        encoding="utf-8",
    )
    (extracted_dir / "usaspending-program-search-hashes.json").write_text(
        json.dumps({program_id: "hash" for program_id in program_ids}),
        encoding="utf-8",
    )


def passing_rows():
    return {
        "acquisitions_rows": [["Example Program", "10.001", "100.00"]],
        "additional_rows": [
            ["IN.001", "Interest", "100.00"],
            ["TC.001", "Tax expenditure", "100.00"],
        ],
        "gwo_rows": [
            ["10.001", "GWO.A1"],
            ["IN.001", "GWO.A1"],
            ["TC.001", "GWO.A1"],
        ],
        "pon_rows": [
            ["10.001", "PON.205"],
            ["IN.001", "PON.205"],
            ["TC.001", "PON.205"],
        ],
    }


def run_checks(tmp_path, rows, **taxonomy_ids):
    extracted_dir = tmp_path / "extracted"
    output_dir = tmp_path / "output"
    populate_extracted(extracted_dir, **rows, **taxonomy_ids)
    with patch.object(check_data_quality_before_transform, "EXTRACTED_DIR", extracted_dir):
        check_data_quality_before_transform.main(output_dir)
    return output_dir


def assert_only_these_csvs(output_dir, expected_names):
    for name in (
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
    ):
        exists = (output_dir / name).is_file()
        assert exists is (name in expected_names)


class TestInvalidGwos:
    def test_does_not_create_csv_or_blocker_when_gwos_are_valid(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows())

        assert not (output_dir / "invalid_gwos.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_and_blocker_when_gwos_are_invalid(self, tmp_path):
        rows = passing_rows()
        rows["acquisitions_rows"].append(["Other Program", "10.002", "50.00"])
        rows["pon_rows"].append(["10.002", "PON.205"])
        rows["gwo_rows"].append(["10.002", "GWO.ZZZ"])

        output_dir = run_checks(tmp_path, rows, taxonomy_gwo_ids=["GWO.A1"])

        assert read_csv(output_dir / "invalid_gwos.csv") == [
            ["GWO ID"],
            ["GWO.ZZZ"],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  1 GWOs are not in the GWO taxonomy\n"
        )
        assert_only_these_csvs(output_dir, {"invalid_gwos.csv"})


class TestInvalidPons:
    def test_does_not_create_csv_or_blocker_when_pons_are_valid(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows())

        assert not (output_dir / "invalid_pons.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_and_blocker_when_pons_are_invalid(self, tmp_path):
        rows = passing_rows()
        rows["pon_rows"].append(["10.001", "PON.ZZZ"])

        output_dir = run_checks(tmp_path, rows, taxonomy_pon_ids=["PON.205"])

        assert read_csv(output_dir / "invalid_pons.csv") == [
            ["PON ID"],
            ["PON.ZZZ"],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  1 PONs are not in the PON taxonomy\n"
        )
        assert_only_these_csvs(output_dir, {"invalid_pons.csv"})


class TestExcessivePonAssignments:
    def test_does_not_create_csv_or_blocker_when_assignments_are_within_limit(
        self, tmp_path
    ):
        rows = passing_rows()
        rows["acquisitions_rows"].append(["Second Program", "10.002", "50.00"])
        rows["gwo_rows"].append(["10.002", "GWO.A1"])
        rows["pon_rows"].extend([
            ["10.001", "PON.206"],
            ["10.001", "PON.207"],
            ["10.002", "PON.205"],
            ["10.002", "PON.206"],
            ["10.002", "PON.207"],
            ["10.002", ""],
        ])

        output_dir = run_checks(tmp_path, rows)

        assert not (output_dir / "excessive_pon_assignments.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_and_blocker_when_a_program_has_more_than_three(
        self, tmp_path
    ):
        rows = passing_rows()
        rows["acquisitions_rows"].extend([
            ["Second Program", "10.002", "50.00"],
            ["Third Program", "10.003", "25.00"],
            ["Fourth Program", "10.004", "10.00"],
        ])
        rows["gwo_rows"].extend([
            ["10.002", "GWO.A1"],
            ["10.003", "GWO.A1"],
            ["10.004", "GWO.A1"],
        ])
        rows["pon_rows"].extend([
            ["10.002", "PON.205"],
            ["10.002", "PON.206"],
            ["10.002", "PON.207"],
            ["10.003", "PON.301"],
            ["10.003", "PON.302"],
            ["10.003", "PON.303"],
            ["10.003", "PON.304"],
            ["10.004", "PON.401"],
            ["10.004", "PON.402"],
            ["10.004", "PON.403"],
            ["10.004", "PON.404"],
            ["10.004", "PON.405"],
        ])

        output_dir = run_checks(tmp_path, rows)

        assert read_csv(output_dir / "excessive_pon_assignments.csv") == [
            ["aln", "pon"],
            ["10.003", "PON.301"],
            ["10.003", "PON.302"],
            ["10.003", "PON.303"],
            ["10.003", "PON.304"],
            ["10.004", "PON.401"],
            ["10.004", "PON.402"],
            ["10.004", "PON.403"],
            ["10.004", "PON.404"],
            ["10.004", "PON.405"],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  2 programs have more than 3 PON assignments\n"
        )
        assert_only_these_csvs(output_dir, {"excessive_pon_assignments.csv"})


class TestInvalidAlns:
    def test_does_not_create_csv_or_blocker_when_alns_are_valid(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows())

        assert not (output_dir / "invalid_alns.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_and_blocker_when_alns_are_invalid(self, tmp_path):
        rows = passing_rows()
        rows["gwo_rows"].append(["99.999", "GWO.A1"])

        output_dir = run_checks(tmp_path, rows)

        assert read_csv(output_dir / "invalid_alns.csv") == [
            ["invalid_aln", "filename"],
            ["99.999", "FPI_GWO_assignment.csv"],
        ]
        assert_only_these_csvs(output_dir, {"invalid_alns.csv"})
        assert not (output_dir / "blockers.txt").exists()


class TestInvalidAgencies:
    def test_does_not_create_csv_or_blocker_when_agencies_are_valid(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows())

        assert not (output_dir / "invalid_agencies.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_and_blocker_when_agency_is_invalid(self, tmp_path):
        rows = passing_rows()
        rows["acquisitions_rows"] = [
            ["Example Program", "10.001", "100.00", "", "999999999"],
        ]

        output_dir = run_checks(tmp_path, rows)

        assert read_csv(output_dir / "invalid_agencies.csv") == [
            ["row", "value", "filename"],
            ["2", "999999999", "acquisitions_and_services.csv"],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  1 agency ids are not valid\n"
        )
        assert_only_these_csvs(output_dir, {"invalid_agencies.csv"})


class TestInvalidProgramTypes:
    def test_does_not_create_csv_or_blocker_when_program_types_are_valid(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows())

        assert not (output_dir / "invalid_program_types.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_and_blocker_when_program_type_is_invalid(self, tmp_path):
        rows = passing_rows()
        rows["acquisitions_rows"] = [
            ["Example Program", "10.001", "100.00", "", VALID_AGENCY_ID, "Grants"],
        ]

        output_dir = run_checks(tmp_path, rows)

        assert read_csv(output_dir / "invalid_program_types.csv") == [
            ["row", "value", "filename"],
            ["2", "Grants", "acquisitions_and_services.csv"],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  1 program types are not valid\n"
        )
        assert_only_these_csvs(output_dir, {"invalid_program_types.csv"})


class TestDuplicateIds:
    def test_does_not_create_csv_or_blocker_when_ids_are_unique(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows())

        assert not (output_dir / "duplicate_ids.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_and_blocker_when_id_is_duplicated(self, tmp_path):
        rows = passing_rows()
        rows["acquisitions_rows"] = [
            ["Example Program", "10.001", "100.00", "2025"],
            ["Example Program", "10.001", "50.00", "2025"],
        ]

        output_dir = run_checks(tmp_path, rows)

        assert read_csv(output_dir / "duplicate_ids.csv") == [
            ["id", "row numbers", "file"],
            ["10.001-2025", "2;3", "acquisitions_and_services.csv"],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  1 duplicate ids\n"
        )
        assert_only_these_csvs(output_dir, {"duplicate_ids.csv"})

    def test_hyphenated_fields_do_not_collide(self, tmp_path):
        extracted_dir = tmp_path / "extracted"
        extracted_dir.mkdir()
        write_csv(
            extracted_dir / "acquisitions_and_services.csv",
            ["Program ID", "Fiscal Year"],
            [
                ["10.001", "202-5"],
                ["10.001-202", "5"],
                ["10.002", "2025"],
                ["10.002", "2025"],
            ],
        )

        assert check_data_quality_before_transform.find_duplicate_ids(extracted_dir) == [
            ["10.002-2025", "4;5", "acquisitions_and_services.csv"],
        ]


class TestMissingInflationYear:
    def test_does_not_create_csv_or_blocker_when_year_is_present(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows())

        assert not (output_dir / "missing_inflation_year.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_and_blocker_when_year_is_missing(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows(), inflation_years=["2019"])

        assert read_csv(output_dir / "missing_inflation_year.csv") == [
            ["year"],
            [constants.LAST_COMPLETED_FISCAL_YEAR],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  "
            + constants.LAST_COMPLETED_FISCAL_YEAR
            + " is missing from inflation_and_population_growth.csv\n"
        )
        assert_only_these_csvs(output_dir, {"missing_inflation_year.csv"})


class TestAdditionalProgramPrefixes:
    def test_does_not_create_csv_or_blocker_when_prefixes_exist(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows())

        assert not (output_dir / "missing_additional_program_prefixes.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_and_blocker_when_interest_program_is_missing(self, tmp_path):
        rows = passing_rows()
        rows["additional_rows"] = [["TC.001", "Tax expenditure", "100.00"]]
        rows["gwo_rows"] = [["10.001", "GWO.A1"], ["TC.001", "GWO.A1"]]
        rows["pon_rows"] = [["10.001", "PON.205"], ["TC.001", "PON.205"]]

        output_dir = run_checks(tmp_path, rows)

        assert read_csv(output_dir / "missing_additional_program_prefixes.csv") == [
            ["prefix"],
            ["IN."],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  additional-programs.csv has no IN. program\n"
        )
        assert_only_these_csvs(
            output_dir,
            {"missing_additional_program_prefixes.csv"},
        )

    def test_creates_csv_and_blocker_when_tax_program_is_missing(self, tmp_path):
        rows = passing_rows()
        rows["additional_rows"] = [["IN.001", "Interest", "100.00"]]
        rows["gwo_rows"] = [["10.001", "GWO.A1"], ["IN.001", "GWO.A1"]]
        rows["pon_rows"] = [["10.001", "PON.205"], ["IN.001", "PON.205"]]

        output_dir = run_checks(tmp_path, rows)

        assert read_csv(output_dir / "missing_additional_program_prefixes.csv") == [
            ["prefix"],
            ["TC."],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  additional-programs.csv has no TC. program\n"
        )
        assert_only_these_csvs(
            output_dir,
            {"missing_additional_program_prefixes.csv"},
        )


class TestTruncatedAlns:
    def test_does_not_create_csv_when_check_passes(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows())

        assert not (output_dir / "alns_possibly_truncated.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_when_records_fail(self, tmp_path):
        rows = passing_rows()
        rows["acquisitions_rows"] = [["Example Program", "10.01", "100.00"]]
        rows["gwo_rows"] = [
            ["10.01", "GWO.A1"],
            ["IN.001", "GWO.A1"],
            ["TC.001", "GWO.A1"],
        ]
        rows["pon_rows"] = [
            ["10.01", "PON.205"],
            ["IN.001", "PON.205"],
            ["TC.001", "PON.205"],
        ]

        output_dir = run_checks(tmp_path, rows)

        assert read_csv(output_dir / "alns_possibly_truncated.csv") == [
            ["aln", "row number", "filename"],
            ["10.01", "2", "acquisitions_and_services.csv"],
            ["10.01", "2", "FPI_GWO_assignment.csv"],
            ["10.01", "2", "FPI_PON_assignment.csv"],
        ]
        assert_only_these_csvs(output_dir, {"alns_possibly_truncated.csv"})

    def test_writes_blockers_when_records_fail(self, tmp_path):
        rows = passing_rows()
        rows["acquisitions_rows"] = [["Example Program", "10.01", "100.00"]]
        rows["gwo_rows"] = [
            ["10.01", "GWO.A1"],
            ["IN.001", "GWO.A1"],
            ["TC.001", "GWO.A1"],
        ]
        rows["pon_rows"] = [
            ["10.01", "PON.205"],
            ["IN.001", "PON.205"],
            ["TC.001", "PON.205"],
        ]

        output_dir = run_checks(tmp_path, rows)

        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  3 ALNs may be truncated\n"
        )


class TestScientificNotation:
    def test_does_not_create_csv_when_check_passes(self, tmp_path):
        output_dir = run_checks(tmp_path, passing_rows())

        assert not (output_dir / "amounts_with_scientific_notation.csv").exists()
        assert not (output_dir / "blockers.txt").exists()

    def test_creates_csv_when_records_fail(self, tmp_path):
        rows = passing_rows()
        rows["acquisitions_rows"] = [["Example Program", "10.001", "1.5e+10"]]

        output_dir = run_checks(tmp_path, rows)

        assert read_csv(output_dir / "amounts_with_scientific_notation.csv") == [
            ["amount", "row number", "column number", "filename"],
            ["1.5e+10", "2", "11", "acquisitions_and_services.csv"],
        ]
        assert_only_these_csvs(output_dir, {"amounts_with_scientific_notation.csv"})

    def test_writes_blockers_when_records_fail(self, tmp_path):
        rows = passing_rows()
        rows["acquisitions_rows"] = [["Example Program", "10.001", "1.5e+10"]]

        output_dir = run_checks(tmp_path, rows)

        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  1 amounts used scientific notation\n"
        )


class TestCsvFileStructure:
    def test_headers_are_correct_across_all_files(self, tmp_path):
        extracted_dir = check_data_quality_before_transform.EXTRACTED_DIR
        names = {path.name for path in extracted_dir.glob("*.csv")}
        assert names == set(check_data_quality_before_transform.EXPECTED_CSV_HEADERS)
        assert check_data_quality_before_transform.find_incorrect_headers(extracted_dir) == []

        check_data_quality_before_transform.check_csv_file_structure(extracted_dir, tmp_path)

        assert not (tmp_path / "files_with_incorrect_headers.csv").exists()
        assert not (tmp_path / "blockers.txt").exists()

    def test_headers_count_is_incorrect_in_a_file(self, tmp_path):
        extracted_dir = tmp_path / "extracted"
        output_dir = tmp_path / "output"
        extracted_dir.mkdir()
        output_dir.mkdir()
        actual_headers = ["Year", "Inflation Rate Percentage"]
        expected_headers = check_data_quality_before_transform.EXPECTED_CSV_HEADERS[
            "inflation_and_population_growth.csv"
        ]
        write_csv(
            extracted_dir / "inflation_and_population_growth.csv",
            actual_headers,
            [["2019", "0.02", "0.02"]],
        )

        check_data_quality_before_transform.check_csv_file_structure(extracted_dir, output_dir)

        assert read_csv(output_dir / "files_with_incorrect_headers.csv") == [
            ["actual headers", "expected headers", "filename"],
            [
                ",".join(actual_headers),
                ",".join(expected_headers),
                "inflation_and_population_growth.csv",
            ],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  1 files have wrong headers\n"
        )
        assert not (output_dir / "files_with_incorrect_column_count.csv").exists()

    def test_column_count_is_correct_across_all_files(self, tmp_path):
        extracted_dir = check_data_quality_before_transform.EXTRACTED_DIR
        assert check_data_quality_before_transform.find_incorrect_column_counts(extracted_dir) == []

        check_data_quality_before_transform.check_csv_file_structure(extracted_dir, tmp_path)

        assert not (tmp_path / "files_with_incorrect_column_count.csv").exists()
        assert not (tmp_path / "blockers.txt").exists()

    def test_column_count_is_incorrect_in_one_file(self, tmp_path):
        extracted_dir = tmp_path / "extracted"
        output_dir = tmp_path / "output"
        extracted_dir.mkdir()
        output_dir.mkdir()
        write_csv(
            extracted_dir / "inflation_and_population_growth.csv",
            check_data_quality_before_transform.EXPECTED_CSV_HEADERS[
                "inflation_and_population_growth.csv"
            ],
            [["2019", "0.02"]],
        )

        check_data_quality_before_transform.check_csv_file_structure(extracted_dir, output_dir)

        assert read_csv(output_dir / "files_with_incorrect_column_count.csv") == [
            ["row", "actual column count", "expected column count", "filename"],
            ["2", "2", "3", "inflation_and_population_growth.csv"],
        ]
        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  1 files have wrong column count\n"
        )
        assert not (output_dir / "files_with_incorrect_headers.csv").exists()


class TestUncaughtExceptions:
    def test_records_blocker_and_returns(self, tmp_path):
        output_dir = tmp_path / "output"
        with patch.object(
            check_data_quality_before_transform,
            "find_invalid_ids",
            side_effect=ValueError(
                "No Program Type column found in acquisitions_and_services.csv"
            ),
        ):
            check_data_quality_before_transform.main(output_dir)

        assert (output_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  ValueError: No Program Type column found "
            "in acquisitions_and_services.csv\n"
        )


class TestUnmappedProgramReport:

    def _database(self):
        connection = sqlite3.connect(":memory:")
        connection.executescript("""
            CREATE TABLE agency (
                id INTEGER PRIMARY KEY,
                agency_name TEXT
            );
            CREATE TABLE program (
                id TEXT PRIMARY KEY,
                agency_id INTEGER,
                name TEXT,
                program_type TEXT
            );
            CREATE TABLE program_to_gwo (
                program_id TEXT,
                gwo_id TEXT
            );
            CREATE TABLE program_to_pon (
                program_id TEXT,
                pon_id TEXT
            );
            INSERT INTO agency VALUES (1, 'Department of Defense');
            INSERT INTO program VALUES
                ('G3.C.12.100', 1, 'Mapped Contract', 'contracts'),
                ('G3.C.12.138', 1, 'Missing Both', 'contracts'),
                ('10.001', 1, 'Missing PON', 'assistance_listing'),
                ('IN.001', NULL, 'Missing GWO', 'interest');
            INSERT INTO program_to_gwo VALUES
                ('G3.C.12.100', 'GWO.ND3'),
                ('10.001', 'GWO.A1');
            INSERT INTO program_to_pon VALUES
                ('G3.C.12.100', 'PON.7ND'),
                ('G3.C.12.100', 'PON.N50'),
                ('IN.001', 'PON.1');
        """)
        return connection

    def test_writes_programs_missing_gwo_or_pon(self, tmp_path):
        connection = self._database()
        output_dir = tmp_path / "qa"

        check_data_quality_after_transform.main(output_dir, connection)

        output_path = output_dir / "unmapped_programs.csv"
        with output_path.open(newline="", encoding="utf-8") as report_file:
            rows = list(csv.DictReader(report_file))

        assert [row["program_id"] for row in rows] == [
            "10.001",
            "G3.C.12.138",
            "IN.001",
        ]
        by_id = {row["program_id"]: row for row in rows}
        assert by_id["G3.C.12.138"]["missing_gwo"] == "yes"
        assert by_id["G3.C.12.138"]["missing_pon"] == "yes"
        assert by_id["G3.C.12.138"]["agency_name"] == "Department of Defense"
        assert by_id["10.001"]["missing_gwo"] == "no"
        assert by_id["10.001"]["missing_pon"] == "yes"
        assert by_id["IN.001"]["missing_gwo"] == "yes"
        assert by_id["IN.001"]["missing_pon"] == "no"
        assert by_id["IN.001"]["agency_name"] == ""
        connection.close()

    def test_does_not_raise_when_the_report_cannot_be_written(self, tmp_path):
        connection = MagicMock()
        connection.cursor.return_value.execute.side_effect = sqlite3.OperationalError(
            "no such table: program"
        )

        check_data_quality_after_transform.main(tmp_path, connection)
