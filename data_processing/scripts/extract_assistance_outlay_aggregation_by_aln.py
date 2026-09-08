#!/usr/bin/env python3
"""
Extract rows from the temporary SQLite database table:
  usaspending_assistance_outlay_aggregation

Filtered by Assistance Listing Number (ALN), which is stored as cfda_number.

Writes a CSV into data_processing/scripts by default.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sqlite3
import sys
from typing import List, Optional, Sequence


def safe_filename_component(value: str) -> str:
    v = (value or "").strip()
    v = re.sub(r"[^A-Za-z0-9._-]+", "_", v)
    v = v.strip("._-")
    return v or "value"


def default_db_path() -> str:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    preferred = os.path.join(repo_root, "data_processing", "temp_data.db")
    if os.path.exists(preferred):
        return preferred
    fallback = os.path.join(repo_root, "data_processing", "transformed", "temp_data.db")
    return fallback


def default_output_path(aln: str) -> str:
    scripts_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(
        scripts_dir,
        f"usaspending_assistance_outlay_aggregation_{safe_filename_component(aln)}.csv",
    )


def _connect_readonly(db_path: str) -> sqlite3.Connection:
    abs_path = os.path.abspath(db_path)
    # Use read-only if possible, but fall back to normal connect for older SQLite builds.
    try:
        return sqlite3.connect(f"file:{abs_path}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        return sqlite3.connect(abs_path)


def extract_rows(db_path: str, aln: str) -> List[sqlite3.Row]:
    conn = _connect_readonly(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM usaspending_assistance
            WHERE cfda_number = ?;
            """,
            (aln,),
        )
        return cur.fetchall()
    finally:
        conn.close()


def write_csv(path: str, rows: Sequence[sqlite3.Row]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fieldnames = ["assistance_transaction_unique_key", "assistance_award_unique_key", "federal_action_obligation", "total_outlayed_amount_for_overall_award", "action_date_fiscal_year", "prime_award_transaction_place_of_performance_cd_current", "cfda_number", "assistance_type_code"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fieldnames})


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract assistance outlay aggregation rows from data_processing/temp_data.db "
            "(SQLite) for a given Assistance Listing Number (ALN / CFDA)."
        )
    )
    parser.add_argument(
        "--aln",
        required=True,
        help='Assistance Listing Number / CFDA number (e.g. "10.205")',
    )
    parser.add_argument(
        "--db",
        default=default_db_path(),
        help=(
            "Path to temp_data.db (defaults to data_processing/temp_data.db, "
            "or data_processing/transformed/temp_data.db if not present)"
        ),
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output CSV path (defaults to data_processing/scripts/...)",
    )
    args = parser.parse_args(argv)

    out_path = args.out or default_output_path(args.aln)
    try:
        rows = extract_rows(args.db, args.aln)
    except sqlite3.Error as exc:
        print(f"SQLite error: {exc}", file=sys.stderr)
        print(f"DB path: {os.path.abspath(args.db)}", file=sys.stderr)
        return 2

    write_csv(out_path, rows)
    print(f"Wrote {len(rows)} row(s) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
