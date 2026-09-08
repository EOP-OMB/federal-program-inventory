#!/usr/bin/env python3
"""
Weekly Assistance Listing Number (ALN) Change Detection Script

Monitors SAM.gov for new or updated ALNs by comparing against previous week's snapshot.
Designed to run weekly at low-traffic times (e.g., 3:27 AM EST on Mondays).

Output:
- Text files with new/updated ALN lists
- JSON report with detailed changes
- Baseline snapshot for next week's comparison
"""

import json
import os
import sys
import time
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
import logging

# Configuration
SCRIPT_DIR = Path(__file__).parent
BASELINE_DIR = SCRIPT_DIR / "baseline"
REPORTS_DIR = SCRIPT_DIR / "reports"
LOGS_DIR = SCRIPT_DIR / "logs"
TRANSFORMED_DB_PATH = SCRIPT_DIR.parent.parent / "website" / "transformed_data.db"

# SAM.gov API endpoint for ALN search
SAM_SEARCH_URL = "https://sam.gov/api/prod/sgs/v1/search/?index=cfda&page=0&mode=search&size=10000&is_active=true"

# Create directories if they don't exist
BASELINE_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'weekly_detector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def fetch_current_alns():
    """
    Fetch current ALN data from SAM.gov search API.
    
    Returns:
        dict: API response with ALN data
    """
    logger.info("Fetching current ALN data from SAM.gov...")
    
    try:
        response = requests.get(SAM_SEARCH_URL, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if "_embedded" not in data or "results" not in data["_embedded"]:
            raise ValueError("Unexpected API response structure")
        
        aln_count = len(data["_embedded"]["results"])
        logger.info(f"Successfully fetched {aln_count} ALNs from SAM.gov")
        
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from SAM.gov: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {e}")
        raise


def load_baseline_snapshot():
    """
    Load the most recent baseline snapshot for comparison.
    
    Returns:
        dict or None: Previous week's ALN data, or None if no baseline exists
    """
    baseline_files = list(BASELINE_DIR.glob("*_aln_snapshot.json"))
    
    if not baseline_files:
        logger.warning("No baseline snapshot found. This appears to be the first run.")
        return None
    
    # Get the most recent baseline file
    latest_baseline = max(baseline_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Loading baseline from: {latest_baseline.name}")
    
    try:
        with open(latest_baseline, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading baseline file: {e}")
        return None


def create_aln_lookup(api_data):
    """
    Create a lookup dictionary of ALNs with key metadata.
    
    Args:
        api_data (dict): SAM.gov API response
        
    Returns:
        dict: ALN lookup with programNumber as key
    """
    aln_lookup = {}
    
    for item in api_data.get("_embedded", {}).get("results", []):
        program_number = item.get("programNumber")
        if program_number:
            # Extract organization hierarchy
            org_hierarchy = item.get("organizationHierarchy", [])
            agency = ""
            sub_agency = ""
            
            for org in org_hierarchy:
                # Handle both test format (strings) and real API format (objects)
                if isinstance(org, str):
                    # Test format: simple string, treat as agency
                    if not agency:
                        agency = org.title()
                elif isinstance(org, dict):
                    # Real API format: objects with level and name
                    if org.get("level") == 1:
                        agency = org.get("name", "").title()
                    elif org.get("level") == 2:
                        sub_agency = org.get("name", "").title()
            
            # Extract most recent fiscal year from historical index
            historical_index = item.get("historicalIndex", [])
            most_recent_fy = ""
            if historical_index:
                # Find the entry with the most recent fiscal year
                most_recent_entry = max(historical_index, key=lambda x: x.get("fiscalYear", 0))
                most_recent_fy = str(most_recent_entry.get("fiscalYear", ""))
            
            aln_lookup[program_number] = {
                "programNumber": program_number,
                "title": item.get("title", ""),
                "agency": agency,
                "sub_agency": sub_agency,
                "objective": item.get("objective", ""),
                "most_recent_fy": most_recent_fy,
                "publishDate": item.get("publishDate"),
                "modifiedDate": item.get("modifiedDate"),
                "isActive": item.get("isActive", True),
                "_id": item.get("_id"),
                "organizationHierarchy": org_hierarchy
            }
    
    return aln_lookup


def find_new_alns_against_database(current_alns):
    """
    Find ALNs that are not present in the existing transformed_data.db database.
    
    Args:
        current_alns (dict): Current ALN data from SAM.gov
        
    Returns:
        list: ALNs that are new (not in the database)
    """
    if not TRANSFORMED_DB_PATH.exists():
        logger.warning(f"Database not found at {TRANSFORMED_DB_PATH}. Treating all ALNs as new.")
        return [
            {
                "programNumber": aln,
                "title": info["title"],
                "agency": info["agency"],
                "sub_agency": info["sub_agency"],
                "objective": info["objective"],
                "most_recent_fy": info["most_recent_fy"],
                "publishDate": info.get("publishDate"),
                "modifiedDate": info.get("modifiedDate")
            }
            for aln, info in current_alns.items()
        ]
    
    new_alns = []
    
    try:
        with sqlite3.connect(TRANSFORMED_DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Get all existing program IDs from the database
            cursor.execute("SELECT id FROM program")
            existing_alns = {row[0] for row in cursor.fetchall()}
            
            logger.info(f"Found {len(existing_alns)} existing ALNs in database")
            
            # Find ALNs in current data that are not in the database
            for aln, info in current_alns.items():
                if aln not in existing_alns:
                    new_alns.append({
                        "programNumber": aln,
                        "title": info["title"],
                        "agency": info["agency"],
                        "sub_agency": info["sub_agency"],
                        "objective": info["objective"],
                        "most_recent_fy": info["most_recent_fy"],
                        "publishDate": info.get("publishDate"),
                        "modifiedDate": info.get("modifiedDate")
                    })
                    logger.debug(f"New ALN not in database: {aln} - {info['title']}")
            
            logger.info(f"Found {len(new_alns)} ALNs that are not in the database")
            
    except sqlite3.Error as e:
        logger.error(f"Database error while checking for new ALNs: {e}")
        # Fall back to treating all as new if database error
        return [
            {
                "programNumber": aln,
                "title": info["title"],
                "agency": info["agency"],
                "sub_agency": info["sub_agency"],
                "objective": info["objective"],
                "most_recent_fy": info["most_recent_fy"],
                "publishDate": info.get("publishDate"),
                "modifiedDate": info.get("modifiedDate")
            }
            for aln, info in current_alns.items()
        ]
    
    return new_alns


def find_recently_modified_alns(current_alns):
    """
    Find ALNs that have been modified since June 2025
    
    Args:
        current_alns (dict): Current ALN data
        
    Returns:
        list: ALNs with modifiedDate since June 2025
    """
    recently_modified = []
    start_date = datetime(2025, 6, 1)

    days_since = (datetime.now() - start_date).days

    cutoff_date = datetime.now() - timedelta(days=days_since)
    
    for aln, info in current_alns.items():
        # Only check active ALNs for recent modifications
        if not info.get("isActive", True):
            continue
            
        modified_date_str = info.get("modifiedDate")
        if modified_date_str:
            try:
                # Parse SAM.gov date format (ISO 8601)
                modified_date = datetime.fromisoformat(modified_date_str.replace('Z', '+00:00'))
                # Convert to UTC for comparison
                modified_date = modified_date.replace(tzinfo=None)
                cutoff_date_utc = cutoff_date.replace(tzinfo=None)
                
                if modified_date >= cutoff_date_utc:
                    recently_modified.append({
                        "programNumber": aln,
                        "title": info["title"],
                        "agency": info["agency"],
                        "sub_agency": info["sub_agency"],
                        "objective": info["objective"],
                        "most_recent_fy": info["most_recent_fy"],
                        "modifiedDate": modified_date_str,
                        "daysAgo": (datetime.now() - modified_date).days
                    })
                    logger.debug(f"Recently modified: {aln} - {info['title']} ({modified_date_str})")
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse modifiedDate for {aln}: {modified_date_str} - {e}")
                continue
    
    logger.info(f"Found {len(recently_modified)} ALNs modified since June 2025")
    return recently_modified


def compare_aln_data(baseline_data, current_data):
    """
    Compare baseline and current ALN data to find changes.
    
    Args:
        baseline_data (dict or None): Previous week's data
        current_data (dict): Current week's data
        
    Returns:
        dict: Analysis results with new, updated, and inactive ALNs
    """
    current_alns = create_aln_lookup(current_data)
    
    if baseline_data is None:
        logger.info("No baseline data - analyzing against database for new ALNs (first run)")
        # On first run, check against database for truly new ALNs
        new_alns = find_new_alns_against_database(current_alns)
        updated_alns = find_recently_modified_alns(current_alns)
        
        # Remove any "new" ALNs that are also in the "updated" list to avoid duplicates
        new_aln_numbers = {aln['programNumber'] for aln in new_alns}
        updated_alns_filtered = [aln for aln in updated_alns if aln['programNumber'] not in new_aln_numbers]
        
        logger.info(f"First run: Found {len(new_alns)} truly new ALNs and {len(updated_alns_filtered)} updated ALNs.")
        return {
            "new_alns": new_alns,
            "updated_alns": updated_alns_filtered,
            "inactive_alns": [],
            "total_current": len(current_alns),
            "total_baseline": 0,
            "is_first_run": True
        }
    
    baseline_alns = create_aln_lookup(baseline_data)
    
    new_alns = []
    updated_alns = []
    inactive_alns = []
    
    # Find new ALNs (in current but not in baseline)
    for aln, current_info in current_alns.items():
        if aln not in baseline_alns:
            new_alns.append({
                "programNumber": aln,
                "title": current_info["title"],
                "agency": current_info["agency"],
                "sub_agency": current_info["sub_agency"],
                "objective": current_info["objective"],
                "most_recent_fy": current_info["most_recent_fy"],
                "publishDate": current_info["publishDate"]
            })
    
    # Find updated ALNs (modifiedDate changed)
    for aln, current_info in current_alns.items():
        if aln in baseline_alns:
            baseline_modified = baseline_alns[aln].get("modifiedDate")
            current_modified = current_info.get("modifiedDate")
            
            if baseline_modified != current_modified:
                updated_alns.append({
                    "programNumber": aln,
                    "title": current_info["title"],
                    "agency": current_info["agency"],
                    "sub_agency": current_info["sub_agency"],
                    "objective": current_info["objective"],
                    "most_recent_fy": current_info["most_recent_fy"],
                    "previousModifiedDate": baseline_modified,
                    "currentModifiedDate": current_modified
                })
    
    # Find inactive ALNs (in baseline but not active in current)
    for aln, baseline_info in baseline_alns.items():
        if aln not in current_alns:
            inactive_alns.append({
                "programNumber": aln,
                "title": baseline_info["title"],
                "agency": baseline_info.get("agency", ""),
                "sub_agency": baseline_info.get("sub_agency", ""),
                "objective": baseline_info.get("objective", ""),
                "most_recent_fy": baseline_info.get("most_recent_fy", ""),
                "lastModifiedDate": baseline_info.get("modifiedDate")
            })
    
    logger.info(f"Analysis complete: {len(new_alns)} new, {len(updated_alns)} updated, {len(inactive_alns)} inactive")
    
    return {
        "new_alns": new_alns,
        "updated_alns": updated_alns,
        "inactive_alns": inactive_alns,
        "total_current": len(current_alns),
        "total_baseline": len(baseline_alns),
        "is_first_run": False
    }


def save_baseline_snapshot(current_data):
    """
    Save current data as baseline for next week's comparison.
    
    Args:
        current_data (dict): Current ALN data to save
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")
    baseline_file = BASELINE_DIR / f"{timestamp}_aln_snapshot.json"
    
    try:
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Baseline snapshot saved: {baseline_file.name}")
        
        # Clean up old baseline files (keep last 4 weeks)
        baseline_files = sorted(BASELINE_DIR.glob("*_aln_snapshot.json"))
        if len(baseline_files) > 4:
            for old_file in baseline_files[:-4]:
                old_file.unlink()
                logger.info(f"Removed old baseline: {old_file.name}")
                
    except IOError as e:
        logger.error(f"Error saving baseline snapshot: {e}")


def generate_reports(analysis_results):
    """
    Generate human-readable reports from analysis results.
    
    Args:
        analysis_results (dict): Results from compare_aln_data()
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    # Generate simple text files with ALN lists and detailed information
    if analysis_results["new_alns"]:
        new_alns_file = REPORTS_DIR / f"{timestamp}_new_alns.txt"
        with open(new_alns_file, 'w', encoding='utf-8') as f:
            f.write("# New Assistance Listing Numbers\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write("# Format: ALN | Title | Agency | Sub-agency | Description | Most Recent FY\n\n")
            
            for aln in analysis_results["new_alns"]:
                # Use full objective text but clean up newlines
                objective = aln.get('objective', '').replace('\n', ' ').replace('\r', ' ').strip()
                
                # Format the line with pipe separators for easy parsing
                line = f"{aln['programNumber']} | {aln.get('title', '')} | {aln.get('agency', '')} | {aln.get('sub_agency', '')} | {objective} | {aln.get('most_recent_fy', '')}\n"
                f.write(line)
        logger.info(f"New ALNs report saved: {new_alns_file.name}")
    
    if analysis_results["updated_alns"]:
        updated_alns_file = REPORTS_DIR / f"{timestamp}_updated_alns.txt"
        with open(updated_alns_file, 'w', encoding='utf-8') as f:
            f.write("# Updated Assistance Listing Numbers\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write("# Format: ALN | Title | Agency | Sub-agency | Description | Most Recent FY\n\n")
            
            for aln in analysis_results["updated_alns"]:
                # Use full objective text but clean up newlines
                objective = aln.get('objective', '').replace('\n', ' ').replace('\r', ' ').strip()
                
                # Format the line with pipe separators for easy parsing
                line = f"{aln['programNumber']} | {aln.get('title', '')} | {aln.get('agency', '')} | {aln.get('sub_agency', '')} | {objective} | {aln.get('most_recent_fy', '')}\n"
                f.write(line)
        logger.info(f"Updated ALNs report saved: {updated_alns_file.name}")
    
    # Generate detailed JSON report
    detailed_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "new_count": len(analysis_results["new_alns"]),
            "updated_count": len(analysis_results["updated_alns"]),
            "inactive_count": len(analysis_results["inactive_alns"]),
            "total_current": analysis_results["total_current"],
            "total_baseline": analysis_results["total_baseline"],
            "is_first_run": analysis_results["is_first_run"]
        },
        "details": analysis_results
    }
    
    detailed_file = REPORTS_DIR / f"{timestamp}_detailed_report.json"
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Detailed report saved: {detailed_file.name}")


def main():
    """
    Main execution function for weekly ALN change detection.
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Weekly ALN Change Detection - Starting")
    logger.info("=" * 60)
    
    try:
        # Step 1: Fetch current ALN data
        current_data = fetch_current_alns()
        
        # Step 2: Load baseline for comparison
        baseline_data = load_baseline_snapshot()
        
        # Step 3: Compare data and identify changes
        analysis_results = compare_aln_data(baseline_data, current_data)
        
        # Step 4: Generate reports
        generate_reports(analysis_results)
        
        # Step 5: Save current data as new baseline
        save_baseline_snapshot(current_data)
        
        # Summary
        elapsed_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info("Weekly ALN Change Detection - Complete")
        logger.info(f"Execution time: {elapsed_time:.2f} seconds")
        if analysis_results.get('is_first_run'):
            logger.info(f"Updated ALNs (recently modified): {len(analysis_results['updated_alns'])}")
        else:
            logger.info(f"New ALNs found: {len(analysis_results['new_alns'])}")
            logger.info(f"Updated ALNs found: {len(analysis_results['updated_alns'])}")
        logger.info(f"Inactive ALNs found: {len(analysis_results['inactive_alns'])}")
        logger.info("=" * 60)
        
        # Exit with status code indicating if changes were found
        if analysis_results["new_alns"] or analysis_results["updated_alns"]:
            sys.exit(1)  # Changes found
        else:
            sys.exit(0)  # No changes
            
    except Exception as e:
        logger.error(f"Script failed with error: {e}", exc_info=True)
        sys.exit(2)  # Error occurred


if __name__ == "__main__":
    main()