#!/usr/bin/env python3
"""
Data quality checks for the transformed program database.

Writes finding files to an output directory (the current directory by default):

- unmapped_programs.csv

A missing table or write error is printed and does not stop the caller.
"""

import argparse
import csv
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

UNMAPPED_PROGRAMS_FILENAME = "unmapped_programs.csv"
UNMAPPED_PROGRAMS_SQL = """
    SELECT
        p.id AS program_id,
        p.name AS program_name,
        p.program_type AS program_type,
        a.agency_name AS agency_name,
        CASE WHEN g.program_id IS NULL THEN 'yes' ELSE 'no' END AS missing_gwo,
        CASE WHEN n.program_id IS NULL THEN 'yes' ELSE 'no' END AS missing_pon
    FROM program p
    LEFT JOIN agency a ON p.agency_id = a.id
    LEFT JOIN (
        SELECT DISTINCT program_id FROM program_to_gwo
    ) g ON g.program_id = p.id
    LEFT JOIN (
        SELECT DISTINCT program_id FROM program_to_pon
    ) n ON n.program_id = p.id
    WHERE g.program_id IS NULL OR n.program_id IS NULL
    ORDER BY p.program_type, p.id
"""


def main(output_directory=".", connection=None):
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        run_checks(output_dir, connection)
    except Exception as error:
        message = f"BLOCKED:  {type(error).__name__}: {error}"
        print(message)
        append_blocker(output_dir, message)


def append_blocker(output_dir, message):
    with (output_dir / "blockers.txt").open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def run_checks(output_dir, connection=None):
    opened_here = False
    try:
        if connection is None:
            db_path = transformed_database_path()
            if not db_path.is_file():
                print(
                    "Unmapped program report was not written: "
                    f"database not found at {db_path}"
                )
                return
            connection = sqlite3.connect(db_path)
            opened_here = True
        report_unmapped_programs(
            connection,
            output_dir / UNMAPPED_PROGRAMS_FILENAME,
        )
    finally:
        if opened_here:
            connection.close()


def transformed_database_path():
    directory = os.getenv("ETL_TRANSFORM_TRANSFORMED_FILES_DIRECTORY")
    filename = os.getenv("ETL_TRANSFORM_TRANSFORMED_DB_FILE_PATH")
    if directory and filename:
        return Path(directory) / filename
    return Path(__file__).resolve().parent.parent / "website" / "transformed_data.db"


def report_unmapped_programs(connection, output_path):
    """Write programs that have no GWO assignment, no PON assignment, or neither.

    This is a QA report. It does not raise, so a missing table or write error
    does not stop transform or load.
    """
    temp_path = None
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cursor = connection.cursor()
        try:
            cursor.execute(UNMAPPED_PROGRAMS_SQL)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
        finally:
            cursor.close()
        fd, temp_path = tempfile.mkstemp(
            prefix=".unmapped_programs_",
            suffix=".csv",
            dir=output_path.parent,
        )
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as report_file:
            writer = csv.writer(report_file)
            writer.writerow(columns)
            for row in rows:
                writer.writerow(["" if value is None else value for value in row])
        os.replace(temp_path, output_path)
        temp_path = None
        print(
            f"Unmapped program report: {len(rows)} program(s) written to {output_path}"
        )
    except Exception as exc:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        print(f"Unmapped program report was not written: {exc}")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run data quality tests on the transformed database."
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
