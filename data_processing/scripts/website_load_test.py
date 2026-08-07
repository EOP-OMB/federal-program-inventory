#!/usr/bin/env python3
"""
Standalone website load test utility using curl via subprocess.

Traffic types:
1) CSV downloads
2) Static page requests
3) Search API requests

The scheduler is deterministic: on each request slot, it issues the traffic
type that is most behind its target share based on issued requests.
Tie-break preference: static > api > csv.
"""

import argparse
import csv
import datetime
import json
import math
import os
import select
import subprocess
import sys
import termios
import threading
import time
import tty
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Dict, List, Optional


TRAFFIC_STATIC = "static"
TRAFFIC_API = "api"
TRAFFIC_CSV = "csv"
TRAFFIC_ORDER = [TRAFFIC_STATIC, TRAFFIC_API, TRAFFIC_CSV]

STATIC_PATHS = [
    "/",
    "/category",
    "/about/fpi",
    "/about/terms",
    "/program/96.002",
    "/gwo/GWO_N3",
    "/pon/PON_861",
]

CSV_PATHS = [
    "/assets/files/all-program-data.csv",
]

API_PATH = "/api/search/programsTable"
API_BODIES = [
    {
        "query": "",
        "page": 1,
        "page_size": 10,
        "sort_field": "obligations",
        "sort_order": "desc",
        "agencySubAgency": [],
        "categorySubcategory": [],
        "assistanceTypes": [],
        "applicantTypes": [],
        "gwo": [],
        "pons": [],
    },
    {
        "query": "health",
        "page": 1,
        "page_size": 10,
        "sort_field": "obligations",
        "sort_order": "desc",
        "agencySubAgency": [],
        "categorySubcategory": [],
        "assistanceTypes": [],
        "applicantTypes": [],
        "gwo": [],
        "pons": [],
    },
    {
        "query": "96.002",
        "page": 1,
        "page_size": 10,
        "sort_field": "obligations",
        "sort_order": "desc",
        "agencySubAgency": [],
        "categorySubcategory": [],
        "assistanceTypes": [],
        "applicantTypes": [],
        "gwo": [],
        "pons": [],
    },
]


@dataclass
class RequestResult:
    request_id: int
    request_type: str
    issued_at_utc: str
    completed_at_utc: str
    method: str
    path: str
    status_code: int
    latency_ms: Optional[float]
    ok: bool
    curl_exit_code: int
    error: str


class KeypressWatcher:
    """Watches stdin and signals stop when any key is pressed."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop_requested(self) -> bool:
        return self._stop_event.is_set()

    def _run(self) -> None:
        if not sys.stdin.isatty():
            # Fallback: no TTY available; cannot reliably detect keypress.
            return

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while not self._stop_event.is_set():
                ready, _, _ = select.select([sys.stdin], [], [], 0.25)
                if ready:
                    sys.stdin.read(1)
                    self._stop_event.set()
                    return
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministic website load test using curl subprocess calls."
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Base URL for website under test (e.g., https://example.gov).",
    )
    parser.add_argument("--csv-share", type=float, default=10.0)
    parser.add_argument("--static-share", type=float, default=30.0)
    parser.add_argument("--api-share", type=float, default=60.0)
    parser.add_argument("--rps", type=float, default=10.0)
    parser.add_argument(
        "--duration-seconds",
        type=float,
        default=0.0,
        help="Optional max run time. 0 means run until keypress.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="curl --max-time value per request.",
    )
    parser.add_argument(
        "--connect-timeout-seconds",
        type=float,
        default=5.0,
        help="curl --connect-timeout value per request.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=200,
        help="Max concurrent curl subprocess workers.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Pass -k to curl (skip TLS certificate verification).",
    )
    return parser.parse_args()


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def join_url(base_url: str, path: str) -> str:
    if path.startswith("/"):
        return f"{base_url}{path}"
    return f"{base_url}/{path}"


def choose_traffic_type(
    shares: Dict[str, float],
    issued_total: int,
    issued_by_type: Dict[str, int],
) -> str:
    candidates = [t for t in TRAFFIC_ORDER if shares[t] > 0.0]
    if not candidates:
        raise ValueError("At least one traffic share must be greater than 0.")

    best_type = candidates[0]
    best_behind = -math.inf

    for traffic_type in candidates:
        expected = (issued_total * shares[traffic_type]) / 100.0
        behind = expected - issued_by_type[traffic_type]
        if behind > best_behind:
            best_behind = behind
            best_type = traffic_type

    return best_type


def drain_completed_requests(
    futures,
    all_results: List[RequestResult],
    completed_by_type: Dict[str, int],
    failures_by_type: Dict[str, int],
    latencies_by_type: Dict[str, List[float]],
    timeout: float,
):
    done, not_done = wait(futures, timeout=timeout, return_when=FIRST_COMPLETED)
    for fut in done:
        result = fut.result()
        all_results.append(result)
        completed_by_type[result.request_type] += 1
        if not result.ok:
            failures_by_type[result.request_type] += 1
        if result.latency_ms is not None:
            latencies_by_type[result.request_type].append(result.latency_ms)
    return set(not_done)


def curl_request(
    request_id: int,
    request_type: str,
    base_url: str,
    path: str,
    method: str,
    timeout_seconds: float,
    connect_timeout_seconds: float,
    insecure: bool,
    body: Optional[dict] = None,
) -> RequestResult:
    issued_at_utc = now_utc_iso()
    url = join_url(base_url, path)

    curl_cmd = [
        "curl",
        "-sS",
        "-o",
        "/dev/null",
        "-w",
        "%{http_code} %{time_total}",
        "--max-time",
        str(timeout_seconds),
        "--connect-timeout",
        str(connect_timeout_seconds),
        "-X",
        method,
    ]

    if insecure:
        curl_cmd.append("-k")

    if body is not None:
        curl_cmd.extend(
            [
                "-H",
                "Content-Type: application/json",
                "--data",
                json.dumps(body, separators=(",", ":")),
            ]
        )

    curl_cmd.append(url)

    try:
        completed = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        completed_at_utc = now_utc_iso()
        return RequestResult(
            request_id=request_id,
            request_type=request_type,
            issued_at_utc=issued_at_utc,
            completed_at_utc=completed_at_utc,
            method=method,
            path=path,
            status_code=0,
            latency_ms=None,
            ok=False,
            curl_exit_code=1,
            error=f"subprocess error: {exc}",
        )

    completed_at_utc = now_utc_iso()
    status_code = 0
    latency_ms: Optional[float] = None
    parse_error = ""

    stdout = (completed.stdout or "").strip()
    if stdout:
        parts = stdout.split()
        if len(parts) >= 2:
            try:
                status_code = int(parts[0])
            except ValueError:
                parse_error = f"invalid status code output: {stdout}"
            try:
                latency_ms = float(parts[1]) * 1000.0
            except ValueError:
                parse_error = f"invalid latency output: {stdout}"
        else:
            parse_error = f"unexpected curl output: {stdout}"
    else:
        parse_error = "empty curl output"

    ok_http = 200 <= status_code < 400
    ok = completed.returncode == 0 and ok_http and latency_ms is not None
    error_text = (completed.stderr or "").strip()

    if parse_error:
        error_text = f"{parse_error}; stderr={error_text}" if error_text else parse_error

    return RequestResult(
        request_id=request_id,
        request_type=request_type,
        issued_at_utc=issued_at_utc,
        completed_at_utc=completed_at_utc,
        method=method,
        path=path,
        status_code=status_code,
        latency_ms=latency_ms,
        ok=ok,
        curl_exit_code=completed.returncode,
        error=error_text,
    )


def percentile(sorted_values: List[float], pct: float) -> Optional[float]:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = math.ceil((pct / 100.0) * len(sorted_values))
    idx = max(1, rank) - 1
    idx = min(idx, len(sorted_values) - 1)
    return sorted_values[idx]


def write_input_parameters_csv(path: str, args: argparse.Namespace, shares: Dict[str, float]) -> None:
    rows = [
        ("generated_at_utc", now_utc_iso()),
        ("base_url", normalize_base_url(args.base_url)),
        ("csv_share", f"{args.csv_share}"),
        ("static_share", f"{args.static_share}"),
        ("api_share", f"{args.api_share}"),
        ("rps", f"{args.rps}"),
        ("duration_seconds", f"{args.duration_seconds}"),
        ("timeout_seconds", f"{args.timeout_seconds}"),
        ("connect_timeout_seconds", f"{args.connect_timeout_seconds}"),
        ("max_workers", f"{args.max_workers}"),
        ("insecure", str(args.insecure).lower()),
        ("normalized_csv_share", f"{shares[TRAFFIC_CSV]:.6f}"),
        ("normalized_static_share", f"{shares[TRAFFIC_STATIC]:.6f}"),
        ("normalized_api_share", f"{shares[TRAFFIC_API]:.6f}"),
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["parameter", "value"])
        writer.writerows(rows)


def write_request_log_csv(path: str, request_results: List[RequestResult]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "request_id",
                "request_type",
                "issued_at_utc",
                "completed_at_utc",
                "method",
                "path",
                "status_code",
                "latency_ms",
                "ok",
                "curl_exit_code",
                "error",
            ]
        )
        for r in request_results:
            writer.writerow(
                [
                    r.request_id,
                    r.request_type,
                    r.issued_at_utc,
                    r.completed_at_utc,
                    r.method,
                    r.path,
                    r.status_code,
                    "" if r.latency_ms is None else f"{r.latency_ms:.3f}",
                    "true" if r.ok else "false",
                    r.curl_exit_code,
                    r.error,
                ]
            )


def write_summary_csv(
    path: str,
    issued_by_type: Dict[str, int],
    completed_by_type: Dict[str, int],
    failures_by_type: Dict[str, int],
    latencies_by_type: Dict[str, List[float]],
) -> None:
    total_issued = sum(issued_by_type.values())
    total_completed = sum(completed_by_type.values())
    total_failures = sum(failures_by_type.values())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "request_type",
                "issued_count",
                "issued_share_pct",
                "completed_count",
                "failed_count",
                "success_count",
                "avg_latency_ms",
                "p90_latency_ms",
                "p95_latency_ms",
                "p99_latency_ms",
            ]
        )

        for traffic_type in TRAFFIC_ORDER:
            latency_values = sorted(latencies_by_type[traffic_type])
            completed = completed_by_type[traffic_type]
            failed = failures_by_type[traffic_type]
            success = completed - failed
            avg = (sum(latency_values) / len(latency_values)) if latency_values else None
            p90 = percentile(latency_values, 90)
            p95 = percentile(latency_values, 95)
            p99 = percentile(latency_values, 99)
            issued = issued_by_type[traffic_type]
            issued_share = (issued / total_issued * 100.0) if total_issued else 0.0

            writer.writerow(
                [
                    traffic_type,
                    issued,
                    f"{issued_share:.6f}",
                    completed,
                    failed,
                    success,
                    "" if avg is None else f"{avg:.3f}",
                    "" if p90 is None else f"{p90:.3f}",
                    "" if p95 is None else f"{p95:.3f}",
                    "" if p99 is None else f"{p99:.3f}",
                ]
            )

        writer.writerow([])
        writer.writerow(["metric", "value"])
        writer.writerow(["total_issued", total_issued])
        writer.writerow(["total_completed", total_completed])
        writer.writerow(["total_failed", total_failures])


def validate_and_normalize_shares(csv_share: float, static_share: float, api_share: float) -> Dict[str, float]:
    if csv_share < 0 or static_share < 0 or api_share < 0:
        raise ValueError("Traffic shares must be non-negative.")

    total = csv_share + static_share + api_share
    if total <= 0:
        raise ValueError("At least one traffic share must be greater than zero.")

    return {
        TRAFFIC_CSV: (csv_share / total) * 100.0,
        TRAFFIC_STATIC: (static_share / total) * 100.0,
        TRAFFIC_API: (api_share / total) * 100.0,
    }


def main() -> int:
    args = parse_args()
    if args.rps <= 0:
        raise ValueError("--rps must be > 0")
    if args.timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be > 0")
    if args.connect_timeout_seconds <= 0:
        raise ValueError("--connect-timeout-seconds must be > 0")
    if args.max_workers <= 0:
        raise ValueError("--max-workers must be > 0")

    shares = validate_and_normalize_shares(args.csv_share, args.static_share, args.api_share)
    base_url = normalize_base_url(args.base_url)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    ts_prefix = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    params_csv = os.path.join(script_dir, f"{ts_prefix}_input_parameters.csv")
    requests_csv = os.path.join(script_dir, f"{ts_prefix}_request_log.csv")
    summary_csv = os.path.join(script_dir, f"{ts_prefix}_summary.csv")

    write_input_parameters_csv(params_csv, args, shares)

    issued_by_type = {TRAFFIC_CSV: 0, TRAFFIC_STATIC: 0, TRAFFIC_API: 0}
    completed_by_type = {TRAFFIC_CSV: 0, TRAFFIC_STATIC: 0, TRAFFIC_API: 0}
    failures_by_type = {TRAFFIC_CSV: 0, TRAFFIC_STATIC: 0, TRAFFIC_API: 0}
    latencies_by_type: Dict[str, List[float]] = {
        TRAFFIC_CSV: [],
        TRAFFIC_STATIC: [],
        TRAFFIC_API: [],
    }

    static_index = 0
    api_index = 0
    csv_index = 0
    request_id = 0
    futures = set()
    all_results: List[RequestResult] = []
    key_watcher = KeypressWatcher()

    start_time = time.monotonic()
    next_tick = start_time
    end_time = start_time + args.duration_seconds if args.duration_seconds > 0 else None
    tick_interval = 1.0 / args.rps

    print("Load test started.")
    print("Press any key to stop and write CSV outputs.")
    print(f"Input parameters CSV: {params_csv}")
    print(f"Request log CSV:       {requests_csv}")
    print(f"Summary CSV:           {summary_csv}")

    key_watcher.start()

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        while True:
            # Drain any completed requests first.
            futures = drain_completed_requests(
                futures=futures,
                all_results=all_results,
                completed_by_type=completed_by_type,
                failures_by_type=failures_by_type,
                latencies_by_type=latencies_by_type,
                timeout=0,
            )

            now = time.monotonic()
            should_stop = key_watcher.stop_requested() or (end_time is not None and now >= end_time)
            if should_stop:
                break

            if now < next_tick:
                time.sleep(min(0.01, next_tick - now))
                continue

            issued_total = sum(issued_by_type.values())
            traffic_type = choose_traffic_type(shares, issued_total, issued_by_type)

            if traffic_type == TRAFFIC_STATIC:
                method = "GET"
                path = STATIC_PATHS[static_index]
                static_index = (static_index + 1) % len(STATIC_PATHS)
                body = None
            elif traffic_type == TRAFFIC_API:
                method = "POST"
                path = API_PATH
                body = API_BODIES[api_index]
                api_index = (api_index + 1) % len(API_BODIES)
            else:
                method = "GET"
                path = CSV_PATHS[csv_index]
                csv_index = (csv_index + 1) % len(CSV_PATHS)
                body = None

            issued_by_type[traffic_type] += 1
            request_id += 1
            fut = executor.submit(
                curl_request,
                request_id=request_id,
                request_type=traffic_type,
                base_url=base_url,
                path=path,
                method=method,
                timeout_seconds=args.timeout_seconds,
                connect_timeout_seconds=args.connect_timeout_seconds,
                insecure=args.insecure,
                body=body,
            )
            futures.add(fut)
            next_tick += tick_interval

            # Catch up if we're significantly behind schedule.
            now_after_issue = time.monotonic()
            if now_after_issue - next_tick > tick_interval:
                next_tick = now_after_issue

        # Stop issuing new requests. Wait briefly for in-flight requests.
        grace_deadline = time.monotonic() + max(1.0, min(args.timeout_seconds, 10.0))
        while futures and time.monotonic() < grace_deadline:
            futures = drain_completed_requests(
                futures=futures,
                all_results=all_results,
                completed_by_type=completed_by_type,
                failures_by_type=failures_by_type,
                latencies_by_type=latencies_by_type,
                timeout=0.2,
            )

    write_request_log_csv(requests_csv, all_results)
    write_summary_csv(summary_csv, issued_by_type, completed_by_type, failures_by_type, latencies_by_type)

    print("Load test stopped.")
    print(f"Total issued: {sum(issued_by_type.values())}")
    print(f"Total completed: {sum(completed_by_type.values())}")
    print(f"Total failed: {sum(failures_by_type.values())}")
    print("CSV outputs written.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
