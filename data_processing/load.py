"""Creates markdown files for static site generation."""

import sqlite3
import os
import json
import yaml
import csv
import constants
from typing import List, Dict, Any

# Constants
CURRENT_DIR = os.getcwd()
DB_FILE_PATH = os.path.join("transformed", "transformed_data.db")
MARKDOWN_DIR = os.path.join(CURRENT_DIR, "..", "website", "_program")
full_path = os.path.join(CURRENT_DIR, DB_FILE_PATH)
FISCAL_YEARS = ['2023', '2024', '2025']


def ensure_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def get_assistance_program_obligations(cursor, program_id, fiscal_years):
    """Get obligations data for specified fiscal years."""
    obligations = []
    for year in fiscal_years:
        year_data = {
            'x': year,
            'sam_estimate': 0.0,
            'sam_actual': 0.0,
            'usa_spending_actual': 0.0
        }

        # Check if we have actual data first
        cursor.execute("""
            SELECT SUM(amount) as actual_amount
            FROM program_sam_spending
            WHERE program_id = ?
            AND fiscal_year = ?
            AND is_actual = 1
            GROUP BY fiscal_year
        """, (program_id, year))

        actual_row = cursor.fetchone()

        if actual_row and actual_row['actual_amount']:
            # If we have actual data, use that and ignore estimates
            year_data['sam_actual'] = float(actual_row['actual_amount'])
        else:
            # Only if we don't have actual data, check for estimates.
            # Regardless of whether the value is an actual (preferred) or
            # estimate, the value is stored as "sam_actual" and presented on
            # the frontend as just "SAM.gov"
            cursor.execute("""
                SELECT SUM(amount) as estimated_amount
                FROM program_sam_spending
                WHERE program_id = ?
                AND fiscal_year = ?
                AND is_actual = 0
                GROUP BY fiscal_year
            """, (program_id, year))

            estimate_row = cursor.fetchone()
            if estimate_row and estimate_row['estimated_amount']:
                year_data['sam_actual'] = float(estimate_row['estimated_amount'])

        # Get USA spending obligations for reference
        cursor.execute("""
            SELECT ROUND(SUM(obligations), 2) as total_obligations
            FROM usaspending_assistance_obligation_aggregation
            WHERE cfda_number = ? AND action_date_fiscal_year = ?
            GROUP BY cfda_number, action_date_fiscal_year
        """, (program_id, year))

        usa_row = cursor.fetchone()
        if usa_row and usa_row['total_obligations'] is not None:
            year_data['usa_spending_actual'] = float(usa_row['total_obligations'])

        obligations.append(year_data)

    return obligations


def get_other_program_obligations(cursor, program_id, fiscal_years):
    """Get obligations data for other programs."""
    other_program_obligations = []
    for year in fiscal_years:
        cursor.execute("""
            SELECT fiscal_year, outlays, forgone_revenue, source
            FROM other_program_spending
            WHERE program_id = ? AND fiscal_year = ?
        """, (program_id, year))

        row = cursor.fetchone()
        year_data = {
            'x': year,
            'outlays': float(row['outlays']) if row and row['outlays'] is not None else 0.0,
            'forgone_revenue': float(row['forgone_revenue']) if row and row['forgone_revenue'] is not None else 0.0
        }
        other_program_obligations.append(year_data)

    return other_program_obligations


def get_outlays_data(cursor, program_id, fiscal_years):
    """Get outlays data for specified fiscal years."""
    outlays = []
    for year in fiscal_years:
        year_data = {
            'x': year,
            'outlay': 0.0,
            'obligation': 0.0
        }

        # Get outlays data
        cursor.execute("""
            SELECT
                ROUND(SUM(outlay), 2) as total_outlay,
                ROUND(SUM(obligation), 2) as total_obligation
            FROM usaspending_assistance_outlay_aggregation
            WHERE cfda_number = ?
            AND award_first_fiscal_year = ?
            GROUP BY cfda_number, award_first_fiscal_year
        """, (program_id, year))

        row = cursor.fetchone()
        if row:
            if row['total_outlay'] is not None:
                year_data['outlay'] = float(row['total_outlay'])
            if row['total_obligation'] is not None:
                year_data['obligation'] = float(row['total_obligation'])

        outlays.append(year_data)

    return outlays


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
                'regular': [],
                'other_program': []
            }

        if row['program_type'] == 'assistance_listing':
            agency_programs[agency_name]['regular'].append(row['program_id'])
        else:
            agency_programs[agency_name]['other_program'].append(row['program_id'])

    # Calculate obligations for each agency
    agencies = []
    for agency_name, programs in agency_programs.items():
        total_obs = 0
        total_programs = len(programs['regular']) + len(programs['other_program'])

        # Get regular program obligations
        if programs['regular']:
            placeholders = ','.join('?' * len(programs['regular']))
            cursor.execute(f"""
                SELECT COALESCE(SUM(CASE
                    WHEN fiscal_year = ? AND is_actual = 0
                    THEN amount
                    ELSE 0
                END), 0) as total_obs
                FROM program_sam_spending
                WHERE program_id IN ({placeholders})
            """, [fiscal_year] + programs['regular'])

            total_obs += float(cursor.fetchone()['total_obs'])

        # Get other obligations
        if programs['other_program']:
            placeholders = ','.join('?' * len(programs['other_program']))
            cursor.execute(f"""
                SELECT COALESCE(SUM(outlays), 0) + COALESCE(SUM(forgone_revenue), 0) as total_obs
                FROM other_program_spending
                WHERE fiscal_year = ?
                AND program_id IN ({placeholders})
            """, [fiscal_year] + programs['other_program'])

            total_obs += float(cursor.fetchone()['total_obs'])

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
            pc.id as parent_id,
            pc.name as parent_name,
            c.name as sub_name
        FROM category pc
        LEFT JOIN category c ON c.parent_id = pc.id
        JOIN program_to_category ptc ON ptc.category_id = c.id
        JOIN program p ON ptc.program_id = p.id
        WHERE ptc.category_type = 'category'
        ORDER BY pc.name, c.name
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


def generate_category_markdown_files(cursor: sqlite3.Cursor, output_dir: str, fiscal_year: str):
    """Generate markdown files for categories with obligations from both regular and other programs."""
    ensure_directory_exists(output_dir)

    # Get all parent categories with at least one program
    cursor.execute("""
        WITH program_counts AS (
            SELECT
                c.parent_id,
                COUNT(DISTINCT p.id) as program_count
            FROM category c
            JOIN program_to_category ptc ON c.id = ptc.category_id
            JOIN program p ON ptc.program_id = p.id
            WHERE c.type = 'category'
            AND ptc.category_type = 'category'
            AND c.parent_id IS NOT NULL
            GROUP BY c.parent_id
            HAVING program_count > 0
        )
        SELECT DISTINCT
            c.parent_id as id,
            pc.name as title
        FROM category c
        JOIN category pc ON c.parent_id = pc.id
        JOIN program_counts pc_count ON c.parent_id = pc_count.parent_id
    """)

    parent_categories = cursor.fetchall()
    for parent in parent_categories:
        # Get unique program IDs in this category
        cursor.execute("""
            SELECT DISTINCT p.id, p.program_type
            FROM program p
            JOIN program_to_category ptc ON p.id = ptc.program_id
            JOIN category c ON ptc.category_id = c.id
            WHERE c.parent_id = ?
            AND ptc.category_type = 'category'
        """, (parent['id'],))

        programs = cursor.fetchall()
        if not programs:
            continue

        # Split programs by type
        regular_program_ids = [p['id'] for p in programs if p['program_type'] == 'assistance_listing']
        other_program_ids = [p['id'] for p in programs if p['program_type'] != 'assistance_listing']

        # Calculate total category obligations
        total_category_obs = 0

        # Get obligations for regular programs
        if regular_program_ids:
            placeholders = ','.join('?' * len(regular_program_ids))
            cursor.execute(f"""
                SELECT COALESCE(SUM(CASE
                    WHEN fiscal_year = ? AND is_actual = 0
                    THEN amount
                    ELSE 0
                END), 0) as total_obligations
                FROM program_sam_spending
                WHERE program_id IN ({placeholders})
            """, [fiscal_year] + regular_program_ids)

            total_category_obs += float(cursor.fetchone()['total_obligations'])

        # Get obligations for other programs
        if other_program_ids:
            placeholders = ','.join('?' * len(other_program_ids))
            cursor.execute(f"""
                SELECT COALESCE(SUM(outlays), 0) + COALESCE(SUM(forgone_revenue), 0) as total_other_obligation
                FROM other_program_spending
                WHERE fiscal_year = ?
                AND program_id IN ({placeholders})
            """, [fiscal_year] + other_program_ids)

            total_category_obs += float(cursor.fetchone()['total_other_obligation'])

        # Get subcategories with their stats
        cursor.execute("""
            SELECT
                c.name as title,
                c.id as category_id
            FROM category c
            WHERE c.parent_id = ?
            AND EXISTS (
                SELECT 1
                FROM program_to_category ptc
                WHERE ptc.category_id = c.id
                AND ptc.category_type = 'category'
            )
        """, (parent['id'],))

        subcats = []
        for subcat in cursor.fetchall():
            # Get programs for this subcategory
            cursor.execute("""
                SELECT DISTINCT p.id, p.program_type
                FROM program p
                JOIN program_to_category ptc ON p.id = ptc.program_id
                WHERE ptc.category_id = ?
                AND ptc.category_type = 'category'
            """, (subcat['category_id'],))

            subcat_programs = cursor.fetchall()

            # Split subcategory programs by type
            sub_regular_ids = [p['id'] for p in subcat_programs if p['program_type'] == 'assistance_listing']
            sub_other_ids = [p['id'] for p in subcat_programs if p['program_type'] != 'assistance_listing']

            # Calculate total obligations for subcategory
            subcat_total_obs = 0
            program_count = len(subcat_programs)

            # Get regular program obligations
            if sub_regular_ids:
                placeholders = ','.join('?' * len(sub_regular_ids))
                cursor.execute(f"""
                    SELECT COALESCE(SUM(CASE
                        WHEN fiscal_year = ? AND is_actual = 0
                        THEN amount
                        ELSE 0
                    END), 0) as total_obligations
                    FROM program_sam_spending
                    WHERE program_id IN ({placeholders})
                """, [fiscal_year] + sub_regular_ids)

                subcat_total_obs += float(cursor.fetchone()['total_obligations'])

            # Get other obligations
            if sub_other_ids:
                placeholders = ','.join('?' * len(sub_other_ids))
                cursor.execute(f"""
                    SELECT COALESCE(SUM(outlays), 0) + COALESCE(SUM(forgone_revenue), 0) as total_other_obligation
                    FROM other_program_spending
                    WHERE fiscal_year = ?
                    AND program_id IN ({placeholders})
                """, [fiscal_year] + sub_other_ids)

                subcat_total_obs += float(cursor.fetchone()['total_other_obligation'])

            subcats.append({
                'title': subcat['title'],
                'program_count': program_count,
                'total_obligations': subcat_total_obs
            })

        # Calculate category totals including both types of programs
        cursor.execute("""
            SELECT
                COUNT(DISTINCT p.id) as total_num_programs,
                COUNT(DISTINCT a1.agency_name) as total_num_agencies,
                COUNT(DISTINCT c_app.name) as total_num_applicant_types
            FROM program p
            JOIN program_to_category ptc ON p.id = ptc.program_id
            JOIN category c ON ptc.category_id = c.id
            LEFT JOIN agency a ON p.agency_id = a.id
            LEFT JOIN agency a1 ON a.tier_1_agency_id = a1.id
            LEFT JOIN program_to_category ptc_app ON p.id = ptc_app.program_id
                AND ptc_app.category_type = 'applicant'
            LEFT JOIN category c_app ON ptc_app.category_id = c_app.id
            WHERE c.parent_id = ?
            AND ptc.category_type = 'category'
        """, (parent['id'],))

        totals = cursor.fetchone()

        category_title = clean_string(parent['title'])

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
    ensure_directory_exists(output_dir)

    # Get all subcategories that have at least one program
    cursor.execute("""
        WITH subcategory_programs AS (
            SELECT
                c.id,
                COUNT(DISTINCT p.id) as program_count
            FROM category c
            JOIN program_to_category ptc ON c.id = ptc.category_id
            JOIN program p ON ptc.program_id = p.id
            WHERE c.type = 'category'
            AND ptc.category_type = 'category'
            AND c.parent_id IS NOT NULL
            GROUP BY c.id
            HAVING program_count > 0
        )
        SELECT DISTINCT
            c.id,
            c.name as title,
            c.parent_id,
            pc.name as parent_title
        FROM category c
        JOIN category pc ON c.parent_id = pc.id
        JOIN subcategory_programs sp ON c.id = sp.id
    """)

    subcategories = cursor.fetchall()
    for subcat in subcategories:
        # Get all programs with their types and spending data
        cursor.execute("""
            SELECT DISTINCT
                p.id,
                p.name as title,
                p.program_type,
                p.popular_name,
                a1.agency_name as agency_name
            FROM program p
            JOIN program_to_category ptc ON p.id = ptc.program_id
            LEFT JOIN agency a ON p.agency_id = a.id
            LEFT JOIN agency a1 ON a.tier_1_agency_id = a1.id
            WHERE ptc.category_id = ?
            AND ptc.category_type = 'category'
        """, (subcat['id'],))

        programs = cursor.fetchall()
        if not programs:
            continue

        # Split programs by type
        regular_program_ids = [p['id'] for p in programs if p['program_type'] == 'assistance_listing']
        other_program_ids = [p['id'] for p in programs if p['program_type'] != 'assistance_listing']

        # Initialize total obligations
        total_subcategory_obs = 0

        # Get obligations for regular programs
        program_obligations = {}
        if regular_program_ids:
            placeholders = ','.join('?' * len(regular_program_ids))
            cursor.execute(f"""
                SELECT program_id,
                    COALESCE(SUM(CASE
                        WHEN fiscal_year = ? AND is_actual = 0
                        THEN amount
                        ELSE 0
                    END), 0) as total_obs
                FROM program_sam_spending
                WHERE program_id IN ({placeholders})
                GROUP BY program_id
            """, [fiscal_year] + regular_program_ids)

            for row in cursor.fetchall():
                program_obligations[row['program_id']] = float(row['total_obs'])
                total_subcategory_obs += float(row['total_obs'])

        # Get obligations for other programs
        if other_program_ids:
            placeholders = ','.join('?' * len(other_program_ids))
            cursor.execute(f"""
                SELECT program_id,
                    COALESCE(SUM(outlays), 0) + COALESCE(SUM(forgone_revenue), 0) as total_obs
                FROM other_program_spending
                WHERE fiscal_year = ?
                AND program_id IN ({placeholders})
                GROUP BY program_id
            """, [fiscal_year] + other_program_ids)

            for row in cursor.fetchall():
                program_obligations[row['program_id']] = float(row['total_obs'])
                total_subcategory_obs += float(row['total_obs'])

        # Calculate subcategory totals
        program_ids = [p['id'] for p in programs]
        cursor.execute("""
            SELECT
                COUNT(DISTINCT p.id) as total_num_programs,
                COUNT(DISTINCT a1.agency_name) as total_num_agencies,
                COUNT(DISTINCT c_app.name) as total_num_applicant_types
            FROM program p
            JOIN program_to_category ptc ON p.id = ptc.program_id
            LEFT JOIN agency a ON p.agency_id = a.id
            LEFT JOIN agency a1 ON a.tier_1_agency_id = a1.id
            LEFT JOIN program_to_category ptc_app ON p.id = ptc_app.program_id
                AND ptc_app.category_type = 'applicant'
            LEFT JOIN category c_app ON ptc_app.category_id = c_app.id
            WHERE ptc.category_id = ?
            AND ptc.category_type = 'category'
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
            'programs': json.dumps([{
                'cfda': p['id'],
                'permalink': f"/program/{p['id']}",
                'title': p['title'],
                'popular_name': p['popular_name'],
                'agency': p['agency_name'] or 'Unspecified',
                'total_obs': program_obligations.get(p['id'], 0.0),
                'program_type': p['program_type']
            } for p in programs], separators=(',', ':'))
        }

        # Write subcategory markdown file
        file_path = os.path.join(output_dir,
            f"{convert_to_url_string(parent_title)}---{convert_to_url_string(subcategory_title)}.md")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('---\n')
            yaml.dump(subcategory_data, file, allow_unicode=True)
            file.write('---\n')

    print("Successfully generated sub-category markdown files")


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
            LEFT JOIN category pc ON c.parent_id = pc.id
            WHERE ptc.program_id = ?
            AND c.type = ptc.category_type
        """, (program['id'],))

        categories = cursor.fetchall()

        # Get obligations based on program type
        if program['program_type'] != 'assistance_listing':
            obligations = None
            other_program_spending = get_other_program_obligations(cursor, program['id'], fiscal_years)
            outlays = None
        else:
            obligations = get_assistance_program_obligations(cursor, program['id'], fiscal_years)
            other_program_spending = None
            outlays = get_outlays_data(cursor, program['id'], fiscal_years)

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

        # Create comprehensive program data
        program_data = {
            'id': program['id'],
            'name': program['name'],
            'popular_name': program['popular_name'],
            'objective': program['objective'],
            'sam_url': program['sam_url'],
            'usaspending_url': program['usaspending_url'],
            'grants_url': program['grants_url'],
            'top_agency_name': program['top_agency_name'],
            'sub_agency_name': program['sub_agency_name'],
            'assistance_types': sorted(list(program_categories['assistance'].values())),
            'beneficiary_types': sorted(list(program_categories['beneficiary'].values())),
            'applicant_types': sorted(list(program_categories['applicant'].values())),
            'categories': sorted(list(program_categories['categories'].values())),
            'obligations': obligations,
            'other_program_spending': other_program_spending,
            'outlays': outlays,
            'results': results,
            'authorizations': authorizations,
            'program_type': program['program_type'],
            'is_subpart_f': program['is_subpart_f'],
            'rules_regulations': program['rules_regulations']
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
        WHERE a1.is_cfo_act_agency = 1
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
            pc.id as id,
            pc.name as title,
            c.name as sub_title
        FROM program p
        JOIN program_to_category ptc ON p.id = ptc.program_id
        JOIN category c ON ptc.category_id = c.id
        JOIN category pc ON c.parent_id = pc.id
        WHERE c.type = 'category'
        AND c.type = ptc.category_type    
        ORDER BY pc.name, c.name
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

    print("Completed shared data creation")
    
    return {
        'cfo_agencies': sorted(cfo_agencies, key=lambda x: x['title']),
        'other_agencies': sorted(other_agencies, key=lambda x: x['title']),
        'applicant_types': applicant_types,
        'assistance_types': assistance_types,
        'beneficiary_types': beneficiary_types,
        'categories': sorted(categories, key=lambda x: x['title'])
    }

def generate_program_markdown_files(output_dir: str, programs_data: List[Dict[str, Any]], fiscal_years: list[str]):
    """Generate individual markdown files for each program using pre-generated data."""
    ensure_directory_exists(output_dir)

    for program in programs_data:
        # Create listing dictionary using pre-generated data
        listing = {
            'title': program['name'],
            'layout': 'program',
            'permalink': f"/program/{program['id']}.html",
            'fiscal_year': constants.FISCAL_YEAR,
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
            'sub-agency': program['sub_agency_name'] or 'N/A',
            'obligations': json.dumps(program['obligations'], separators=(',', ':')),
            'results': program['results'],
            'program_type': program['program_type'],
            'authorizations': [{'text': auth['text'], 'url': auth['url']} for auth in program['authorizations']],
            'is_subpart_f': program['is_subpart_f'],
            'rules_regulations': program['rules_regulations']
        }

        # Add obligations based on program type
        if program['program_type'] != 'assistance_listing':
            listing['other_program_spending'] = json.dumps(program['other_program_spending'], separators=(',', ':'))
            listing['obligations'] = None
            listing['outlays'] = None
        else:
            listing['obligations'] = json.dumps(program['obligations'], separators=(',', ':'))
            listing['outlays'] = json.dumps(program['outlays'], separators=(',', ':'))
            listing['other_program_spending'] = None

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
        'categories': shared_data['categories']
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write('---\n')
        yaml.dump(search_page, file, allow_unicode=True)
        file.write('---\n')
    print("Successfully generated search page")


def generate_home_page(output_path: str, shared_data: Dict[str, Any],
                       fiscal_year: str):
    """Generate the home page using pre-generated shared data."""
    page = {
        'title': 'Home',
        'layout': 'home',
        'permalink': '/',
        'fiscal_year': fiscal_year,
        'cfo_agencies': shared_data['cfo_agencies'],
        'other_agencies': shared_data['other_agencies'],
        'applicant_types': shared_data['applicant_types'],
        'program_types': shared_data['assistance_types'],
        'categories': shared_data['categories']
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
        # Calculate obligations based on program type
        if program['program_type'] != 'assistance_listing':
            # For other programs, sum outlays and forgone_revenue
            current_year_part_obligation = next(
                (tx for tx in program['other_program_spending'] if tx['x'] == fiscal_year),
                {'outlays': 0, 'forgone_revenue': 0}
            )
            current_year_obligation = current_year_part_obligation['outlays'] + current_year_part_obligation['forgone_revenue']
        else:
            # For assistance programs, use sam_actual
            current_year_obligation = next(
                (obl['sam_actual']
                for obl in program['obligations'] 
                if obl['x'] == fiscal_year), 
                0
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

        # Rest of the function remains the same...
        program_json = {
            'cfda': program['id'],
            'title': program['name'],
            'permalink': f"/program/{program['id']}",
            'obligations': float(current_year_obligation),
            'objectives': program['objective'],
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

    # Get unique program types and create mapping
    cursor.execute("""
        SELECT DISTINCT
            COALESCE(program_type, 'assistance_listing') as program_type
        FROM program
    """)
    program_types = [row['program_type'] for row in cursor.fetchall()]

    # Calculate overall obligations by program type
    obligations_by_type = []

    # Get all program IDs that are in categories
    cursor.execute("""
        SELECT DISTINCT p.id, p.program_type
        FROM program p
        JOIN program_to_category ptc ON p.id = ptc.program_id
        JOIN category c ON ptc.category_id = c.id
        WHERE c.type = 'category'
        AND ptc.category_type = 'category'
    """)
    all_categorized_programs = cursor.fetchall()

    # Group all programs by type
    programs_by_type = {prog_type: [] for prog_type in program_types}
    for prog in all_categorized_programs:
        prog_type = prog['program_type'] or 'assistance_listing'
        programs_by_type[prog_type].append(prog['id'])

    # Calculate obligations for each program type
    for prog_type, prog_ids in programs_by_type.items():
        if not prog_ids:
            continue

        if prog_type != 'assistance_listing':
            placeholders = ','.join('?' * len(prog_ids))
            cursor.execute(f"""
                SELECT SUM(total_other_obligation) as total_obs
                FROM (
                    SELECT DISTINCT program_id,
                           (outlays + forgone_revenue) as total_other_obligation
                    FROM other_program_spending
                    WHERE fiscal_year = ?
                    AND program_id IN ({placeholders})
                )
            """, [fiscal_year] + prog_ids)
        else:
            placeholders = ','.join('?' * len(prog_ids))
            cursor.execute(f"""
                SELECT SUM(amount) as total_obs
                FROM (
                    SELECT DISTINCT program_id, amount
                    FROM program_sam_spending
                    WHERE fiscal_year = ?
                    AND is_actual = 0
                    AND program_id IN ({placeholders})
                )
            """, [fiscal_year] + prog_ids)

        type_total = float(cursor.fetchone()['total_obs'] or 0)
        if type_total > 0:
            obligations_by_type.append({
                'title': constants.PROGRAM_TYPE_MAPPING.get(prog_type,
                                                            prog_type),
                'total_obs': type_total
            })

    # Get total number of unique programs
    cursor.execute("""
        SELECT COUNT(DISTINCT p.id) as total_programs
        FROM program p
        JOIN program_to_category ptc ON p.id = ptc.program_id
        JOIN category c ON ptc.category_id = c.id
        WHERE c.type = 'category'
        AND ptc.category_type = 'category'
    """)
    total_programs = cursor.fetchone()['total_programs']

    # Total obligations is sum of all program type obligations
    total_obs = sum(type_obj['total_obs'] for type_obj in obligations_by_type)

    # Calculate category stats
    category_stats = {}
    for category in categories:
        # Get programs for this category
        cursor.execute("""
            SELECT DISTINCT p.id, p.program_type
            FROM program p
            JOIN program_to_category ptc ON p.id = ptc.program_id
            JOIN category c ON ptc.category_id = c.id
            WHERE c.parent_id = (
                SELECT id FROM category WHERE name = ?
            )
            AND ptc.category_type = 'category'
        """, (category,))
        programs = cursor.fetchall()

        if programs:
            # Split programs by type and calculate obligations
            cat_programs_by_type = {prog_type: [] for prog_type in program_types}
            for prog in programs:
                prog_type = prog['program_type'] or 'assistance_listing'
                cat_programs_by_type[prog_type].append(prog['id'])

            # Calculate total obligations for category
            total_cat_obs = 0
            for prog_type, prog_ids in cat_programs_by_type.items():
                if not prog_ids:
                    continue

                if prog_type != 'assistance_listing':
                    placeholders = ','.join('?' * len(prog_ids))
                    cursor.execute(f"""
                        SELECT SUM(total_other_obligation) as total_obs
                        FROM (
                            SELECT DISTINCT program_id,
                                   (outlays + forgone_revenue) as total_other_obligation
                            FROM other_program_spending
                            WHERE fiscal_year = ?
                            AND program_id IN ({placeholders})
                        )
                    """, [fiscal_year] + prog_ids)
                else:
                    placeholders = ','.join('?' * len(prog_ids))
                    cursor.execute(f"""
                        SELECT SUM(amount) as total_obs
                        FROM (
                            SELECT DISTINCT program_id, amount
                            FROM program_sam_spending
                            WHERE fiscal_year = ?
                            AND is_actual = 0
                            AND program_id IN ({placeholders})
                        )
                    """, [fiscal_year] + prog_ids)

                type_total = float(cursor.fetchone()['total_obs'] or 0)
                total_cat_obs += type_total

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
        'obligations_by_type': obligations_by_type,
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
            'al_number',
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
            'obligations'
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
                json.dumps(program['obligations'], separators=(',', ':'))
            ])

    print(f"Generated CSV file with {len(programs_data)} programs")


try:
    conn = sqlite3.connect(full_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # programs_data = generate_program_data(cursor, FISCAL_YEARS)

    # shared_data = generate_shared_data(cursor)

    # generate_program_markdown_files(MARKDOWN_DIR, programs_data, FISCAL_YEARS)

    # generate_program_csv('../website/assets/files/all-program-data.csv', programs_data, FISCAL_YEARS)

    # search_path = os.path.join('../website', 'pages', 'search.md')
    # generate_search_page(search_path, shared_data, constants.FISCAL_YEAR)

    # category_path = os.path.join('../website', 'pages', 'category.md')
    # generate_category_page(cursor, programs_data, category_path, constants.FISCAL_YEAR)

    # home_path = os.path.join('../website', 'pages', 'home.md')
    # generate_home_page(home_path, shared_data, constants.FISCAL_YEAR)

    # programs_json_path = os.path.join('../indexer', 'programs-table.json')
    # generate_programs_table_json(programs_json_path, programs_data, constants.FISCAL_YEAR)

    # category_dir = os.path.join('../website', '_category')
    # generate_category_markdown_files(cursor, category_dir, constants.FISCAL_YEAR)

    # subcategory_dir = os.path.join('../website', '_subcategory')
    # generate_subcategory_markdown_files(cursor, subcategory_dir, constants.FISCAL_YEAR)

except sqlite3.Error as e:
    print(f"Database error occurred: {e}")
    raise e
except Exception as e:
    print(f"An error occurred: {e}")
    raise e
finally:
    if 'conn' in locals():
        conn.close()