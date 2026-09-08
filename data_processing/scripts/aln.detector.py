#!/usr/bin/env python3
"""
Assistance Listing Number (ALN) Detection Script

This script pulls all ALNs currently in SAM.gov, and it saves to a csv in the
reports directory called [date]_all_alns.csv.
"""

from datetime import datetime
from pathlib import Path
import requests
import time

SCRIPT_DIR = Path(__file__).parent
REPORTS_DIR = SCRIPT_DIR / "reports"
SAM_SEARCH_URL = "https://sam.gov/api/prod/sgs/v1/search/?index=cfda&page=0&mode=search&size=10000&is_active=true"
SAM_DETAILS_URL_PREFIX = "https://sam.gov/api/prod/fac/v1/programs/"

def fix_string_for_csv(field):
    return str(field).replace('"','""""').replace('\r', '').replace('\n', '')

def get_detailed_data(sam_id, aln_index):
    print(f"    Fetching data for index {aln_index}, id {sam_id}...")
    while True:
        try:
            response = requests.get(SAM_DETAILS_URL_PREFIX + sam_id, timeout=60)
            response.raise_for_status()
            detailed_aln_data = response.json()['data']
            print(f"    Successfully fetched data")
            time.sleep(0.5)
            return detailed_aln_data
        except Exception as e:
            print(f"    Exception occurred: {e}")
            print(f"    Waiting 60 seconds before retrying...")
            time.sleep(60)

print("Fetching current ALN data from SAM.gov...")
response = requests.get(SAM_SEARCH_URL, timeout=60)
response.raise_for_status()
alns = response.json()['_embedded']['results']
print(f"Successfully fetched {len(alns)} ALNs from SAM.gov")

output = ['al_#,Title,Agency,Sub-agency,AL Description,Last modified date,Published date,Most recent year in the historical index,Program types']
aln_index = 0
for aln in alns:
    sam_id = aln['_id']
    agency = 'N/A'
    subagency = 'N/A'
    if 'organizationHierarchy' in aln:
        agency = aln['organizationHierarchy'][0]['name']
        if len(aln['organizationHierarchy']) > 1:
            subagency = aln['organizationHierarchy'][1]['name']

    assistance_types_list = []
    if 'assistanceTypes' in aln:
        for hierarchy in aln['assistanceTypes']:
            if hierarchy is not None and 'hierarchy' in hierarchy and hierarchy['hierarchy'] is not None:
                for assistance_type in hierarchy['hierarchy']:
                    if assistance_type is not None and 'level' in assistance_type and 'value' in assistance_type and assistance_type['level'] == 1:
                        # the parent type can appear in multiple hierarchies
                        if assistance_type['value'] not in assistance_types_list:
                            assistance_types_list.append(assistance_type['value'])

    latestHistoricalIndex = 'N/A'
    if 'historicalIndex' in aln and aln['historicalIndex'] is not None:
        latestHistoricalIndex = max(aln['historicalIndex'], key=lambda item: item['fiscalYear'])['fiscalYear']

    # the first API truncates some fields
    detailed_aln_data = get_detailed_data(sam_id, aln_index)

    description = fix_string_for_csv(detailed_aln_data['objective'])
    programNumber = fix_string_for_csv(aln['programNumber'])
    title = fix_string_for_csv(detailed_aln_data['title'])
    assistance_types = fix_string_for_csv("|".join(assistance_types_list))

    output.append(f'"{programNumber}","{title}","{agency}","{subagency}","{description}","{aln['modifiedDate']}","{aln['publishDate']}","{latestHistoricalIndex}","{assistance_types}"')
    aln_index += 1

now = datetime.now()
output_path = REPORTS_DIR / f"{now.strftime("%Y-%m-%d")}_all_alns.csv"
with open(output_path, 'w') as file:
    file.write('\n'.join(output))

print(f"File successfully saved to {output_path}")