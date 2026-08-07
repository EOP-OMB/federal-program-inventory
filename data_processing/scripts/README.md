# Weekly ALN Change Detection Script

## Overview
The `weekly_aln.detector.py` script automatically monitors SAM.gov for changes in Assistance Listing Numbers (ALNs) on a weekly basis. It detects new ALNs, updated ALNs, and inactive ALNs by comparing current data against a stored baseline.

## Features
- **Automated Detection**: Identifies new, updated, and inactive ALNs
- **Baseline Management**: Maintains weekly snapshots for comparison
- **Multiple Reports**: Generates both detailed JSON and human-readable summaries
- **Comprehensive Logging**: Full execution logs with timestamps
- **Error Handling**: Robust error handling for API failures
- **Email Notifications**: Optional email notifications for changes (configurable)

## Quick Start

### First Run (Establishes Baseline)
```bash
cd /Users/{your_user}/folio/omb-fpi/data_processing
source venv/bin/activate
python scripts/weekly_aln.detector.py
```

The first run will:
- Fetch all current ALNs from SAM.gov (currently 2,555 ALNs)
- Create a baseline snapshot in `scripts/baseline/`
- Generate an initial report in `scripts/reports/`
- Log "first run" status (no changes detected)

### Subsequent Runs
Every subsequent run will:
- Compare current ALNs against the most recent baseline
- Detect and report any changes
- Update the baseline with current data
- Generate detailed change reports

## Output Files

### Directory Structure
```
scripts/
├── baseline/           # Baseline snapshots (auto-managed)
│   └── YYYY-MM-DD_aln_snapshot.json
├── reports/           # Change reports
│   ├── YYYY-MM-DD_detailed_report.json
│   └── YYYY-MM-DD_summary_report.txt
└── logs/              # Execution logs (if configured)
    └── weekly_aln.log
```

### Report Content
- **New ALNs**: Recently published assistance listings
- **Updated ALNs**: ALNs with modified data (title, objectives, etc.)
- **Inactive ALNs**: ALNs no longer available on SAM.gov
- **Summary Statistics**: Total counts and execution details

## Scheduling Options

### 1. Cron (Recommended for Local/Server)
```bash
# Run every Tuesday at 3:27 AM EST (when new data is likely available)
27 3 * * 2 cd /Users/{your_user}/folio/omb-fpi/data_processing && source venv/bin/activate && python scripts/weekly_aln.detector.py >> scripts/logs/weekly_aln.log 2>&1
```

### 2. GitHub Actions (Recommended for CI/CD)
Create `.github/workflows/weekly-aln-check.yml`:
```yaml
name: Weekly ALN Change Detection
on:
  schedule:
    - cron: '27 8 * * 2'  # Every Tuesday at 3:27 AM EST (8:27 UTC)
  workflow_dispatch:      # Manual trigger

jobs:
  detect_changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          cd data_processing
          pip install requests
      - name: Run ALN detector
        run: |
          cd data_processing
          python scripts/weekly_aln.detector.py
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: aln-reports
          path: data_processing/scripts/reports/
```

### 3. Cloud Functions (AWS Lambda, Google Cloud Functions)
The script is designed to run in serverless environments:
- Package the script with dependencies
- Set up scheduled triggers (CloudWatch Events, Cloud Scheduler)
- Configure environment variables for storage paths

## Configuration

### Environment Variables (Optional)
```bash
export EMAIL_ENABLED=true
export EMAIL_RECIPIENTS="admin@agency.gov,analyst@agency.gov"
export SMTP_SERVER="smtp.agency.gov"
export SMTP_PORT=587
```

### Script Parameters
The script is designed to run without parameters, but you can modify:
- `SAM_API_BASE_URL`: Change API endpoint if needed
- File paths for baseline/report storage
- Logging configuration
- Email notification settings

## Monitoring & Maintenance

### Log Monitoring
Check logs for:
- API failures or rate limiting
- Unexpected change volumes
- Performance issues

### Baseline Management
- Baselines are automatically managed (keeps most recent)
- No manual intervention required
- Old baselines can be safely archived

### Expected Changes
Typical weekly changes:
- **New ALNs**: 0-5 per week (new federal programs)
- **Updated ALNs**: 10-50 per week (routine updates)
- **Inactive ALNs**: 0-2 per week (program discontinuation)

## Troubleshooting

### Common Issues
1. **"No module named 'requests'"**
   - Solution: Ensure virtual environment is activated
   - Run: `source venv/bin/activate && pip install requests`

2. **"SAM.gov API Error"**
   - Solution: Check network connectivity and API status
   - The script will retry automatically

3. **"Permission denied"**
   - Solution: Ensure write permissions for scripts/ directory
   - Run: `chmod -R 755 scripts/`

### API Rate Limits
- SAM.gov allows reasonable API usage
- Script includes retry logic with exponential backoff
- Contact SAM.gov support if persistent issues occur

## Integration with Existing Pipeline

The script is designed to complement the existing data pipeline:
- **Independent Operation**: Runs separately from main ETL process
- **No Dependencies**: Doesn't require transformed_data.db or other pipeline outputs
- **Output Compatibility**: Reports can be integrated into dashboards or notifications

### Future Integration Ideas
- Add ALN change alerts to the FPI website
- Include change statistics in weekly agency reports
- Trigger pipeline updates when significant changes detected
- Archive historical change data for trend analysis

## Support
For questions or issues with the ALN change detection script:
1. Check logs for specific error messages
2. Verify SAM.gov API availability
3. Review this README for configuration options
4. Contact the FPI development team for assistance

# ALN Detection Script
This script pulls all ALNs from SAM.gov and flattens the data into a single csv in the reports directory.

# download-usaspending-files.py

This downloads award data archive files from https://www.usaspending.gov/download_center/award_data_archive.  Note that the years and suffix may change over time.  Also note that usaspending.gov will throttle after ~10 files, so the script may take multiple runs.

# summarize-usaspending-files.py

This opens the downloaded zip files in memory, summarizes all of the csv data by ALN, and saves the output to a csv file.

# summarize-sam-data.py

This opens the extracted assistance-listings.json file, summarizes available data by ALN, and saves the output to a csv file.

# verify_aln_outlays_by_year.py

This pulls obligations and outlays from the API.  Example command:  `python3 verify_aln_outlays_by_year.py --aln 10.205 --year 2016 --max-action-date 2026-03-06`.

Note: this pulls the latest data from the API, so if this is used for verification, there may be differences due to recent activity.

# extract_assistance_outlay_aggregation_by_aln.py

This pulls outlay and obligation data by ALN from the temp_db created by the data pipeline.  Example command:  `python3 extract_assistance_outlay_aggregation_by_aln.py --aln "10.205"`

# query_usaspending_csvs.py

This iterates through a directory of usaspending award archive zip files and generates a detailed list of supporting files and summary lists by award and year.  Example command:  `python3 query_usaspending_csvs.py --filepath ~/usaspending-awards-data/assistance --cfda 93.778 --temp-dir ~/tmp`

# website_load_test.py

Standalone website load test script that issues HTTP requests through `curl` subprocess calls (requires curl 8+ available on PATH).

## What it tests

- CSV downloads
- Static pages
- Search API requests

The static-page traffic always rotates through this fixed circular list:

- `/`
- `/category`
- `/about/fpi`
- `/about/terms`
- `/program/96.002`
- `/gwo/GWO_N3`
- `/pon/PON_861`

## Request mix behavior

The scheduler is deterministic based on requests **issued** (not completed):

- At each request slot, the script computes which traffic type is most behind its target share.
- Tie-break preference is `static > api > csv`.
- Any traffic type with a share of `0` is never selected.
- Within each selected traffic type, requests rotate in circular order through that type's configured list (static paths, API bodies, and CSV paths).

## Usage

```bash
python3 data_processing/scripts/website_load_test.py \
  --base-url "https://your-site.example.gov" \
  --csv-share 10 \
  --static-share 30 \
  --api-share 60 \
  --rps 10
```

Press any key to stop the run. You can also set a fixed run time with `--duration-seconds`.

## Parameters

- `--base-url` (required): base URL to test
- `--csv-share` (default `10`)
- `--static-share` (default `30`)
- `--api-share` (default `60`)
- `--rps` (default `10`)
- `--duration-seconds` (default `0`; `0` means run until keypress)
- `--timeout-seconds` (default `30`)
- `--connect-timeout-seconds` (default `5`)
- `--max-workers` (default `200`)
- `--insecure` (optional; passes `-k` to curl)

If shares do not sum to exactly 100, they are normalized proportionally.

## Outputs

All outputs are written to the same directory as the script (`data_processing/scripts/`) and prefixed with a UTC timestamp:

- `<timestamp>_input_parameters.csv`
- `<timestamp>_request_log.csv`
- `<timestamp>_summary.csv`

### request_log CSV columns

- `request_id`
- `request_type`
- `issued_at_utc`
- `completed_at_utc`
- `method`
- `path`
- `status_code`
- `latency_ms`
- `ok`
- `curl_exit_code`
- `error`

### summary CSV contents

- Per traffic type:
  - issued count and issued share
  - completed count
  - failed count
  - success count
  - average latency
  - p90, p95, p99 latency
- Overall totals:
  - total issued
  - total completed
  - total failed