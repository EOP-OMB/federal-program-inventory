#!/usr/bin/env python3
"""
Download USAspending transaction data for a given Assistance Listing Number (ALN),
group by assistance_award_unique_key, and bucket outlays by the award's first
(earliest) action_date fiscal year.

Obligations are summed by each transaction's action_date fiscal year.

This script uses the USAspending "download transactions" API so we can request
specific columns and handle larger result sets via date-range chunking.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import math
import os
import re
import sqlite3
import sys
import time
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


API_BASE_URL = "https://api.usaspending.gov"
DOWNLOAD_TRANSACTIONS_PATH = "/api/v2/download/transactions/"
DOWNLOAD_STATUS_PATH = "/api/v2/download/status"
DOWNLOAD_COUNT_PATH = "/api/v2/download/count/"


DEFAULT_AWARD_TYPE_CODES_ASSISTANCE = [
    "02",  # Grant
    "03",  # Formula Grant
    "04",  # Project Grant
    "05",  # Cooperative Agreement
    "06",  # Direct Payment for Specified Use
    "07",  # Direct Loan
    "08",  # Guaranteed/Insured Loan
    "09",  # Insurance
    "10",  # Direct Payment with Unrestricted Use
    "11",  # Other
    "-1",  # Unknown/Other
]


@dataclass(frozen=True)
class DateRange:
    start_date: dt.date
    end_date: dt.date

    def to_time_period_filter(self) -> Dict[str, str]:
        return {
            "date_type": "action_date",
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
        }


def _abs_url(path_or_url: str) -> str:
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    return API_BASE_URL.rstrip("/") + "/" + path_or_url.lstrip("/")


def safe_filename_component(value: str) -> str:
    """
    Keep filenames predictable and portable across OS/filesystems.
    Allows letters, numbers, dot, dash, underscore. Everything else -> underscore.
    """
    v = (value or "").strip()
    v = re.sub(r"[^A-Za-z0-9._-]+", "_", v)
    v = v.strip("._-")
    return v or "value"


def zip_filename_for_range(aln: str, dr: "DateRange") -> str:
    aln_part = safe_filename_component(aln)
    return f"{aln_part}-{dr.start_date.isoformat()}_{dr.end_date.isoformat()}.zip"


def write_bytes_atomic_overwrite(path: str, data: bytes) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "wb") as f:
        f.write(data)
    os.replace(tmp_path, path)


def _sleep_with_backoff(attempt: int, base_s: float = 0.75, cap_s: float = 20.0) -> None:
    sleep_s = min(cap_s, base_s * (2**attempt))
    time.sleep(sleep_s)


def _request_json_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    json_body: Optional[Dict[str, Any]] = None,
    timeout_s: int = 60,
    max_attempts: int = 8,
) -> Dict[str, Any]:
    last_exc: Optional[BaseException] = None
    for attempt in range(max_attempts):
        try:
            resp = session.request(method, url, json=json_body, timeout=timeout_s)
            if resp.status_code in (429, 500, 502, 503, 504):
                _sleep_with_backoff(attempt)
                continue
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last_exc = exc
            _sleep_with_backoff(attempt)
            continue
    raise RuntimeError(f"Request failed after {max_attempts} attempts: {url}") from last_exc


def _download_bytes_with_retries(
    session: requests.Session,
    url: str,
    *,
    timeout_s: int = 120,
    max_attempts: int = 6,
) -> bytes:
    last_exc: Optional[BaseException] = None
    for attempt in range(max_attempts):
        try:
            with session.get(url, stream=True, timeout=timeout_s) as resp:
                if resp.status_code in (429, 500, 502, 503, 504):
                    _sleep_with_backoff(attempt)
                    continue
                resp.raise_for_status()
                return resp.content
        except requests.RequestException as exc:
            last_exc = exc
            _sleep_with_backoff(attempt)
            continue
    raise RuntimeError(f"Download failed after {max_attempts} attempts: {url}") from last_exc


def build_filters(
    aln: str,
    award_type_codes: List[str],
    date_range: DateRange,
) -> Dict[str, Any]:
    # The download endpoint uses the same general filter structure as advanced search downloads.
    # For ALN/CFDA filters, USAspending uses program_numbers (e.g., "10.555").
    return {
        "award_type_codes": award_type_codes,
        "program_numbers": [aln],
        "time_period": [date_range.to_time_period_filter()],
    }


def get_transaction_count(
    session: requests.Session,
    filters: Dict[str, Any],
) -> Dict[str, Any]:
    url = _abs_url(DOWNLOAD_COUNT_PATH)
    payload = {"filters": filters, "spending_level": "transactions"}
    return _request_json_with_retries(session, "POST", url, json_body=payload)


def request_transaction_download(
    session: requests.Session,
    filters: Dict[str, Any],
    columns: List[str],
    *,
    file_format: str = "csv",
    limit: int = 500_000,
) -> Dict[str, Any]:
    url = _abs_url(DOWNLOAD_TRANSACTIONS_PATH)
    payload: Dict[str, Any] = {
        "filters": filters,
        "columns": columns,
        "file_format": file_format,
        "limit": limit,
    }
    return _request_json_with_retries(session, "POST", url, json_body=payload, timeout_s=90)


def poll_download_finished(
    session: requests.Session,
    file_name: str,
    *,
    timeout_s: int = 60 * 30,
    poll_interval_s: float = 2.0,
) -> Dict[str, Any]:
    start = time.time()
    while True:
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Timed out waiting for download to finish: {file_name}")

        status_url = _abs_url(f"{DOWNLOAD_STATUS_PATH}?file_name={file_name}")
        status = _request_json_with_retries(session, "GET", status_url, timeout_s=60)
        state = status.get("status")

        if state == "finished":
            return status
        if state == "failed":
            raise RuntimeError(f"Download failed: {status.get('message')}")

        time.sleep(poll_interval_s)
        poll_interval_s = min(15.0, poll_interval_s * 1.2)


def split_date_range(dr: DateRange) -> Tuple[DateRange, DateRange]:
    days = (dr.end_date - dr.start_date).days
    if days <= 0:
        return (dr, dr)
    mid = dr.start_date + dt.timedelta(days=days // 2)
    left = DateRange(start_date=dr.start_date, end_date=mid)
    right = DateRange(start_date=mid + dt.timedelta(days=1), end_date=dr.end_date)
    return left, right


def chunk_date_ranges_to_limit(
    session: requests.Session,
    aln: str,
    award_type_codes: List[str],
    initial_range: DateRange,
    *,
    max_rows: int = 500_000,
    max_splits: int = 64,
) -> List[DateRange]:
    """
    Use /download/count to split the requested date range until each chunk is within max_rows.
    """
    chunks: List[DateRange] = []
    queue: List[DateRange] = [initial_range]
    splits = 0

    while queue:
        dr = queue.pop(0)
        filters = build_filters(aln=aln, award_type_codes=award_type_codes, date_range=dr)
        count_info = get_transaction_count(session, filters)

        calculated = int(count_info.get("calculated_transaction_count") or 0)
        maximum = int(count_info.get("maximum_transaction_limit") or max_rows)
        too_many = bool(count_info.get("transaction_rows_gt_limit"))

        effective_max = min(maximum, max_rows)
        if (not too_many) and calculated <= effective_max:
            chunks.append(dr)
            continue

        if splits >= max_splits:
            raise RuntimeError(
                f"Exceeded max splits while chunking date range; last count={calculated}, "
                f"range={dr.start_date.isoformat()}..{dr.end_date.isoformat()}"
            )

        if dr.start_date >= dr.end_date:
            raise RuntimeError(
                f"Single-day range still exceeds limit; count={calculated}, date={dr.start_date.isoformat()}"
            )

        left, right = split_date_range(dr)
        queue.insert(0, right)
        queue.insert(0, left)
        splits += 1

    chunks.sort(key=lambda r: (r.start_date, r.end_date))
    return chunks


def iter_csv_rows_from_zip_bytes(zip_bytes: bytes) -> Iterable[Dict[str, str]]:
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    if not csv_names:
        raise RuntimeError("No CSV files found in downloaded zip")

    for name in csv_names:
        with zf.open(name, "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.DictReader(text)
            for row in reader:
                yield row


def parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_action_year(date_str: str) -> Optional[int]:
    s = (date_str or "").strip()
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10]).year
    except ValueError:
        return None


def parse_action_date(date_str: str) -> Optional[dt.date]:
    s = (date_str or "").strip()
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10])
    except ValueError:
        return None


def parse_last_modified_date(value: str) -> Optional[dt.date]:
    # USAspending commonly represents last_modified_date as an ISO date or timestamp;
    # we only need the date portion.
    s = (value or "").strip()
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10])
    except ValueError:
        return None


def fiscal_year_from_date(d: dt.date) -> int:
    # Federal fiscal year runs Oct 1 .. Sep 30
    return d.year + 1 if d.month >= 10 else d.year


def parse_action_fiscal_year(date_str: str) -> Optional[int]:
    d = parse_action_date(date_str)
    if d is None:
        return None
    return fiscal_year_from_date(d)


def parse_iso_date_arg(value: str) -> dt.date:
    s = (value or "").strip()
    try:
        return dt.date.fromisoformat(s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid date (expected YYYY-MM-DD): {value!r}") from exc


def format_money(x: float) -> str:
    return f"{x:,.2f}"


def load_db_obligations_by_year(db_path: str, aln: str, min_year: int) -> Dict[int, float]:
    query = """
        SELECT fiscal_year, SUM(obligation) AS total_obligation
        FROM usaspending_assistance_outlay_aggregation
        WHERE cfda_number = ?
          AND fiscal_year >= ?
        GROUP BY fiscal_year
    """
    out: Dict[int, float] = {}
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(query, (aln, min_year))
        for fiscal_year, total_obligation in cur.fetchall():
            if fiscal_year is None or total_obligation is None:
                continue
            out[int(fiscal_year)] = float(total_obligation)
    return out


def print_last_modified_exceeds_years(years: set[int], max_action_date: Optional[dt.date]) -> None:
    if max_action_date is None or not years:
        return
    print("")
    years_csv = ", ".join(str(y) for y in sorted(years))
    print(
        "Fiscal years with at least one transaction where "
        f"last_modified_date > {max_action_date.isoformat()}: {years_csv}"
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify outlays by ALN/CFDA by downloading USAspending transactions, "
            "grouping by assistance_award_unique_key, bucketing outlays by the "
            "award's first (earliest) action_date fiscal year, and summing "
            "obligations by transaction fiscal year."
        )
    )
    parser.add_argument("--aln", required=True, help='Assistance Listing Number (e.g. "10.555")')
    parser.add_argument("--year", required=True, type=int, help="Earliest fiscal year to include (inclusive)")
    parser.add_argument(
        "--award-type-codes",
        nargs="+",
        default=DEFAULT_AWARD_TYPE_CODES_ASSISTANCE,
        help="Award type codes to include (defaults to assistance types)",
    )
    parser.add_argument(
        "--max-rows-per-download",
        type=int,
        default=500_000,
        help="Max rows per download request (will chunk date ranges if needed)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=60 * 30,
        help="Max time to wait for each download job to finish",
    )
    parser.add_argument(
        "--award-key-field",
        default="assistance_award_unique_key",
        help="CSV field name for assistance award unique key",
    )
    parser.add_argument(
        "--action-date-field",
        default="action_date",
        help="CSV field name for action date",
    )
    parser.add_argument(
        "--outlay-field",
        default="total_outlayed_amount_for_overall_award",
        help="CSV field name for outlays amount",
    )
    parser.add_argument(
        "--max-action-date",
        type=parse_iso_date_arg,
        default=None,
        help="Max action_date (YYYY-MM-DD). Rows after this date are excluded.",
    )
    args = parser.parse_args(argv)

    # The website logic buckets by fiscal year, so interpret --year as fiscal year.
    # FY N starts on Oct 1 of calendar year N-1.
    start_date = dt.date(args.year - 1, 10, 1)
    end_date = dt.date.today()
    if args.max_action_date is not None:
        end_date = min(end_date, args.max_action_date)
    if start_date > end_date:
        raise SystemExit("Invalid date range: start is after end (check --year and --max-action-date)")

    requested_columns = [
        args.award_key_field,
        args.action_date_field,
        args.outlay_field,
        "federal_action_obligation",
        "last_modified_date",
        "original_loan_subsidy_cost"
    ]

    session = requests.Session()
    session.headers.update({"User-Agent": "omb-fpi/verify-aln-outlays (requests)"})

    initial_range = DateRange(start_date=start_date, end_date=end_date)
    date_ranges = chunk_date_ranges_to_limit(
        session,
        aln=args.aln,
        award_type_codes=args.award_type_codes,
        initial_range=initial_range,
        max_rows=args.max_rows_per_download,
    )

    award_min_year: Dict[str, int] = {}
    # total_outlayed_amount_for_overall_award is an award-level total; do not sum it
    # across transactions. Use the maximum observed non-null value per award.
    award_outlay_max: Dict[str, float] = {}
    obligations_by_action_year: Dict[int, float] = {}
    years_with_last_modified_after_max: set[int] = set()

    for dr in date_ranges:
        filters = build_filters(aln=args.aln, award_type_codes=args.award_type_codes, date_range=dr)
        dl = request_transaction_download(
            session,
            filters,
            requested_columns,
            limit=args.max_rows_per_download,
        )

        file_name = dl.get("file_name")
        file_url = dl.get("file_url")
        if not file_name:
            raise RuntimeError(f"Unexpected download response missing file_name: {dl}")

        status = poll_download_finished(session, file_name, timeout_s=args.timeout_seconds)
        file_url = status.get("file_url") or file_url
        if not file_url:
            raise RuntimeError(f"Unexpected download status missing file_url: {status}")

        zip_bytes = _download_bytes_with_retries(session, _abs_url(file_url))
        zip_name = zip_filename_for_range(args.aln, dr)
        write_bytes_atomic_overwrite(os.path.join(os.getcwd(), zip_name), zip_bytes)
        for row in iter_csv_rows_from_zip_bytes(zip_bytes):
            award_key = (row.get(args.award_key_field) or "").strip()
            if not award_key:
                continue

            action_date = parse_action_date(row.get(args.action_date_field) or "")
            if action_date is None:
                continue
            if args.max_action_date is not None and action_date > args.max_action_date:
                continue

            fy = fiscal_year_from_date(action_date)

            if args.max_action_date is not None:
                last_mod = parse_last_modified_date(row.get("last_modified_date") or "")
                if last_mod is not None and last_mod > args.max_action_date:
                    years_with_last_modified_after_max.add(fy)

            prev = award_min_year.get(award_key)
            award_min_year[award_key] = fy if prev is None else min(prev, fy)

            outlay = parse_float(row.get(args.outlay_field))
            if outlay is not None:
                prev_outlay = award_outlay_max.get(award_key)
                award_outlay_max[award_key] = outlay if prev_outlay is None else max(prev_outlay, outlay)

            obligation = parse_float(row.get("federal_action_obligation")) + parse_float(row.get("original_loan_subsidy_cost"))
            if obligation is not None:
                obligations_by_action_year[fy] = obligations_by_action_year.get(fy, 0.0) + obligation

    totals_by_first_year: Dict[int, float] = {}
    counts_by_first_year: Dict[int, int] = {}

    for award_key, first_year in award_min_year.items():
        outlays = award_outlay_max.get(award_key)
        if outlays is not None:
            totals_by_first_year[first_year] = totals_by_first_year.get(first_year, 0.0) + outlays

        if outlays is None:
            continue
        counts_by_first_year[first_year] = counts_by_first_year.get(first_year, 0) + 1

    years = sorted(
        y
        for y in (set(totals_by_first_year.keys()) | set(obligations_by_action_year.keys()))
        if y >= args.year
    )
    if not years:
        print(
            "No results found. "
            "If this ALN is valid, try adjusting award type codes or verify column names."
        )
        return 0

    print(f"ALN: {args.aln}")
    print(f"Date range (action_date): {start_date.isoformat()} .. {end_date.isoformat()}")
    print(
        "Method: group by assistance_award_unique_key; "
        "take max(total_outlayed_amount_for_overall_award) per award; "
        "bucket outlays to fiscal year of earliest action_date per award; "
        "sum obligations by each transaction action_date fiscal year."
    )
    print("")
    print("year|award_count|total_outlays|total_obligations")
    for y in years:
        total = totals_by_first_year.get(y, 0.0)
        oblig = obligations_by_action_year.get(y, 0.0)
        cnt = counts_by_first_year.get(y, 0)
        print(f"{y}|{cnt}|{format_money(total)}|{format_money(oblig)}")

    if args.year in totals_by_first_year:
        print("")
        print(f"Requested fiscal year {args.year} total_outlays = {format_money(totals_by_first_year[args.year])}")
    if args.year in obligations_by_action_year:
        print(
            f"Requested fiscal year {args.year} total_obligations = "
            f"{format_money(obligations_by_action_year[args.year])}"
        )

    db_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "website", "transformed_data.db")
    )
    db_obligations_by_year = load_db_obligations_by_year(db_path, args.aln, args.year)

    compare_years = sorted(
        set(obligations_by_action_year.keys()) | set(db_obligations_by_year.keys())
    )
    if compare_years:
        latest_year = max(compare_years)
        years_to_compare = [y for y in compare_years if y != latest_year]
    else:
        years_to_compare = []

    if not years_to_compare:
        print("")
        print("Obligation comparison skipped: no non-latest fiscal years available.")
        print_last_modified_exceeds_years(years_with_last_modified_after_max, args.max_action_date)
        return 0

    mismatches: List[Tuple[int, float, float]] = []
    for y in years_to_compare:
        api_value = obligations_by_action_year.get(y, 0.0)
        db_value = db_obligations_by_year.get(y, 0.0)
        if round(api_value) != round(db_value):
            mismatches.append((y, api_value, db_value))

    print("")
    if not mismatches:
        print("API and database obligations match to the nearest dollar for all checked years.")
    else:
        print("Obligation differences by year (API vs database):")
        for y, api_value, db_value in mismatches:
            diff = api_value - db_value
            print(
                f"{y}: api={format_money(api_value)}, "
                f"database={format_money(db_value)}, diff={format_money(diff)}"
            )

    print_last_modified_exceeds_years(years_with_last_modified_after_max, args.max_action_date)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise SystemExit(130)
