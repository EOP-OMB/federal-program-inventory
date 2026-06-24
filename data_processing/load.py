"""Creates markdown files for static site generation."""

from datetime import datetime
from pathlib import Path
import sqlite3
import os
import shutil
import json
import yaml
import csv
import constants
import yaml as yml
from pathlib import Path
from typing import List, Dict, Any

# Constants
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE_PATH = os.path.join("transformed", "transformed_data.db")
MARKDOWN_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "website", "_program")
full_path = os.path.join(CURRENT_DIR, DB_FILE_PATH)
FISCAL_YEARS = [
    '2015',
    '2016',
    '2017',
    '2018',
    '2019',
    '2020',
    '2021',
    '2022',
    '2023',
    '2024',
    '2025',
    '2026'
]
WEBSITE_DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "website", "_data")
INFLATION_POPULATION_FILE_PATH = os.path.join(CURRENT_DIR, "extracted", "inflation_and_population_growth.csv")
GLOBAL_DATA_YML_PATH = os.path.join(WEBSITE_DATA_DIR, "global_data.yml")
DATA_SOURCES_YML_PATH = os.path.join(WEBSITE_DATA_DIR, "data_sources.yml")

def calculate_improper_payment_metrics(improper_payments_array):
    """
    Calculate improper payment metrics for display.
    
    Returns dict with raw numeric values
    - is_multiple: contains multiple timeframes for the payment accuracy fiscal year
    - current_year_details: improper payment details for the payment accuracy fiscal year
    - improper_payments_total: raw dollar amount
    - improper_payments_percent: percentage as number (e.g., 10.6)
    - sparkline: series for ip rate line chart
    """
    rate_by_year = {}
    current_year_timeframes_seen = set()
    current_year_details = []
    all_programs = {}
    for ip_row in improper_payments_array:
        all_programs[ip_row['name']] = {
            'agency': ip_row['agency'],
            'slug': ip_row['slug']
        }

    improper_payments_array_cy = [
        ip_row for ip_row in improper_payments_array
        if str(ip_row['fiscal_year']) == constants.PAYMENTACCURACY_FY_DATE
    ]
    improper_payments_array_cy_lookup = {ip_row['name']: ip_row for ip_row in improper_payments_array_cy}

    for program_name in all_programs:
        program = all_programs[program_name]
        if program_name in improper_payments_array_cy_lookup:
            ip_row = improper_payments_array_cy_lookup[program_name]
            current_year_details.append(ip_row)
            if 'outlays' in ip_row and ip_row['outlays'] is not None and ip_row['outlays'] != 0:
                current_year_timeframes_seen.add(ip_row['start_date'] + '-' + ip_row['end_date'])
        else:
            current_year_details.append({
                'name': program_name,
                'outlays': None,
                'improper_payments': None,
                'insufficient_payment': None,
                'start_date': None,
                'end_date': None,
                'fiscal_year': constants.PAYMENTACCURACY_FY_DATE,
                'agency': program['agency'],
                'slug': program['slug']
            })

    for ip_row in improper_payments_array:
        ip = ip_row.get('improper_payments', 0.0)
        outlays = ip_row.get('outlays', 0.0)
        fiscal_year = str(ip_row['fiscal_year'])

        if fiscal_year not in rate_by_year:
            rate_by_year[fiscal_year] = {
                'total_improper_payments': ip,
                'total_outlays': outlays,
                'improper_payments_percent': ((ip / outlays) * 100) if outlays > 0 else 0.0,
                'fiscal_year': fiscal_year
            }
        else:
            rate_by_year[fiscal_year]['total_improper_payments'] += ip
            rate_by_year[fiscal_year]['total_outlays'] += outlays
            if rate_by_year[fiscal_year]['total_outlays'] > 0:
                rate_by_year[fiscal_year]['improper_payments_percent'] = 100 * rate_by_year[fiscal_year]['total_improper_payments'] / rate_by_year[fiscal_year]['total_outlays']
            else:
                rate_by_year[fiscal_year]['improper_payments_percent'] = 0.0

    return {
        # if more than one timeframe was seen, this will convolute the aggregate ip rate
        'is_multiple': len(current_year_timeframes_seen) > 1,
        'improper_payments_total': round(rate_by_year[constants.PAYMENTACCURACY_FY_DATE]['total_improper_payments'] if constants.PAYMENTACCURACY_FY_DATE in rate_by_year else 0, 2),
        'improper_payments_percent': round(rate_by_year[constants.PAYMENTACCURACY_FY_DATE]['improper_payments_percent'] if constants.PAYMENTACCURACY_FY_DATE in rate_by_year else 0, 1),
        'current_year_details': current_year_details,
        'sparkline': list(map(lambda x: {
            'x': x['fiscal_year'],
            'rate': x['improper_payments_percent']
        }, rate_by_year.values()))
    }

def recreate_directory(directory_path):
    if os.path.isdir(directory_path):
        shutil.rmtree(directory_path)
    os.makedirs(directory_path)

obligations_data = {}
def get_assistance_program_obligations(cursor, program_id, fiscal_years):
    """Get obligations data for specified fiscal years.
    These fields are used on all-program-data.csv.  usa_spending_actual
    groups by transaction date; whereas, obligations on other parts of the 
    site group by initial award date."""
    global obligations_data
    if not obligations_data:
        print('Caching obligations...')
        cursor.execute("""
            SELECT
                id,
                fiscal_year,
                ROUND(COALESCE(sam_estimated_obligation, 0), 2) AS sam_estimate,
                ROUND(COALESCE(sam_actual_obligation, 0), 2) AS sam_actual,
                ROUND(COALESCE(usaspending_obligation_by_action_date, 0), 2) AS usa_spending_actual
            FROM program_amounts_lookup
        """)
        for row in cursor.fetchall():
            if row['id'] not in obligations_data:
                obligations_data[row['id']] = {}
            obligations_data[row['id']][row['fiscal_year']] = {
                'x': row['fiscal_year'],
                'sam_estimate': float(row['sam_estimate']),
                'sam_actual': float(row['sam_actual']),
                'usa_spending_actual': float(row['usa_spending_actual'])
            }
        print('Obligations cached.')

    obligations = []
    for year in fiscal_years:
        obligations.append(obligations_data[program_id][year])

    return obligations

def get_other_program_amounts(cursor, program_id, fiscal_years):
    """Get obligations data for other programs."""
    return list(map(
        lambda amount: {
            'x': amount['x'],
            'outlays': amount['outlay'],
            'forgone_revenue': amount['forgone_revenue']
        },
        get_amounts(cursor, program_id, fiscal_years)
    ))

outlays_data = {}
def get_amounts(cursor, program_id, fiscal_years):
    """Get outlays data for specified fiscal years."""
    global outlays_data
    if not outlays_data:
        print('Caching amounts...')
        cursor.execute("""
            SELECT
                id,
                fiscal_year,
                ROUND(COALESCE(outlay, 0), 2) AS outlay,
                ROUND(COALESCE(obligation, 0), 2) AS obligation,
                ROUND(COALESCE(expenditure, 0), 2) AS expenditure,
                ROUND(COALESCE(forgone_revenue, 0), 2) AS forgone_revenue
            FROM program_amounts_lookup
        """)
        for row in cursor.fetchall():
            if row['id'] not in outlays_data:
                outlays_data[row['id']] = {}
            outlays_data[row['id']][row['fiscal_year']] = {
                'x': row['fiscal_year'],
                'outlay': float(row['outlay']),
                'obligation': float(row['obligation']),
                'expenditure': float(row['expenditure']),
                'forgone_revenue': float(row['forgone_revenue'])
            }
        print('Amounts cached.')

    outlays = []
    for year in fiscal_years:
        outlays.append(outlays_data[program_id][year])

    return outlays

def get_assistance_listing_expenditures(cursor, program_ids, fiscal_year):
    """Get total and per-program obligations for assistance listing programs."""
    if not program_ids:
        return {}, 0.0
    
    program_obligations = {}
    total_obligations = 0.0

    for program_id in program_ids:
        outlays = get_amounts(cursor, program_id, [fiscal_year])
        if len(outlays) > 0:
            # Use expenditure, because we may need to compare different program types
            amount = float(outlays[0]['expenditure'])
            program_obligations[program_id] = amount
            total_obligations += amount
    
    return program_obligations, total_obligations

def get_program_expenditures_by_type(cursor, program_ids, fiscal_year):
    """Get obligations grouped by program type."""
    if not program_ids:
        return {}
        
    # Get all programs and their types
    placeholders = ','.join('?' * len(program_ids))
    cursor.execute(f"""
        SELECT id, COALESCE(program_type, 'assistance_listing') as program_type
        FROM program 
        WHERE id IN ({placeholders})
    """, program_ids)
    
    # Group programs by type
    programs_by_type = {}
    for row in cursor.fetchall():
        prog_type = row['program_type']
        if prog_type not in programs_by_type:
            programs_by_type[prog_type] = []
        programs_by_type[prog_type].append(row['id'])
    
    # Calculate obligations for each type
    results = {}
    for prog_type, type_program_ids in programs_by_type.items():
        _, total = get_assistance_listing_expenditures(cursor, type_program_ids, fiscal_year)
        results[prog_type] = total
    
    return results

def generate_agency_list(cursor: sqlite3.Cursor, program_ids: List[str], fiscal_year: str) -> List[Dict[str, Any]]:
    """
    Generate list of agencies with program counts and obligations for a set of
    programs. Includes both SAM spending and other program obligations.
    """
    if not program_ids:
        return []

    # First get programs by agency with their types
    placeholders = ','.join('?' * len(program_ids))
    cursor.execute(f"""
        SELECT
            a1.agency_name as title,
            p.id as program_id,
            p.program_type
        FROM program p
        LEFT JOIN agency a ON p.agency_id = a.id
        LEFT JOIN agency a1 ON a.tier_1_agency_id = a1.id
        WHERE p.id IN ({placeholders})
    """, program_ids)

    # Group programs by agency and type
    agency_programs = {}
    for row in cursor.fetchall():
        agency_name = row['title'] or 'Unspecified'
        if agency_name not in agency_programs:
            agency_programs[agency_name] = {
                'assistance_program': [],
                'other_program': []
            }

        if row['program_type'] == 'assistance_listing':
            agency_programs[agency_name]['assistance_program'].append(row['program_id'])
        else:
            agency_programs[agency_name]['other_program'].append(row['program_id'])

    # Calculate obligations for each agency
    agencies = []
    for agency_name, programs in agency_programs.items():
        total_obs = 0
        total_programs = len(programs['assistance_program']) + len(programs['other_program'])

        _, agency_total_obs = get_assistance_listing_expenditures(
            cursor,
            programs['assistance_program'] + programs['other_program'],
            fiscal_year
        )
        total_obs += agency_total_obs

        agencies.append({
            'title': agency_name,
            'total_num_programs': total_programs,
            'total_obs': total_obs
        })

    # Sort by total obligations descending
    return sorted(agencies, key=lambda x: (x['total_obs'], x['title']), reverse=True)


def generate_applicant_type_list(cursor: sqlite3.Cursor, program_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Generate list of applicant types with program counts for a set of programs.
    """
    if not program_ids:
        return []

    cursor.execute("""
        SELECT
            c.name as title,
            COUNT(DISTINCT ptc.program_id) as total_num_programs
        FROM category c
        JOIN program_to_category ptc ON c.id = ptc.category_id
        WHERE c.type = 'applicant'
        AND c.type = ptc.category_type
        AND ptc.program_id IN ({})
        GROUP BY c.name
        HAVING
            c.name IS NOT NULL
            AND total_num_programs > 0
        ORDER BY total_num_programs DESC, title
    """.format(','.join('?' * len(program_ids))), program_ids)

    applicant_types = []
    for row in cursor.fetchall():
        applicant_types.append({
            'title': row['title'],
            'total_num_programs': row['total_num_programs']
        })

    return applicant_types


def convert_to_url_string(s: str) -> str:
    """Convert a string to URL-friendly format."""
    return str(''.join(c if c.isalnum() else '-' for c in s.lower()))


def clean_string(s: str) -> str:
    """Clean a string by removing newlines and excessive whitespace."""
    return s.replace('\n', '').replace('\r', '').strip()


def get_categories_hierarchy(cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    """
    Generate a nested structure of categories and subcategories with explicit object construction.
    """
    # Fetch parent categories with their subcategories
    cursor.execute("""
        SELECT DISTINCT
            taxonomy_category.id as parent_id,
            taxonomy_category.category as parent_name,
            taxonomy_focus_area.focus_area as sub_name
        FROM taxonomy_category
        JOIN program_taxonomy_lookup ON
            taxonomy_category.id = program_taxonomy_lookup.taxonomy_category_id
        LEFT JOIN taxonomy_focus_area ON
            taxonomy_category.id = taxonomy_focus_area.category_id
        ORDER BY taxonomy_category.category, taxonomy_focus_area.focus_area
    """)

    categories = []
    current_parent = None
    current_category_obj = None

    for row in cursor.fetchall():
        parent_name = clean_string(row['parent_name'])

        if current_parent != parent_name:
            if current_category_obj is not None:
                categories.append(current_category_obj)

            current_parent = parent_name
            current_category_obj = {
                'title': parent_name,
                'permalink': f"/category/{convert_to_url_string(parent_name)}",
                'subcategories': []
            }

        if row['sub_name']:
            sub_name = clean_string(row['sub_name'])
            current_category_obj['subcategories'].append({
                'title': sub_name,
                'permalink': f"{current_category_obj['permalink']}/{convert_to_url_string(sub_name)}"
            })

    if current_category_obj is not None:
        categories.append(current_category_obj)

    return categories

def get_improper_payment_info(cursor: sqlite3.Cursor, program_id: str) -> List[Dict[str, Any]]:
    """Get improper payment data for a program including related programs."""
    # Get all improper payment records this program is associated with
    initial_year = int(constants.CURRENT_FISCAL_YEAR) - constants.SPENDING_CHART_YEAR_RANGE
    cursor.execute("""
        SELECT 
            improper_payment_program_name,
            agency,
            outlays,
            improper_payment_amount as improper_payments,
            fiscal_year,
            start_date,
            end_date,
            insufficient_documentation_amount as insufficient_payment,
            slug
        FROM improper_payment_mapping
        WHERE program_id = ? AND fiscal_year >= ?
        ORDER BY improper_payment_program_name, fiscal_year
    """, (program_id, initial_year))
    
    improper_payments = []
    
    for payment_row in cursor.fetchall():
        improper_name = payment_row['improper_payment_program_name']
        
        input_date_format = "%Y-%m-%d"
        output_date_format = "%m-%Y"
        improper_payments.append({
            'name': improper_name,
            'outlays': float(payment_row['outlays']) if payment_row['outlays'] else 0.0,
            'improper_payments': float(payment_row['improper_payments']) if payment_row['improper_payments'] else 0.0,
            'insufficient_payment': float(payment_row['insufficient_payment']) if payment_row['insufficient_payment'] else 0.0,
            'start_date': datetime.strptime(payment_row['start_date'], input_date_format)
                .strftime(output_date_format) if payment_row['start_date'] is not None else '',
            'end_date': datetime.strptime(payment_row['end_date'], input_date_format)
                .strftime(output_date_format) if payment_row['end_date'] is not None else '',
            'fiscal_year': payment_row['fiscal_year'],
            'agency': payment_row['agency'],
            'slug': payment_row['slug']
        })
    
    return improper_payments

def get_related_programs(cursor, improper_payment_data, program_id):
    """Get related programs in the current fiscal year."""
    related_programs = {}
    program_names = set()

    # get unique list of program names
    for ip_row in improper_payment_data:
        program_names.add(ip_row['name'])

    for program_name in program_names:
        cursor.execute("""
                SELECT DISTINCT
                    p.id,
                    p.name
                FROM improper_payment_mapping ip
                JOIN program p ON ip.program_id = p.id
                WHERE ip.improper_payment_program_name = ?
                AND p.id != ?
            """, (program_name, program_id))
        for mapping_row in cursor.fetchall():
            if mapping_row['id'] not in related_programs:
                related_programs[mapping_row['id']] = {
                    'id': mapping_row['id'],
                    'name': mapping_row['name'],
                    'permalink': f"/program/{mapping_row['id']}"
                }

    return sorted(list(related_programs.values()), key=lambda p: p['id'])

def generate_category_markdown_files(cursor: sqlite3.Cursor, output_dir: str, fiscal_year: str):
    """Generate markdown files for categories with obligations from both regular and other programs."""
    recreate_directory(output_dir)

    # Get all parent categories with at least one program
    cursor.execute("""
        SELECT DISTINCT
            taxonomy_category.category AS title,
            taxonomy_category.id
        FROM taxonomy_category
        JOIN program_taxonomy_lookup ON taxonomy_category.id = program_taxonomy_lookup.taxonomy_category_id
    """)

    parent_categories = cursor.fetchall()
    for parent in parent_categories:
        # Get unique program IDs in this category
        cursor.execute("""
            SELECT program.id, program.program_type
            FROM program
            JOIN program_taxonomy_lookup
                ON program_taxonomy_lookup.program_id = program.id
            WHERE program_taxonomy_lookup.taxonomy_category_id = ?
        """, (parent['id'],))

        programs = cursor.fetchall()
        if not programs:
            continue

        program_ids = [p['id'] for p in programs]

        # Calculate total category obligations
        total_category_obs = 0

        # Get obligations for regular programs
        if program_ids:
            _, total_obs = get_assistance_listing_expenditures(cursor, program_ids, fiscal_year)
            total_category_obs += total_obs

        # Get subcategories with their stats
        cursor.execute("""
            SELECT DISTINCT
                taxonomy_focus_area.focus_area AS title,
                taxonomy_focus_area.id AS category_id
            FROM taxonomy_focus_area
            JOIN program_taxonomy_lookup
                ON taxonomy_focus_area.id = program_taxonomy_lookup.taxonomy_focus_area_id
            WHERE taxonomy_focus_area.category_id = ?
        """, (parent['id'],))

        subcats = []
        for subcat in cursor.fetchall():
            # Get programs for this subcategory
            cursor.execute("""
                SELECT
                    program.id, program.program_type FROM program
                JOIN program_taxonomy_lookup
                    ON program.id = program_taxonomy_lookup.program_id
                WHERE program_taxonomy_lookup.taxonomy_focus_area_id = ?
            """, (subcat['category_id'],))

            subcat_programs = cursor.fetchall()

            sub_program_ids = [p['id'] for p in subcat_programs]

            # Calculate total obligations for subcategory
            subcat_total_obs = 0
            program_count = len(subcat_programs)

            if sub_program_ids:
                _, total_obs = get_assistance_listing_expenditures(cursor, sub_program_ids, fiscal_year)
                subcat_total_obs += total_obs

            subcats.append({
                'title': subcat['title'],
                'program_count': program_count,
                'total_obligations': subcat_total_obs
            })

        # Calculate category totals including both types of programs
        cursor.execute("""
            SELECT
                COUNT(DISTINCT ptl.program_id) as total_num_programs,
                COUNT(DISTINCT a1.agency_name) as total_num_agencies,
                COUNT(DISTINCT c_app.name) as total_num_applicant_types
            FROM program_taxonomy_lookup ptl
            JOIN program p ON ptl.program_id = p.id
            LEFT JOIN agency a ON p.agency_id = a.id
            LEFT JOIN agency a1 ON a.tier_1_agency_id = a1.id
            LEFT JOIN program_to_category ptc_app
                ON p.id = ptc_app.program_id AND
                ptc_app.category_type = 'applicant'
            LEFT JOIN category c_app ON ptc_app.category_id = c_app.id
            WHERE ptl.taxonomy_category_id = ?
        """, (parent['id'],))

        totals = cursor.fetchone()

        category_title = clean_string(parent['title'])

        subcats.sort(key=lambda x: x['title'])
        # Create category data
        category_data = {
            'title': category_title,
            'permalink': f"/category/{convert_to_url_string(category_title)}",
            'fiscal_year': fiscal_year,
            'total_num_programs': totals['total_num_programs'],
            'total_num_sub_cats': len(subcats),
            'total_num_agencies': totals['total_num_agencies'],
            'total_num_applicant_types': totals['total_num_applicant_types'],
            'total_obs': total_category_obs,
            'sub_cats': json.dumps([{
                'title': sub['title'],
                'permalink': f"/category/{convert_to_url_string(category_title)}/{convert_to_url_string(sub['title'])}",
                'total_num_programs': sub['program_count'],
                'total_obs': float(sub['total_obligations'])
            } for sub in subcats], separators=(',', ':')),
            'agencies': json.dumps(generate_agency_list(cursor, [p['id'] for p in programs], fiscal_year), separators=(',', ':')),
            'applicant_types': json.dumps(generate_applicant_type_list(cursor, [p['id'] for p in programs]), separators=(',', ':')),
            'categories_subcategories': get_categories_hierarchy(cursor)
        }

        # Write category markdown file
        file_path = os.path.join(output_dir, f"{convert_to_url_string(category_title)}.md")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('---\n')
            yaml.dump(category_data, file, allow_unicode=True)
            file.write('---\n')

    print("Successfully generated category markdown files")


def generate_subcategory_markdown_files(cursor: sqlite3.Cursor, output_dir: str, fiscal_year: str):
    """Generate markdown files for subcategories with obligations from both regular and other programs."""
    recreate_directory(output_dir)

    # Get all subcategories that have at least one program
    cursor.execute("""
        SELECT
            ptl.taxonomy_focus_area_id AS id,
            f.focus_area AS title,
            ptl.taxonomy_category_id AS parent_id,
            c.category AS parent_title
        FROM program_taxonomy_lookup ptl
        JOIN taxonomy_category c ON ptl.taxonomy_category_id = c.id
        JOIN taxonomy_focus_area f ON ptl.taxonomy_focus_area_id = f.id
    """)

    subcategories = cursor.fetchall()
    for subcat in subcategories:
        # Get all programs with their types and spending data
        cursor.execute("""
            SELECT DISTINCT
                p.id,
                p.name AS title,
                p.program_type,
                p.popular_name,
                a1.agency_name as agency_name
            FROM program p
            JOIN program_taxonomy_lookup ptl ON p.id = ptl.program_id
            LEFT JOIN agency a ON p.agency_id = a.id
            LEFT JOIN agency a1 ON a.tier_1_agency_id = a1.id
            WHERE ptl.taxonomy_focus_area_id = ?
        """, (subcat['id'],))

        programs = cursor.fetchall()
        if not programs:
            continue

        program_ids = [p['id'] for p in programs]

        # Initialize total obligations
        total_subcategory_obs = 0.0
        program_obligations = {}

        program_obligations = {}
        if program_ids:
            program_obs, total_obs = get_assistance_listing_expenditures(
                cursor, program_ids, fiscal_year)
            program_obligations.update(program_obs)
            total_subcategory_obs += total_obs

        cursor.execute("""
            SELECT
                COUNT(DISTINCT ptl.program_id) as total_num_programs,
                COUNT(DISTINCT a1.agency_name) as total_num_agencies,
                COUNT(DISTINCT c_app.name) as total_num_applicant_types
            FROM program_taxonomy_lookup ptl
            JOIN program p ON ptl.program_id = p.id
            LEFT JOIN agency a ON p.agency_id = a.id
            LEFT JOIN agency a1 ON a.tier_1_agency_id = a1.id
            LEFT JOIN program_to_category ptc_app
                ON p.id = ptc_app.program_id AND
                ptc_app.category_type = 'applicant'
            LEFT JOIN category c_app ON ptc_app.category_id = c_app.id
            WHERE ptl.taxonomy_focus_area_id = ?
        """, (subcat['id'],))

        totals = cursor.fetchone()

        # Create subcategory data
        parent_title = subcat['parent_title']
        subcategory_title = subcat['title']

        subcategory_data = {
            'title': subcategory_title,
            'permalink': f"/category/{convert_to_url_string(parent_title)}/{convert_to_url_string(subcategory_title)}",
            'parent_title': parent_title,
            'parent_permalink': f"/category/{convert_to_url_string(parent_title)}",
            'fiscal_year': fiscal_year,
            'total_num_programs': totals['total_num_programs'],
            'total_num_agencies': totals['total_num_agencies'],
            'total_num_applicant_types': totals['total_num_applicant_types'],
            'total_obs': total_subcategory_obs,
            'agencies': json.dumps(generate_agency_list(cursor, program_ids, fiscal_year), separators=(',', ':')),
            'applicant_types': json.dumps(generate_applicant_type_list(cursor, program_ids), separators=(',', ':')),
            'categories_subcategories': get_categories_hierarchy(cursor),
            'programs': json.dumps(sorted([{
                'cfda': p['id'],
                'permalink': f"/program/{p['id']}",
                'title': p['title'],
                'popular_name': p['popular_name'],
                'agency': p['agency_name'] or 'Unspecified',
                'total_obs': program_obligations.get(p['id'], 0.0),
                'program_type': p['program_type']
            } for p in programs], key=lambda x: (-x['total_obs'], x['title'])), separators=(',', ':'))
        }

        # Write subcategory markdown file
        file_path = os.path.join(output_dir,
            f"{convert_to_url_string(parent_title)}---{convert_to_url_string(subcategory_title)}.md")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('---\n')
            yaml.dump(subcategory_data, file, allow_unicode=True)
            file.write('---\n')

    print("Successfully generated sub-category markdown files")

def generate_gwo_markdown_files(cursor: sqlite3.Cursor, output_dir: str):
    """Generate markdown files for gwos with related programs."""
    recreate_directory(output_dir)

    cursor.execute("""
        SELECT DISTINCT
            gwo.id,
            taxonomy_focus_area.focus_area,
            taxonomy_category.category,
            gwo.gwo,
            gwo.gwo_definition
        FROM gwo
        JOIN program_to_gwo ON gwo.id = program_to_gwo.gwo_id
        JOIN taxonomy_focus_area ON gwo.focus_area_id = taxonomy_focus_area.id
        JOIN taxonomy_category ON taxonomy_focus_area.category_id = taxonomy_category.id
    """)

    gwos = cursor.fetchall()

    for gwo in gwos:
        cursor.execute("""
            SELECT 
                p.id, 
                p.name,
                a1.agency_name,
                p.program_type
            FROM program p
            JOIN program_to_gwo ON p.id = program_to_gwo.program_id
            LEFT JOIN agency a ON p.agency_id = a.id
            LEFT JOIN agency a1 ON a.tier_1_agency_id = a1.id
            WHERE gwo_id = ?
            ORDER BY name
        """, (gwo["id"],))

        where_used = cursor.fetchall()

        url_friendly_id = gwo['id'].replace('#','_').replace('.','_')

        # Enhance where_used with agency and expenditure data
        where_used_enhanced = []
        for p in where_used:
            program_data = {
                'permalink': f"/program/{p['id']}",
                'name': p['name'],
                'agency': p['agency_name'] or 'Unspecified',
                'program_type': p['program_type']
            }

            # Use expenditure, because we may need to compare different program types
            expenditure_amount = 0.0
            spending = get_amounts(cursor, p['id'], FISCAL_YEARS)
            if spending:
                expenditure_amount = next((o.get('expenditure', 0.0) for o in spending if o.get('x') == constants.CURRENT_FISCAL_YEAR), 0.0)

            program_data['expenditure_amount'] = expenditure_amount
            where_used_enhanced.append(program_data)

        gwo_data = {
            'permalink': f"/gwo/{url_friendly_id}",
            'title': gwo['gwo'],
            'gwo_id': gwo["id"],
            'focus_area': gwo["focus_area"],
            'category': gwo['category'],
            'definition': gwo['gwo_definition'],
            'where_used': where_used_enhanced
        }

        file_path = os.path.join(output_dir, f"{url_friendly_id}.md")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('---\n')
            yaml.dump(gwo_data, file, allow_unicode=True)
            file.write('---\n')

    print("Successfully generated gwo markdown files")

def generate_about_markdown_files(cursor: sqlite3.Cursor, output_path: str, programs_data, fiscal_year: str):
    """Generate the about page using pre-generated data."""
    spending_total = get_government_wide_spending_total(cursor, fiscal_year)

    page = {
        'title': 'About the FPI',
        'layout': 'about-fpi',
        'permalink': '/about/fpi',
        'fiscal_year': fiscal_year,
        'spending_total': spending_total,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write('---\n')
        yaml.dump(page, file, allow_unicode=True)
        file.write('---\n')
    print("Successfully generated about page")

def generate_pon_markdown_files(cursor: sqlite3.Cursor, output_dir: str):
    """Generate markdown files for pons with related programs."""
    recreate_directory(output_dir)

    cursor.execute("""
        SELECT DISTINCT
            pon.id,
            taxonomy_focus_area.focus_area,
            taxonomy_category.category,
            pon.pon2,
            pon.pon_definition
        FROM pon
        JOIN program_to_pon ON pon.id = program_to_pon.pon_id
        JOIN taxonomy_focus_area ON pon.focus_area_id = taxonomy_focus_area.id
        JOIN taxonomy_category ON taxonomy_focus_area.category_id = taxonomy_category.id
    """)

    pons = cursor.fetchall()

    for pon in pons:
        cursor.execute("""
            SELECT 
                p.id,
                p.name,
                a1.agency_name,
                p.program_type
            FROM program p
            JOIN program_to_pon ON p.id = program_to_pon.program_id
            LEFT JOIN agency a ON p.agency_id = a.id
            LEFT JOIN agency a1 ON a.tier_1_agency_id = a1.id
            WHERE program_to_pon.pon_id = ?
            ORDER BY p.name
        """, (pon["id"],))

        where_used = cursor.fetchall()

        url_friendly_id = pon['id'].replace('#','_').replace('.','_')

        # Enhance where_used with agency and expenditure data
        where_used_enhanced = []
        for p in where_used:
            program_data = {
                'permalink': f"/program/{p['id']}",
                'name': p['name'],
                'agency': p['agency_name'] or 'Unspecified',
                'program_type': p['program_type']
            }

            # Use expenditure, because we may need to compare different program types
            expenditure_amount = 0.0
            spending = get_amounts(cursor, p['id'], FISCAL_YEARS)
            if spending:
                expenditure_amount = next((o.get('expenditure', 0.0) for o in spending if o.get('x') == constants.CURRENT_FISCAL_YEAR), 0.0)

            program_data['expenditure_amount'] = expenditure_amount
            where_used_enhanced.append(program_data)

        pon_data = {
            'permalink': f"/pon/{url_friendly_id}",
            'title': pon['pon2'],
            'gwo_id': pon["id"],
            'focus_area': pon["focus_area"],
            'category': pon['category'],
            'definition': pon['pon_definition'],
            'where_used': where_used_enhanced
        }

        file_path = os.path.join(output_dir, f"{url_friendly_id}.md")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('---\n')
            yaml.dump(pon_data, file, allow_unicode=True)
            file.write('---\n')

    print("Successfully generated pon markdown files")

def generate_program_data(cursor: sqlite3.Cursor, fiscal_years: list[str]) -> List[Dict[str, Any]]:
    """
    Generate comprehensive program data that can be reused across different generation functions.
    Returns a list of dictionaries containing all necessary program information.
    """
    programs_data = []

    # Get base program information
    cursor.execute("""
        SELECT
            p.id,
            p.name,
            p.popular_name,
            p.objective,
            p.sam_url,
            p.usaspending_awards_url as usaspending_url,
            p.grants_url,
            p.program_type,
            p.agency_id,
            (SELECT a2.agency_name
             FROM agency a2
             WHERE a2.id = a.tier_1_agency_id) as top_agency_name,
            (SELECT a2.agency_name
             FROM agency a2
             WHERE a2.id = a.tier_2_agency_id) as sub_agency_name,
            p.is_subpart_f,
            p.rules_regulations
        FROM program p
        LEFT JOIN agency a ON p.agency_id = a.id
        ORDER BY p.id
    """)

    base_programs = cursor.fetchall()

    for program in base_programs:
        cursor.execute("""
            SELECT DISTINCT
                c.id as category_id,
                c.type as category_type,
                CASE
                    WHEN c.type = 'assistance' AND c.parent_id IS NOT NULL
                    THEN pc.name
                    ELSE c.name
                    END as category_name,
                pc.name as parent_category_name
                FROM program_to_category ptc
                INNER JOIN category c ON ptc.category_id = c.id
                LEFT JOIN category pc ON c.parent_id = pc.id AND c.type = pc.type
                WHERE ptc.program_id = ?
                AND c.type = ptc.category_type
                AND c.type <> 'category'
            UNION
            SELECT
                ptl.taxonomy_category_id AS category_id,
                'category' AS category_type,
                f.focus_area AS category_name,
                c.category AS parent_category_name
            FROM program_taxonomy_lookup ptl
            JOIN taxonomy_category c ON ptl.taxonomy_category_id = c.id
            JOIN taxonomy_focus_area f ON ptl.taxonomy_focus_area_id = f.id
            WHERE ptl.program_id = ?
        """, (program['id'],program['id']))

        categories = cursor.fetchall()

        # Get obligations based on program type
        program_type = program['program_type']
        if program_type == 'assistance_listing':
            obligations = get_assistance_program_obligations(cursor, program['id'], fiscal_years)
            other_program_spending = None
            outlays = get_amounts(cursor, program['id'], fiscal_years)
        elif program_type == 'contracts' or program_type == 'government_service':
            obligations = None
            other_program_spending = None
            outlays = get_amounts(cursor, program['id'], fiscal_years)
        else:
            obligations = None
            other_program_spending = get_other_program_amounts(cursor, program['id'], fiscal_years)
            outlays = None

        # Get program results
        cursor.execute("""
            SELECT fiscal_year, result
            FROM program_result
            WHERE program_id = ?
            ORDER BY fiscal_year
        """, (program['id'],))
        results = [{'year': str(row['fiscal_year']), 'description': row['result']}
                  for row in cursor.fetchall()]

        # Get program authorizations
        cursor.execute("""
            SELECT text, url
            FROM program_authorization
            WHERE program_id = ?
        """, (program['id'],))
        authorizations = [{'text': row['text'], 'url': row['url']} for row in cursor.fetchall()]

        # Get program objective
        cursor.execute("""
            SELECT gwo.id, gwo.gwo FROM program_to_gwo
            JOIN gwo ON program_to_gwo.gwo_id = gwo.id
            WHERE program_to_gwo.program_id = ?
        """, (program['id'],))
        gwo_row = cursor.fetchone()
        gwo = None
        if gwo_row is not None:
            url_friendly_id = gwo_row['id'].replace('#','_').replace('.','_')
            gwo = {
                'gwo': gwo_row['gwo'],
                'permalink': f"/gwo/{url_friendly_id}"
            }

        # Get program outcomes
        cursor.execute("""
            SELECT pon.id, pon.pon2 FROM program_to_pon
            JOIN pon ON program_to_pon.pon_id = pon.id
            WHERE program_to_pon.program_id = ?
            ORDER BY pon.pon2
        """, (program['id'],))
        pons = [{
            'pon': row['pon2'],
            'permalink': f"/pon/{row['id'].replace('#','_').replace('.','_')}"
        } for row in cursor.fetchall()]

        # Use sets to prevent duplicates when organizing categories
        program_categories = {
            'assistance': {},
            'beneficiary': {},
            'applicant': {},
            'categories': {}
        }

        for cat in categories:
            category_type = cat['category_type']
            category_id = cat['category_id']

            if category_type in ['assistance', 'beneficiary', 'applicant']:
                program_categories[category_type][category_id] = cat['category_name']
            elif category_type == 'category':
                if cat['parent_category_name']:
                    program_categories['categories'][category_id] = (
                        f"{cat['parent_category_name']} - {cat['category_name']}"
                    )
                else:
                    program_categories['categories'][category_id] = cat['category_name']

        improper_payment_data = get_improper_payment_info(cursor, program['id'])
        related_programs = get_related_programs(cursor, improper_payment_data, program['id'])

        # Calculate improper payment metrics
        improper_payment_metrics = {}
        if improper_payment_data and len(improper_payment_data) > 0:
            improper_payment_metrics = calculate_improper_payment_metrics(
                improper_payment_data
            )
        else:
            # Ensure default values when no improper payment data
            improper_payment_metrics = {
                'has_mappings': False,
                'is_multiple': False,
                'improper_payments_total': 0,
                'improper_payments_percent': 0,
                'current_year_details': [],
                'sparkline': []
            }

        # Use expenditure, because we may need to compare different program types
        headline_amount = get_expenditure_for_program(
            outlays,
            other_program_spending,
            constants.CURRENT_FISCAL_YEAR
        )

        # Create comprehensive program data
        program_data = {
            'id': program['id'],
            'name': program['name'],
            'popular_name': program['popular_name'],
            'objective': program['objective'],
            'sam_url': program['sam_url'],
            'usaspending_url': program['usaspending_url'],
            'grants_url': program['grants_url'],
            'agency_id': program['agency_id'],
            'top_agency_name': program['top_agency_name'],
            'sub_agency_name': program['sub_agency_name'],
            'assistance_types': sorted(list(set(program_categories['assistance'].values()))),
            'beneficiary_types': sorted(list(set(program_categories['beneficiary'].values()))),
            'applicant_types': sorted(list(set(program_categories['applicant'].values()))),
            'categories': sorted(list(set(program_categories['categories'].values()))),
            'obligations': obligations,
            'other_program_spending': other_program_spending,
            'outlays': outlays,
            'results': results,
            'authorizations': authorizations,
            'program_type': program['program_type'],
            'is_subpart_f': program['is_subpart_f'],
            'rules_regulations': program['rules_regulations'],
            'improper_payments': improper_payment_data,
            'related_programs': related_programs,
            'improper_payment_metrics': improper_payment_metrics,
            'headline_amount': round(headline_amount, 2),
            'gwo': gwo,
            'pons': pons
        }

        programs_data.append(program_data)

    print("Completed program object creation")

    return programs_data


def generate_shared_data(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """
    Generate shared data used across multiple pages.
    Returns a dictionary containing agencies, applicant types, and categories data.
    """
    # Get CFO agencies
    cursor.execute("""
        SELECT DISTINCT 
            a1.id,
            a1.agency_name as title
        FROM program p
        JOIN agency a ON p.agency_id = a.id
        JOIN agency a1 ON a.tier_1_agency_id = a1.id
        -- hide USAID (aka "Agency for International Development") from search filters
        WHERE a1.is_cfo_act_agency = 1 AND a1.id <> 100148640
        ORDER BY title
    """)
    
    cfo_agencies = []
    for row in cursor.fetchall():
        if not row['title']:
            continue
            
        agency = {'title': row['title']}
        
        # Check if this agency has any sub-agencies
        cursor.execute("""
            SELECT DISTINCT a2.agency_name as title
            FROM agency a
            JOIN agency a2 ON a.tier_2_agency_id = a2.id
            WHERE a.tier_1_agency_id = ?
            AND a.tier_2_agency_id IS NOT NULL
            AND a2.agency_name IS NOT NULL
        """, (row['id'],))
        
        has_sub_agencies = len(cursor.fetchall()) > 0
        
        if has_sub_agencies:
            # Get programs associated only with the top-level agency
            cursor.execute("""
                SELECT DISTINCT p.id
                FROM program p
                JOIN agency a ON p.agency_id = a.id
                WHERE a.tier_1_agency_id = ?
                AND a.tier_2_agency_id IS NULL
            """, (row['id'],))
            
            top_level_only_programs = set(r['id'] for r in cursor.fetchall())
            
            # Get sub-agencies and their programs
            cursor.execute("""
                SELECT DISTINCT
                    a2.agency_name as title,
                    GROUP_CONCAT(p.id) as program_ids
                FROM program p
                JOIN agency a ON p.agency_id = a.id
                JOIN agency a2 ON a.tier_2_agency_id = a2.id
                WHERE a.tier_1_agency_id = ?
                AND a.tier_2_agency_id IS NOT NULL
                AND a2.agency_name IS NOT NULL
                GROUP BY a2.agency_name
                ORDER BY title
            """, (row['id'],))
            
            sub_agencies = []
            for sub_row in cursor.fetchall():
                if sub_row['title']:
                    program_ids = set(sub_row['program_ids'].split(',') if sub_row['program_ids'] else [])
                    sub_agencies.append({
                        'title': sub_row['title']
                    })
            
            # Add Unspecified sub-agency if needed
            if sub_agencies and top_level_only_programs:
                sub_agencies.append({
                    'title': 'Unspecified'
                })
            
            if sub_agencies:
                agency['sub_categories'] = sub_agencies
                
        cfo_agencies.append(agency)
    
    # Get non-CFO agencies
    cursor.execute("""
        SELECT DISTINCT 
            a1.id,
            a1.agency_name as title
        FROM program p
        JOIN agency a ON p.agency_id = a.id
        JOIN agency a1 ON a.tier_1_agency_id = a1.id
        WHERE a1.is_cfo_act_agency = 0
        ORDER BY title
    """)
    
    other_agencies = []
    for row in cursor.fetchall():
        if not row['title']:
            continue
            
        agency = {'title': row['title']}
        
        # Check if this agency has any sub-agencies
        cursor.execute("""
            SELECT DISTINCT a2.agency_name as title
            FROM agency a
            JOIN agency a2 ON a.tier_2_agency_id = a2.id
            WHERE a.tier_1_agency_id = ?
            AND a.tier_2_agency_id IS NOT NULL
            AND a2.agency_name IS NOT NULL
        """, (row['id'],))
        
        has_sub_agencies = len(cursor.fetchall()) > 0
        
        if has_sub_agencies:
            # Get programs associated only with the top-level agency
            cursor.execute("""
                SELECT DISTINCT p.id
                FROM program p
                JOIN agency a ON p.agency_id = a.id
                WHERE a.tier_1_agency_id = ?
                AND a.tier_2_agency_id IS NULL
            """, (row['id'],))
            
            top_level_only_programs = set(r['id'] for r in cursor.fetchall())
            
            # Get sub-agencies and their programs
            cursor.execute("""
                SELECT DISTINCT
                    a2.agency_name as title,
                    GROUP_CONCAT(p.id) as program_ids
                FROM program p
                JOIN agency a ON p.agency_id = a.id
                JOIN agency a2 ON a.tier_2_agency_id = a2.id
                WHERE a.tier_1_agency_id = ?
                AND a.tier_2_agency_id IS NOT NULL
                AND a2.agency_name IS NOT NULL
                GROUP BY a2.agency_name
                ORDER BY title
            """, (row['id'],))
            
            sub_agencies = []
            for sub_row in cursor.fetchall():
                if sub_row['title']:
                    program_ids = set(sub_row['program_ids'].split(',') if sub_row['program_ids'] else [])
                    sub_agencies.append({
                        'title': sub_row['title']
                    })
            
            # Add Unspecified sub-agency if needed
            if sub_agencies and top_level_only_programs:
                sub_agencies.append({
                    'title': 'Unspecified'
                })
            
            if sub_agencies:
                agency['sub_categories'] = sub_agencies
                
        other_agencies.append(agency)
    
    # Get simple categories for applicants
    cursor.execute("""
        SELECT DISTINCT 
            c.name as title
        FROM program p
        JOIN program_to_category ptc ON p.id = ptc.program_id
        JOIN category c ON ptc.category_id = c.id
        WHERE c.type = 'applicant'
        AND c.type = ptc.category_type
        AND EXISTS (SELECT 1 FROM category WHERE id = ptc.category_id AND type = ptc.category_type)
        ORDER BY c.name
    """)
    applicant_types = [{'title': row['title']} for row in cursor.fetchall()]
    
    # Get simple categories for assistance types
    cursor.execute("""
        WITH assistance_names AS (
            SELECT DISTINCT 
                CASE 
                    WHEN c.parent_id IS NOT NULL AND pc.id = c.parent_id AND pc.type = c.type THEN pc.name
                    ELSE c.name 
                END as title
            FROM program p
            JOIN program_to_category ptc ON p.id = ptc.program_id
            JOIN category c ON ptc.category_id = c.id AND c.type = 'assistance' 
            LEFT JOIN category pc ON c.parent_id = pc.id AND c.type = pc.type
            WHERE c.type = ptc.category_type
            AND p.program_type = 'assistance_listing'
            AND title IS NOT NULL
        )
        SELECT title
        FROM assistance_names
        ORDER BY title
    """)
    assistance_types = [{'title': row['title']} for row in cursor.fetchall()]

    # Get simple categories for beneficiary types
    cursor.execute("""
        SELECT DISTINCT 
            c.name as title
        FROM program p
        JOIN program_to_category ptc ON p.id = ptc.program_id
        JOIN category c ON ptc.category_id = c.id
        WHERE c.type = 'beneficiary'
        AND c.type = ptc.category_type
        AND EXISTS (SELECT 1 FROM category WHERE id = ptc.category_id AND type = ptc.category_type)
        ORDER BY c.name
    """)
    beneficiary_types = [{'title': row['title']} for row in cursor.fetchall()]
    
    # Get categories with subcategories
    cursor.execute("""
        SELECT DISTINCT
            taxonomy_category.id as id,
            taxonomy_category.category as title,
            taxonomy_focus_area.focus_area as sub_title
        FROM taxonomy_category
        JOIN program_taxonomy_lookup ON
            taxonomy_category.id = program_taxonomy_lookup.taxonomy_category_id
        LEFT JOIN taxonomy_focus_area ON
            taxonomy_category.id = taxonomy_focus_area.category_id
        ORDER BY taxonomy_category.category, taxonomy_focus_area.focus_area
    """)
    
    categories = []
    current_category = None
    
    for row in cursor.fetchall():
        if not row['title']:
            continue
            
        if current_category is None or current_category['title'] != row['title']:
            current_category = {
                'title': row['title'],
                'sub_categories': []
            }
            categories.append(current_category)
        
        if row['sub_title']:
            sub_exists = False
            for existing_sub in current_category['sub_categories']:
                if existing_sub['title'] == row['sub_title']:
                    sub_exists = True
                    break
            if not sub_exists:
                current_category['sub_categories'].append({
                    'title': row['sub_title']
                })

    # Get GWO (Government-wide Objectives) options
    cursor.execute("""
        SELECT DISTINCT gwo.gwo as title
        FROM gwo
        JOIN program_to_gwo ON gwo.id = program_to_gwo.gwo_id
        ORDER BY gwo.gwo
    """)
    gwo_options = [{'title': row['title']} for row in cursor.fetchall()]

    # Get PON (Program Outcomes) options
    cursor.execute("""
        SELECT DISTINCT pon.pon2 as title
        FROM pon
        JOIN program_to_pon ON pon.id = program_to_pon.pon_id
        ORDER BY pon.pon2
    """)
    pon_options = [{'title': row['title']} for row in cursor.fetchall()]

    print("Completed shared data creation")
    
    return {
        'cfo_agencies': sorted(cfo_agencies, key=lambda x: x['title']),
        'other_agencies': sorted(other_agencies, key=lambda x: x['title']),
        'applicant_types': applicant_types,
        'assistance_types': assistance_types,
        'beneficiary_types': beneficiary_types,
        'categories': sorted(categories, key=lambda x: x['title']),
        'gwo_options': gwo_options,
        'pon_options': pon_options
    }

def generate_program_markdown_files(output_dir: str, programs_data: List[Dict[str, Any]], fiscal_years: list[str]):
    """Generate individual markdown files for each program using pre-generated data."""
    recreate_directory(output_dir)

    for program in programs_data:
        # Create listing dictionary using pre-generated data
        listing = {
            'title': program['name'],
            'layout': 'program',
            'permalink': f"/program/{program['id']}.html",
            'fiscal_year': constants.LAST_COMPLETED_FISCAL_YEAR,
            'cfda': program['id'],
            'objective': program['objective'],
            'sam_url': program['sam_url'],
            'usaspending_url': program['usaspending_url'],
            'grants_url': program['grants_url'],
            'popular_name': program['popular_name'] if program['popular_name'] else '',
            'assistance_types': program['assistance_types'],
            'beneficiary_types': program['beneficiary_types'],
            'applicant_types': program['applicant_types'],
            'categories': program['categories'],
            'agency': program['top_agency_name'] or 'Unspecified',
            'agency_id': program['agency_id'],
            'sub-agency': program['sub_agency_name'] or 'N/A',
            'obligations': json.dumps(program['obligations'], separators=(',', ':')),
            'results': program['results'],
            'program_type': program['program_type'],
            'authorizations': [{'text': auth['text'], 'url': auth['url']} for auth in program['authorizations']],
            'is_subpart_f': program['is_subpart_f'],
            'rules_regulations': program['rules_regulations'],
            'improper_payments': program['improper_payment_metrics'].get('current_year_details', []),
            'improper_payments_total': program['improper_payment_metrics'].get('improper_payments_total', 0),
            'improper_payments_percent': program['improper_payment_metrics'].get('improper_payments_percent', 0),
            'improper_payments_is_multiple': program['improper_payment_metrics'].get('is_multiple', False),
            'improper_payments_sparkline': json.dumps(program['improper_payment_metrics'].get('sparkline', []), separators=(',', ':')),
            'improper_payments_related_programs': program['related_programs'],
            'headline_amount': program.get('headline_amount', 0),
            'gwo': program['gwo'],
            'pons': program['pons']
        }

        # Add obligations based on program type
        if program['program_type'] == 'assistance_listing':
            listing['obligations'] = json.dumps(program['obligations'], separators=(',', ':'))
            listing['outlays'] = json.dumps(program['outlays'], separators=(',', ':'))
            listing['other_program_spending'] = None
        elif program['program_type'] == 'contracts' or \
            program['program_type'] == 'government_service':
                listing['obligations'] = None
                listing['outlays'] = json.dumps(program['outlays'], separators=(',', ':'))
                listing['other_program_spending'] = None
        else:
            listing['other_program_spending'] = json.dumps(program['other_program_spending'], separators=(',', ':'))
            listing['obligations'] = None
            listing['outlays'] = None

        # Write markdown file
        markdown_file_path = os.path.join(output_dir, f"{program['id']}.md")
        with open(markdown_file_path, 'w', encoding='utf-8') as file:
            file.write('---\n')
            yaml.dump(listing, file, allow_unicode=True)
            file.write('---\n')

    print(f"Created markdown files for {len(programs_data)} programs")


def generate_search_page(output_path: str, shared_data: Dict[str, Any], fiscal_year: str):
    """Generate the search page using pre-generated shared data."""
    search_page = {
        'title': 'Program search',
        'layout': 'search',
        'permalink': '/search.html',
        'fiscal_year': fiscal_year,
        'cfo_agencies': shared_data['cfo_agencies'],
        'other_agencies': shared_data['other_agencies'],
        'applicant_types': shared_data['applicant_types'],
        'assistance_types': shared_data['assistance_types'],
        'beneficiary_types': shared_data['beneficiary_types'],
        'categories': shared_data['categories'],
        'gwo_options': shared_data['gwo_options'],
        'pon_options': shared_data['pon_options']
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write('---\n')
        yaml.dump(search_page, file, allow_unicode=True)
        file.write('---\n')
    print("Successfully generated search page")

def get_government_wide_spending_total(cursor, fiscal_year):
    cursor.execute("""
        SELECT
            SUM(expenditure) AS total
        FROM program_amounts_lookup
        WHERE fiscal_year = ?
    """, (str(fiscal_year),))

    total = cursor.fetchone()

    return total['total']

def get_expenditure_for_program(outlays, other_program_spending, fiscal_year):
    expenditures = 0
    other_expenditures = 0

    if outlays:
        for item in outlays:
            if item.get('x') == str(fiscal_year):
                expenditures = item.get('expenditure', 0)
                break
    elif other_program_spending:
        for item in other_program_spending:
            if item.get('x') == str(fiscal_year):
                other_expenditures = item.get('outlays', 0) + item.get('forgone_revenue', 0)
                break

    return expenditures + other_expenditures

def build_data_sources_config() -> Dict[str, Any]:
    """Build the data sources configuration structure.
    
    Returns a dictionary mapping program types, year types, and spending types to data sources.
    This follows the pattern of other configuration exports in this module.
    """
    # Tax expenditure mapping (includes revenue_losses for forgone_revenue)
    tax_expenditure_sources = {
        'obligations': 'Treasury.gov',
        'outlays': 'USASpending.gov',
        'revenue_losses': 'USASpending.gov',
        'expenditure': 'Treasury.gov'
    }
    
    # Interest mapping (includes revenue_losses for forgone_revenue)
    interest_sources = {
        'obligations': 'USASpending.gov',
        'outlays': 'USASpending.gov',
        'revenue_losses': 'USASpending.gov',
        'expenditure': 'USASpending.gov'
    }
    
    # Default mapping: all spending types point to USASpending.gov (no revenue_losses)
    default_usaspending = {
        'obligations': 'USASpending.gov',
        'outlays': 'USASpending.gov',
        'expenditure': 'USASpending.gov'
    }
    
    # Assistance listing current year (SAM.gov for obligations/expenditure, no revenue_losses)
    assistance_listing_current = {
        'obligations': 'SAM.gov',
        'outlays': 'USASpending.gov',
        'expenditure': 'SAM.gov'
    }
    
    return {
        'tax_expenditure': {
            'current_year': tax_expenditure_sources,
            'prior_year': tax_expenditure_sources
        },
        'interest': {
            'current_year': interest_sources,
            'prior_year': interest_sources
        },
        'contracts': {
            'current_year': default_usaspending,
            'prior_year': default_usaspending
        },
        'government_service': {
            'current_year': default_usaspending,
            'prior_year': default_usaspending
        },
        'assistance_listing': {
            'current_year': assistance_listing_current,
            'prior_year': default_usaspending
        }
    }

def export_data_sources_config():
    """Export data sources configuration to YAML file.
    
    Writes the configuration to website/_data/data_sources.yml with Jekyll front matter.
    This follows the same pattern as export_inflation_population_from_csv().
    """
    config = build_data_sources_config()

    class NoAliasDumper(yml.SafeDumper):
        """YAML dumper that always expands mappings instead of anchors/aliases."""

        def ignore_aliases(self, data):
            return True
    
    try:
        with open(DATA_SOURCES_YML_PATH, 'w', encoding='utf-8') as file:
            yml_data = {
                'data_sources': config
            }
            file.write('---\n')
            yml.dump(yml_data, file, allow_unicode=True, Dumper=NoAliasDumper)
            file.write('...\n')
        print(f'Exported data sources configuration to {DATA_SOURCES_YML_PATH}')
    except Exception as e:
        print(f'Error exporting data sources config: {e}')

def generate_home_page(cursor: sqlite3.Cursor, output_path: str, programs_data,
                       shared_data: Dict[str, Any], fiscal_year: str):
    """Generate the home page using pre-generated data."""
    spending_total = get_government_wide_spending_total(cursor, fiscal_year)

    agencies_count = len(shared_data['cfo_agencies']) + len(shared_data['other_agencies'])

    page = {
        'title': 'Home',
        'layout': 'home',
        'permalink': '/',
        'fiscal_year': fiscal_year,
        'cfo_agencies': shared_data['cfo_agencies'],
        'other_agencies': shared_data['other_agencies'],
        'applicant_types': shared_data['applicant_types'],
        'program_types': shared_data['assistance_types'],
        'categories': shared_data['categories'],
        # spaces in number formatting force jekyll to treat comma formatted numbers as strings
        'programs_count': f"{len(programs_data):,} ",
        'spending_total': spending_total,
        'agencies_count': f"{agencies_count:,} ",
        'outcomes_count': f"{len(shared_data['pon_options']):,} "
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write('---\n')
        yaml.dump(page, file, allow_unicode=True)
        file.write('---\n')
    print("Successfully generated home page")


def generate_programs_table_json(output_path: str, programs_data: List[Dict[str, Any]], fiscal_year: str):
    """Generate the programs table JSON file using pre-generated data."""
    programs_json = []

    for program in programs_data:
        current_year_obligation = get_expenditure_for_program(
            program['outlays'],
            program['other_program_spending'],
            fiscal_year
        )

        unique_categories = set()
        categories_json = []

        for cat in program['categories']:
            parts = cat.split(' - ', 1)
            if len(parts) == 2:
                parent, subcategory = parts
                category_tuple = (parent, subcategory)
                if category_tuple not in unique_categories:
                    unique_categories.add(category_tuple)
                    categories_json.append({
                        'title': parent,
                        'subCategory': {'title': subcategory}
                    })

        program_json = {
            'cfda': program['id'],
            'title': program['name'],
            'permalink': f"/program/{program['id']}",
            'obligations': float(current_year_obligation),
            'programType': program['program_type'],
            'objectives': program['objective'],
            'gwo': [program['gwo']['gwo']] if program['gwo'] is not None else [],
            'pons': [row['pon'] for row in program['pons']],
            'popularName': program['popular_name'],
            'agency': {
                'title': program['top_agency_name'] or 'Unspecified',
                'subAgency': {
                    'title': program['sub_agency_name'] or 'N/A'
                }
            },
            'assistanceTypes': program['assistance_types'],
            'applicantTypes': program['applicant_types'],
            'categories': categories_json
        }

        programs_json.append(program_json)

    # Sort by obligations descending
    programs_json.sort(key=lambda x: x['obligations'], reverse=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(programs_json, file, separators=(',', ':'))
    print("Successfully generated program json")


def generate_category_page(cursor: sqlite3.Cursor,
                           programs_data: List[Dict[str, Any]],
                           output_path: str, fiscal_year: str):
    """Generate the category page using a mix of pre-generated data and database queries."""
    # Get all unique categories and their hierarchies
    categories = set()
    for program in programs_data:
        for category in program['categories']:
            if ' - ' in category:
                parent = category.split(' - ')[0]
                categories.add(parent)
    categories = sorted(list(categories))

    # Get all program IDs
    cursor.execute("""
        SELECT DISTINCT id 
        FROM program
    """)
    program_ids = [row['id'] for row in cursor.fetchall()]

    # Calculate obligations by program type using the utility function
    obligations_result = get_program_expenditures_by_type(cursor, program_ids, fiscal_year)
    obligations_by_type = []
    
    for prog_type, total_obs in obligations_result.items():
        if total_obs > 0:
            title = constants.PROGRAM_TYPE_MAPPING.get(prog_type, prog_type)
            if title == 'Major Acquisition Programs':
                title = 'Acquisition Programs'
            obligations_by_type.append({
                'title': title,
                'total_obs': total_obs
            })

    # Get total number of unique programs
    total_programs = len(programs_data)

    # Total obligations is sum of all program type obligations
    total_obs = sum(type_obj['total_obs'] for type_obj in obligations_by_type)

    # Calculate category stats
    category_stats = {}
    for category in categories:
        # Get programs for this category
        cursor.execute("""
            SELECT DISTINCT p.id, p.program_type
            FROM program p
            JOIN program_taxonomy_lookup ptl ON p.id = ptl.program_id
            JOIN taxonomy_category c ON ptl.taxonomy_category_id = c.id
            WHERE c.category = ?
        """, (category,))
        programs = cursor.fetchall()

        if programs:
            program_ids = [p['id'] for p in programs]
            
            # Use the utility function to calculate obligations
            obligations_result = get_program_expenditures_by_type(cursor, program_ids, fiscal_year)
            total_cat_obs = sum(total_obs for total_obs in obligations_result.values())

            category_stats[category] = {
                'title': category,
                'total_num_programs': len(programs),
                'total_obs': total_cat_obs,
                'permalink': f"/category/{convert_to_url_string(category)}"
            }

    # Prepare categories list and JSON
    categories_list = [{
        'title': cat,
        'permalink': f"/category/{convert_to_url_string(cat)}"
    } for cat in categories]

    categories_json = json.dumps(sorted(list(category_stats.values()),
                                        key=lambda x: x['total_obs'],
                                        reverse=True),
                                 separators=(',', ':'))

    category_page = {
        'title': 'Categories',
        'layout': 'category-index',
        'permalink': '/category.html',
        'fiscal_year': fiscal_year,
        'total_num_programs': total_programs,
        'total_obs': total_obs,
        'obligations_by_type': sorted(obligations_by_type, key=lambda x: x['title']),
        'categories': categories_list,
        'categories_json': categories_json,
        'categories_hierarchy': get_categories_hierarchy(cursor)
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write('---\n')
        yaml.dump(category_page, file, allow_unicode=True)
        file.write('---\n')


def generate_program_csv(output_path: str, programs_data: List[Dict[str, Any]], fiscal_years: list[str]):
    """Generate CSV file containing all program data using pre-generated data."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow([
            'program_number',
            'title',
            'popular_name',
            'agency',
            'sub-agency',
            'objective',
            'sam_url',
            'usaspending_url',
            'grants_url',
            'assistance_types',
            'beneficiary_types',
            'applicant_types',
            'categories',
            'obligations',
            'outlays',
            'other expenditures',

        ])

        for program in programs_data:
            csvwriter.writerow([
                program['id'],
                program['name'],
                program['popular_name'] or '',
                program['top_agency_name'] or 'Unspecified',
                program['sub_agency_name'] or 'N/A',
                program['objective'],
                program['sam_url'],
                program['usaspending_url'],
                program['grants_url'],
                ','.join(program['assistance_types']),
                ','.join(program['beneficiary_types']),
                ','.join(program['applicant_types']),
                ','.join(program['categories']),
                json.dumps([{
                    'x': obl['x'],
                    'sam_spending': obl['sam_actual'],
                    'usa_spending_actual': obl['usa_spending_actual']
                } for obl in program['obligations']], separators=(',', ':')) if program['obligations'] else "",
                json.dumps(program['outlays'], separators=(',', ':')) if program['outlays'] else "",
                json.dumps([{
                    'x': spend['x'],
                    'outlays': spend['outlays'],
                    **({'revenue_losses': spend['forgone_revenue']} if 'forgone_revenue' in spend else {})
                } for spend in program['other_program_spending']], separators=(',', ':')) if program['other_program_spending'] else ""
            ])

    print(f"Generated CSV file with {len(programs_data)} programs")

def export_inflation_population_from_csv():
    inflation_population_data = []

    #csv into memory
    with open(INFLATION_POPULATION_FILE_PATH, newline="", encoding='utf-8') as file:
        csvreader = csv.DictReader(file)
        for row in csvreader:
            inflation_population_data.append({
                "Year": int(row["Year"]),
                "InflationRatePercentage": float(row["Inflation Rate Percentage"]),
                "PopulationGrowthPercentage": float(row["Population Growth Percentage"])
            })

        #write to yml
        with open(GLOBAL_DATA_YML_PATH, 'w', encoding='utf-8') as file:
            yml_data = {
                "InflationPopulation": inflation_population_data
            }
            file.write("---\n")
            yml.dump(yml_data, file, allow_unicode=True)
            file.write("...\n")

def export_global_dates_to_yml():
    """Export constants to website/_data/constants_global_dates.yml for Jekyll."""
    data_path = Path(__file__).resolve().parents[1] / 'website' / '_data'
    data_path.mkdir(parents=True, exist_ok=True)
    constants_data = {
        "CURRENT_FISCAL_YEAR": constants.CURRENT_FISCAL_YEAR,
        "LAST_COMPLETED_FISCAL_YEAR": constants.LAST_COMPLETED_FISCAL_YEAR,
        "BASELINE_INFLATION_YEAR": constants.BASELINE_INFLATION_YEAR,
        "SPENDING_CHART_YEAR_RANGE": constants.SPENDING_CHART_YEAR_RANGE,
        "SITE_UPDATE_DATE": constants.SITE_UPDATE_DATE,
        "SAMGOV_ASSISTANCE_LISTINGS_DATE": constants.SAMGOV_ASSISTANCE_LISTINGS_DATE,
        "USASPENDING_TRANSACTION_DATE": constants.USASPENDING_TRANSACTION_DATE,
        "TREASURYGOV_TAX_EXPEND_DATE": constants.TREASURYGOV_TAX_EXPEND_DATE,
        "PAYMENTACCURACY_FY_DATE": constants.PAYMENTACCURACY_FY_DATE
    }
    output_file = data_path / 'constants_global_dates.yml'
    with open(output_file, 'w', encoding='utf-8') as file:
        yaml.dump(constants_data, file, default_flow_style=False, allow_unicode=True)
    print(f"Exported global date variables to {output_file}")
    return output_file


try:
    conn = sqlite3.connect(full_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    programs_data = generate_program_data(cursor, FISCAL_YEARS)

    shared_data = generate_shared_data(cursor)

    generate_program_markdown_files(MARKDOWN_DIR, programs_data, FISCAL_YEARS)

    generate_program_csv('../website/assets/files/all-program-data.csv', programs_data, FISCAL_YEARS)

    export_inflation_population_from_csv()

    export_global_dates_to_yml()

    export_data_sources_config()

    search_path = os.path.join('../website', 'pages', 'search.md')
    generate_search_page(search_path, shared_data, constants.CURRENT_FISCAL_YEAR)

    category_path = os.path.join('../website', 'pages', 'category.md')
    generate_category_page(cursor, programs_data, category_path,
                           constants.LAST_COMPLETED_FISCAL_YEAR)

    home_path = os.path.join('../website', 'pages', 'home.md')
    generate_home_page(cursor, home_path, programs_data, shared_data, constants.LAST_COMPLETED_FISCAL_YEAR)

    programs_json_path = os.path.join('../indexer', 'programs-table.json')
    generate_programs_table_json(programs_json_path, programs_data,
                                 constants.CURRENT_FISCAL_YEAR)

    category_dir = os.path.join('../website', '_category')
    generate_category_markdown_files(cursor, category_dir, constants.LAST_COMPLETED_FISCAL_YEAR)

    subcategory_dir = os.path.join('../website', '_subcategory')
    generate_subcategory_markdown_files(cursor, subcategory_dir, constants.LAST_COMPLETED_FISCAL_YEAR)

    gwo_dir = os.path.join('../website', '_gwo')
    generate_gwo_markdown_files(cursor, gwo_dir)

    pon_dir = os.path.join('../website', '_pon')
    generate_pon_markdown_files(cursor, pon_dir)

    about_path = os.path.join('../website', 'pages', 'about-fpi.md')
    generate_about_markdown_files(cursor, about_path, programs_data, constants.LAST_COMPLETED_FISCAL_YEAR)

except sqlite3.Error as e:
    print(f"Database error occurred: {e}")
    raise e
except Exception as e:
    print(f"An error occurred: {e}")
    raise e
finally:
    if 'conn' in locals():
        conn.close()