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