#!/usr/bin/env python3
"""
Query USAspending assistance award archive CSVs within zip files.

For each zip in an input directory, extracts CSVs to a temp directory,
filters rows matching a given CFDA/ALN (`cfda_number`), writes a detail CSV,
then creates summary rollups by award and by award first fiscal year.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


def safe_filename_component(value: str) -> str:
    v = (value or "").strip()
    v = re.sub(r"[^A-Za-z0-9._-]+", "_", v)
    v = v.strip("._-")
    return v or "value"


def _reports_dir() -> Path:
    return Path(__file__).resolve().parent / "reports"


def _iter_zip_files(input_dir: Path) -> Iterable[Path]:
    for p in sorted(input_dir.iterdir()):
        if p.is_file() and p.suffix.lower() == ".zip":
            yield p


def _normalize_fieldnames(fieldnames: list[str]) -> dict[str, str]:
    # Map lowercase name -> original name (preserve original case)
    m: dict[str, str] = {}
    for name in fieldnames:
        if name is None:
            continue
        m[str(name).strip().lower()] = str(name)
    return m


def _choose_column(
    field_map: dict[str, str],
    desired_lower: str,
    *,
    fallback_lowers: Optional[list[str]] = None,
) -> str:
    if desired_lower in field_map:
        return field_map[desired_lower]
    for alt in fallback_lowers or []:
        if alt in field_map:
            return field_map[alt]
    raise KeyError(desired_lower)


def _write_rows_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Filter USAspending assistance CSVs inside zip files by CFDA number, "
            "then produce detail and summary reports."
        )
    )
    parser.add_argument(
        "--filepath",
        required=True,
        help="Directory containing USAspending award archive .zip files.",
    )
    parser.add_argument(
        "--cfda",
        required=True,
        help='CFDA/ALN to match against `cfda_number` (e.g. "10.205").',
    )
    parser.add_argument(
        "--temp-dir",
        required=True,
        help="Temporary directory used to extract CSVs for processing.",
    )
    args = parser.parse_args(argv)

    input_dir = Path(args.filepath).expanduser().resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory does not exist: {input_dir}", file=sys.stderr)
        return 2

    temp_dir = Path(args.temp_dir).expanduser().resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)

    cfda = str(args.cfda).strip()
    today = _dt.date.today().isoformat()
    cfda_safe = safe_filename_component(cfda)

    # Initialize an empty list to store output data.
    output_rows: list[list[str]] = []
    output_header: Optional[list[str]] = None

    for zip_path in _iter_zip_files(input_dir):
        print(zip_path.name)

        with zipfile.ZipFile(zip_path, "r") as zf:
            csv_members = [m for m in zf.namelist() if m.lower().endswith(".csv")]
            for member in csv_members:
                zf.extract(member, path=temp_dir)

            for member in csv_members:
                csv_path = (temp_dir / member).resolve()
                if not csv_path.exists() or not csv_path.is_file():
                    continue

                print(csv_path.name)

                with csv_path.open("r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    if not reader.fieldnames:
                        continue

                    field_map = _normalize_fieldnames(list(reader.fieldnames))
                    try:
                        cfda_col = _choose_column(field_map, "cfda_number")
                    except KeyError:
                        raise KeyError(
                            f"Required column `cfda_number` not found in {csv_path}"
                        )

                    if output_header is None:
                        output_header = list(reader.fieldnames)
                        output_rows.append(output_header)

                    for row in reader:
                        if (row.get(cfda_col) or "").strip() == cfda:
                            output_rows.append([row.get(col, "") for col in output_header])

                try:
                    csv_path.unlink()
                except OSError:
                    pass

    reports_dir = _reports_dir()
    reports_dir.mkdir(parents=True, exist_ok=True)

    detail_path = reports_dir / f"{today}_{cfda_safe}_cfda_detail.csv"
    _write_rows_csv(detail_path, output_rows)
    print(f"Saved {detail_path}")

    if not output_rows or output_header is None:
        print("No CSV data found; skipping summary outputs.", file=sys.stderr)
        return 0

    df = pd.DataFrame(output_rows[1:], columns=output_header)
    df_cols = _normalize_fieldnames(list(df.columns))

    try:
        award_key_col = _choose_column(df_cols, "assistance_award_unique_key")
        fiscal_year_col = _choose_column(df_cols, "action_date_fiscal_year")
        outlay_col = _choose_column(df_cols, "total_outlayed_amount_for_overall_award")
        obligation_col = _choose_column(
            df_cols,
            "total_obligation_amount",
            fallback_lowers=["federal_action_obligation"],
        )
    except KeyError as exc:
        print(
            f"Missing required column for summarization: {exc}. "
            f"Available columns: {list(df.columns)}",
            file=sys.stderr,
        )
        return 2

    df[obligation_col] = pd.to_numeric(df[obligation_col], errors="coerce").fillna(0.0)
    df[outlay_col] = pd.to_numeric(df[outlay_col], errors="coerce").fillna(0.0)
    df[fiscal_year_col] = pd.to_numeric(df[fiscal_year_col], errors="coerce")

    df_award = (
        df.groupby(award_key_col, dropna=False, sort=False)
        .agg(
            obligations=(obligation_col, "sum"),
            outlays=(outlay_col, "first"),
            award_first_fiscal_year=(fiscal_year_col, "min"),
        )
        .reset_index()
    )

    df_award = df_award[
        [award_key_col, "award_first_fiscal_year", "obligations", "outlays"]
    ]

    award_path = reports_dir / f"{today}_{cfda_safe}_cfda_summary_by_award.csv"
    df_award.to_csv(award_path, index=False)
    print(f"Saved {award_path}")

    df_year = (
        df_award.groupby("award_first_fiscal_year", dropna=False, sort=False)
        .agg(obligations=("obligations", "sum"), outlays=("outlays", "sum"))
        .reset_index()
        .rename(columns={"award_first_fiscal_year": "year"})
    )

    year_path = reports_dir / f"{today}_{cfda_safe}_cfda_summary_by_year.csv"
    df_year.to_csv(year_path, index=False)
    print(f"Saved {year_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

