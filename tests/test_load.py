"""
This tests our functions that generate markdown files for the static website.
These functions are what create all the program pages, category pages, etc.

KNOWN ISSUES:
1. clean_string doesn't normalize internal whitespace
2. Hardcoded database path in database connection
"""

import csv
import json
import os
import tempfile
from pathlib import Path
import yaml
import pytest
from unittest.mock import patch, mock_open, MagicMock, ANY

from data_processing import constants

# Mock the sqlite3.connect function
# This helps with error when connecting to non-existent database files
with patch('sqlite3.connect', return_value=MagicMock()):
    # Import the module
    from data_processing import load


@pytest.fixture(autouse=True)
def reset_load_caches():
    """Clear module-level lookup caches so tests do not share query results."""
    load.obligations_data = {}
    load.outlays_data = {}
    yield
    load.obligations_data = {}
    load.outlays_data = {}


class TestRecreateDirectory:

    @patch('os.path.isdir')
    @patch('shutil.rmtree')
    @patch('os.makedirs')
    def test_recreate_directory_new_dir(self, mock_makedirs, mock_rmtree, mock_isdir):
        """
        Test creating a directory that doesn't exist.
        Make sure output directories are available.
        """
        mock_isdir.return_value = False

        load.recreate_directory('/test/directory')

        mock_rmtree.assert_not_called()
        mock_makedirs.assert_called_once_with('/test/directory')

    @patch('os.path.isdir')
    @patch('shutil.rmtree')
    @patch('os.makedirs')
    def test_recreate_directory_existing_dir(self, mock_makedirs, mock_rmtree, mock_isdir):
        """Test replacing a directory that already exists."""
        mock_isdir.return_value = True

        load.recreate_directory('/test/directory')

        mock_rmtree.assert_called_once_with('/test/directory')
        mock_makedirs.assert_called_once_with('/test/directory')

class TestGetAssistanceProgramObligations:
    
    def test_get_assistance_program_obligations(self):
        """
        Test getting obligation data for assistance programs.
        This should collect data from both SAM.gov and USAspending.
        """
        result = load.get_assistance_program_obligations(
            _cursor_returning([
                _obligation_row('10.001', '2023', 1000000, 1200000),
                _obligation_row('10.001', '2024', 1000000, 1200000),
            ]),
            '10.001',
            ['2023', '2024'],
        )

        assert len(result) == 2  # Two fiscal years
        assert result[0]['x'] == '2023'
        assert result[0]['sam_actual'] == 1000000.0
        assert result[0]['usa_spending_actual'] == 1200000.0

class TestGetOtherProgramAmounts:
    
    def test_get_other_program_amounts_tax_expenditure(self):
        """
        Test getting amount data for tax expenditure programs.
        These have both outlays and forgone revenue.
        """
        result = load.get_other_program_amounts(
            _cursor_returning([
                _amount_row('TX001', '2023', 0, 0, 0, 2000000),
            ]),
            'TX001',
            ['2023'],
        )

        assert len(result) == 1
        assert result[0]['x'] == '2023'
        assert result[0]['outlays'] == 0.0
        assert result[0]['forgone_revenue'] == 2000000.0
    
    def test_get_other_program_amounts_interest(self):
        """
        Test getting amount data for interest programs.
        """
        result = load.get_other_program_amounts(
            _cursor_returning([
                _amount_row('I001', '2023', 5000000, 0, 5000000),
            ]),
            'I001',
            ['2023'],
        )

        assert len(result) == 1
        assert result[0]['x'] == '2023'
        assert result[0]['outlays'] == 5000000.0
        assert result[0]['forgone_revenue'] == 0.0

class TestGetAmounts:
    
    def test_get_amounts(self):
        """
        Test getting amount data for programs.
        This should return both outlays and their corresponding obligations.
        """
        result = load.get_amounts(
            _cursor_returning([
                _amount_row('10.001', '2023', 800000, 1000000, 800000),
                _amount_row('10.001', '2024', 800000, 1000000, 800000),
            ]),
            '10.001',
            ['2023', '2024'],
        )

        assert len(result) == 2  # Two fiscal years
        assert result[0]['x'] == '2023'
        assert result[0]['outlay'] == 800000.0
        assert result[0]['obligation'] == 1000000.0

class TestGetAssistanceListingExpenditures:
    
    def test_get_assistance_listing_expenditures_with_data(self):
        """
        Test getting expenditures for assistance listings with actual data.
        """
        program_obs, total_obs = load.get_assistance_listing_expenditures(
            _cursor_returning([
                _amount_row('10.001', '2023', 1000000, 1000000, 1000000),
                _amount_row('10.002', '2023', 2000000, 2000000, 2000000),
            ]),
            ['10.001', '10.002'],
            '2023',
        )

        assert len(program_obs) == 2  # Two programs
        assert program_obs['10.001'] == 1000000.0
        assert program_obs['10.002'] == 2000000.0
        assert total_obs == 3000000.0
    
    def test_get_assistance_listing_expenditures_empty(self):
        """Test handling of empty program list - should return empty results"""
        program_obs, total_obs = load.get_assistance_listing_expenditures(
            _cursor_returning([]), [], '2023')

        assert program_obs == {}
        assert total_obs == 0.0


class TestGenerateAgencyList:

    def test_generate_agency_list(self):
        """
        Test grouping programs by parent agency with expenditure totals.
        Programs without an agency name should appear as Unspecified.
        """
        fiscal_year = constants.LAST_COMPLETED_FISCAL_YEAR
        program_ids = [program['id'] for program in SAMPLE_PROGRAMS_DATA]

        result = load.generate_agency_list(
            _query_aware_cursor(_agency_list_fetchall),
            program_ids,
            fiscal_year,
        )

        totals_by_agency = {}
        counts_by_agency = {}
        for program in SAMPLE_PROGRAMS_DATA:
            agency_name = program['top_agency_name'] or 'Unspecified'
            counts_by_agency[agency_name] = counts_by_agency.get(agency_name, 0) + 1
            totals_by_agency[agency_name] = (
                totals_by_agency.get(agency_name, 0.0)
                + _lookup_expenditure(program['id'], fiscal_year)
            )

        assert result == sorted(
            [
                {
                    'title': agency_name,
                    'total_num_programs': counts_by_agency[agency_name],
                    'total_obs': totals_by_agency[agency_name],
                }
                for agency_name in totals_by_agency
            ],
            key=lambda item: (item['total_obs'], item['title']),
            reverse=True,
        )
        assert [agency['title'] for agency in result] == [
            'Department of Agriculture',
            'Unspecified',
        ]


class TestGenerateApplicantTypeList:
    
    def test_generate_applicant_type_list(self):
        """
        Test generating a list of applicant types with program counts.
        This is used for filtering on the website.
        """
        result = load.generate_applicant_type_list(
            _cursor_returning([
                {'title': 'State Government', 'total_num_programs': 10},
                {'title': 'Local Government', 'total_num_programs': 5},
            ]),
            ['10.001', '10.002'],
        )
        
        # Verify the results
        assert len(result) == 2
        assert result[0]['title'] == 'State Government'
        assert result[0]['total_num_programs'] == 10
        assert result[1]['title'] == 'Local Government'
        assert result[1]['total_num_programs'] == 5

class TestConvertToURLString:
    
    def test_convert_to_url_string(self):
        """
        Test URL string conversion.
        This is used for generating slugs/permalinks.
        """
        # Test various strings
        assert load.convert_to_url_string("Income Security") == "income-security"
        assert load.convert_to_url_string("Health & Human Services") == "health---human-services"
        assert load.convert_to_url_string("K-12 Education") == "k-12-education"
        assert load.convert_to_url_string("") == ""

class TestGetCategoriesHierarchy:
    
    def test_get_categories_hierarchy(self):
        
        result = load.get_categories_hierarchy(_cursor_returning([
            {'parent_id': 'education', 'parent_name': 'Education', 'sub_name': 'Higher Education'},
            {'parent_id': 'education', 'parent_name': 'Education', 'sub_name': 'K-12 Education'},
            {'parent_id': 'health', 'parent_name': 'Health', 'sub_name': 'Public Health'},
        ]))
        
        # Verify the results
        assert len(result) == 2  # Two parent categories
        
        # Check first category - Education
        assert result[0]['title'] == 'Education'
        assert result[0]['permalink'] == '/category/education'
        assert len(result[0]['subcategories']) == 2
        assert result[0]['subcategories'][0]['title'] == 'Higher Education'
        assert result[0]['subcategories'][1]['title'] == 'K-12 Education'
        
        # Check second category - Health
        assert result[1]['title'] == 'Health'
        assert result[1]['permalink'] == '/category/health'
        assert len(result[1]['subcategories']) == 1
        assert result[1]['subcategories'][0]['title'] == 'Public Health'

class TestGetImproperPaymentInfo:
    
    def test_get_improper_payment_info(self):
        """
        Test getting improper payment data for a program.
        """
        result = load.get_improper_payment_info(
            _cursor_returning([
                {
                    'improper_payment_program_name': 'Test Payment Program',
                    'agency': 'Department of Agriculture',
                    'outlays': 10000000,
                    'improper_payments': 500000,
                    'fiscal_year': 2025,
                    'start_date': '2024-10-01',
                    'end_date': '2025-09-30',
                    'insufficient_payment': 100000,
                    'slug': 'test-payment-program',
                }
            ]),
            '10.001',
        )

        assert len(result) == 1
        assert result[0]['name'] == 'Test Payment Program'
        assert result[0]['outlays'] == 10000000.0
        assert result[0]['improper_payments'] == 500000.0
        assert result[0]['insufficient_payment'] == 100000.0
        assert result[0]['start_date'] == '10-2024'
        assert result[0]['end_date'] == '09-2025'
        assert result[0]['fiscal_year'] == 2025
        assert result[0]['agency'] == 'Department of Agriculture'
        assert result[0]['slug'] == 'test-payment-program'


class TestCalculateImproperPaymentMetrics:

    def test_calculate_improper_payment_metrics(self):
        """
        Test aggregating improper payment rates, current-year details,
        and multiple-timeframe detection.
        """
        current_year = constants.PAYMENTACCURACY_FY_DATE
        prior_year = str(int(current_year) - 1)

        program_a_prior = {
            'name': 'Test Payment Program',
            'outlays': 10000000.0,
            'improper_payments': 200000.0,
            'insufficient_payment': 50000.0,
            'start_date': '10-2023',
            'end_date': '09-2024',
            'fiscal_year': int(prior_year),
            'agency': 'Department of Agriculture',
            'slug': 'test-payment-program',
        }
        program_a_current = {
            'name': 'Test Payment Program',
            'outlays': 10000000.0,
            'improper_payments': 500000.0,
            'insufficient_payment': 100000.0,
            'start_date': '10-2024',
            'end_date': '09-2025',
            'fiscal_year': int(current_year),
            'agency': 'Department of Agriculture',
            'slug': 'test-payment-program',
        }
        program_b_current = {
            'name': 'Other Payment Program',
            'outlays': 20000000.0,
            'improper_payments': 400000.0,
            'insufficient_payment': 20000.0,
            'start_date': '01-2025',
            'end_date': '12-2025',
            'fiscal_year': int(current_year),
            'agency': 'Department of Education',
            'slug': 'other-payment-program',
        }
        program_c_prior = {
            'name': 'Retired Payment Program',
            'outlays': 5000000.0,
            'improper_payments': 100000.0,
            'insufficient_payment': 0.0,
            'start_date': '10-2023',
            'end_date': '09-2024',
            'fiscal_year': int(prior_year),
            'agency': 'Department of Health',
            'slug': 'retired-payment-program',
        }

        result = load.calculate_improper_payment_metrics([
            program_a_prior,
            program_a_current,
            program_b_current,
            program_c_prior,
        ])

        assert result == {
            'is_multiple': True,
            'improper_payments_total': 900000.0,
            'improper_payments_percent': 3.0,
            'current_year_details': [
                program_a_current,
                program_b_current,
                {
                    'name': 'Retired Payment Program',
                    'outlays': None,
                    'improper_payments': None,
                    'insufficient_payment': None,
                    'start_date': None,
                    'end_date': None,
                    'fiscal_year': current_year,
                    'agency': 'Department of Health',
                    'slug': 'retired-payment-program',
                },
            ],
            'sparkline': [
                {'x': prior_year, 'rate': 2.0},
                {'x': current_year, 'rate': 3.0},
            ],
        }


class TestGetRelatedPrograms:

    def test_get_related_programs(self):
        """
        Test finding other programs that share improper payment mappings.
        Duplicate names and shared mappings should not create duplicate results.
        """
        mock_cursor = _query_aware_cursor(_related_programs_fetchall)
        result = load.get_related_programs(
            mock_cursor,
            [
                {'name': 'Test Payment Program'},
                {'name': 'Test Payment Program'},
                {'name': 'Other Payment Program'},
            ],
            '10.001',
        )

        assert mock_cursor.execute.call_count == 2
        mock_cursor.execute.assert_any_call(ANY, ('Test Payment Program', '10.001'))
        mock_cursor.execute.assert_any_call(ANY, ('Other Payment Program', '10.001'))
        assert result == [
            {
                'id': '10.002',
                'name': 'Related Program',
                'permalink': '/program/10.002',
            },
            {
                'id': '10.003',
                'name': 'Another Related Program',
                'permalink': '/program/10.003',
            },
            {
                'id': 'C.1',
                'name': 'Contracts Program',
                'permalink': '/program/C.1',
            },
        ]


FISCAL_YEARS = ['2024', constants.LAST_COMPLETED_FISCAL_YEAR]
ASSISTANCE_TYPES = ['Formula Grants']
BENEFICIARY_TYPES = ['Individual/Family']
APPLICANT_TYPES = ['State Government']
PROGRAM_CATEGORIES = ['Education - Higher Education']
GWO = {
    'gwo': 'Increase educational attainment',
    'permalink': '/gwo/GWO_1_2',
}
ALL_GWO_ROWS = [
    {
        'id': 'GWO.1#2',
        'title': GWO['gwo'],
        'definition': 'Increase educational attainment across the population',
        'focus_area': 'Higher Education',
        'category': 'Education',
    },
    {
        'id': 'GWO.9#9',
        'title': 'Unassigned GWO',
        'definition': 'A government-wide objective with no program mapping',
    },
]
ASSIGNED_GWO_ID_ROWS = [{'gwo_id': ALL_GWO_ROWS[0]['id']}]
PONS = [
    {'pon': 'Improve student outcomes', 'permalink': '/pon/PON_1_2'}
]
ALL_PON_ROWS = [
    {
        'id': 'PON.1#2',
        'title': PONS[0]['pon'],
        'definition': 'Improve student outcomes in higher education',
        'focus_area': 'Higher Education',
        'category': 'Education',
    },
    {
        'id': 'PON.9#9',
        'title': 'Unassigned PON',
        'definition': 'A program outcome with no program mapping',
    },
]
TOTAL_PON_COUNT = len(ALL_PON_ROWS)
SPARKLINE = [{'x': '2024', 'rate': 1.5}]
RELATED_PROGRAMS = [
    {'id': '10.002', 'name': 'Related Program', 'permalink': '/program/10.002'}
]

ASSISTANCE_OBLIGATIONS = [
    {
        'x': '2024',
        'sam_estimate': 0.0,
        'sam_actual': 900000.0,
        'usa_spending_actual': 950000.0,
    },
    {
        'x': constants.LAST_COMPLETED_FISCAL_YEAR,
        'sam_estimate': 0.0,
        'sam_actual': 1000000.0,
        'usa_spending_actual': 1200000.0,
    },
]
ASSISTANCE_OUTLAYS = [
    {
        'x': '2024',
        'outlay': 700000.0,
        'obligation': 900000.0,
        'expenditure': 700000.0,
        'forgone_revenue': 0.0,
    },
    {
        'x': constants.LAST_COMPLETED_FISCAL_YEAR,
        'outlay': 800000.0,
        'obligation': 1000000.0,
        'expenditure': 800000.0,
        'forgone_revenue': 0.0,
    },
]
CONTRACTS_OUTLAYS = [
    {
        'x': '2024',
        'outlay': 2000000.0,
        'obligation': 2500000.0,
        'expenditure': 2000000.0,
        'forgone_revenue': 0.0,
    },
    {
        'x': constants.LAST_COMPLETED_FISCAL_YEAR,
        'outlay': 2100000.0,
        'obligation': 2600000.0,
        'expenditure': 2100000.0,
        'forgone_revenue': 0.0,
    },
]
GOVERNMENT_SERVICE_OUTLAYS = [
    {
        'x': '2024',
        'outlay': 3000000.0,
        'obligation': 3500000.0,
        'expenditure': 3000000.0,
        'forgone_revenue': 0.0,
    },
    {
        'x': constants.LAST_COMPLETED_FISCAL_YEAR,
        'outlay': 3100000.0,
        'obligation': 3600000.0,
        'expenditure': 3100000.0,
        'forgone_revenue': 0.0,
    },
]
INTEREST_SPENDING = [
    {'x': '2024', 'outlays': 5000000.0, 'forgone_revenue': 0.0},
    {
        'x': constants.LAST_COMPLETED_FISCAL_YEAR,
        'outlays': 5100000.0,
        'forgone_revenue': 0.0,
    },
]
TAX_SPENDING = [
    {'x': '2024', 'outlays': 0.0, 'forgone_revenue': 4000000.0},
    {
        'x': constants.LAST_COMPLETED_FISCAL_YEAR,
        'outlays': 0.0,
        'forgone_revenue': 4100000.0,
    },
]


def _program_row(program_id, name, program_type, **overrides):
    data = {
        'id': program_id,
        'name': name,
        'popular_name': None,
        'objective': f'{name} objective',
        'sam_url': None,
        'usaspending_url': None,
        'grants_url': None,
        'program_type': program_type,
        'agency_id': 100000000,
        'top_agency_name': 'Department of Agriculture',
        'sub_agency_name': None,
        'is_subpart_f': 0,
        'rules_regulations': None,
    }
    data.update(overrides)
    return data


def _obligation_row(program_id, year, sam_actual, usa_spending_actual, sam_estimate=0):
    return {
        'id': program_id,
        'fiscal_year': year,
        'sam_estimate': sam_estimate,
        'sam_actual': sam_actual,
        'usa_spending_actual': usa_spending_actual,
    }


def _amount_row(program_id, year, outlay, obligation, expenditure, forgone_revenue=0):
    return {
        'id': program_id,
        'fiscal_year': year,
        'outlay': outlay,
        'obligation': obligation,
        'expenditure': expenditure,
        'forgone_revenue': forgone_revenue,
    }


def _program_page_data(program_id, name, program_type, **overrides):
    data = {
        'id': program_id,
        'name': name,
        'popular_name': None,
        'objective': f'{name} objective',
        'sam_url': 'https://sam.gov/example',
        'usaspending_url': 'https://usaspending.gov/example',
        'grants_url': 'https://grants.gov/example',
        'assistance_types': ASSISTANCE_TYPES,
        'beneficiary_types': BENEFICIARY_TYPES,
        'applicant_types': APPLICANT_TYPES,
        'categories': PROGRAM_CATEGORIES,
        'top_agency_name': 'Department of Agriculture',
        'agency_id': 100000000,
        'sub_agency_name': None,
        'obligations': None,
        'outlays': None,
        'other_program_spending': None,
        'results': [{'year': '2024', 'description': 'Sample result'}],
        'program_type': program_type,
        'authorizations': [{'text': 'Sample Act', 'url': 'https://example.com/act'}],
        'is_subpart_f': 0,
        'rules_regulations': 'Sample rules',
        'improper_payment_metrics': {
            'current_year_details': [],
            'improper_payments_total': 0,
            'improper_payments_percent': 0,
            'is_multiple': False,
            'sparkline': [],
        },
        'related_programs': [],
        'headline_amount': 0,
        'gwo': None,
        'pons': [],
    }
    data.update(overrides)
    return data


def _obligation_lookup_rows(program_id, obligations):
    return [
        _obligation_row(
            program_id,
            item['x'],
            item['sam_actual'],
            item['usa_spending_actual'],
            item.get('sam_estimate', 0),
        )
        for item in obligations
    ]


def _amount_lookup_rows_from_outlays(program_id, outlays):
    return [
        _amount_row(
            program_id,
            item['x'],
            item['outlay'],
            item['obligation'],
            item['expenditure'],
            item.get('forgone_revenue', 0),
        )
        for item in outlays
    ]


def _amount_lookup_rows_from_other_spending(program_id, other_spending):
    return [
        _amount_row(
            program_id,
            item['x'],
            item['outlays'],
            0,
            item['outlays'],
            item.get('forgone_revenue', 0),
        )
        for item in other_spending
    ]


def _cursor_returning(rows):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = rows
    return mock_cursor


def _query_aware_cursor(fetchall_for_sql, fetchone_for_sql=None):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    def execute_side_effect(query, params=None):
        sql = ' '.join(query.split())
        mock_cursor.fetchall.return_value = fetchall_for_sql(sql, params)
        if fetchone_for_sql is not None:
            mock_cursor.fetchone.return_value = fetchone_for_sql(sql, params)

    mock_cursor.execute.side_effect = execute_side_effect
    return mock_cursor


def _load_program_markdown(path):
    with open(path, encoding='utf-8') as file:
        content = file.read()
    assert content.startswith('---\n')
    assert content.endswith('---\n')
    return yaml.safe_load(content.split('---', 2)[1])


def _csv_obligations(obligations):
    return [
        {
            'x': obl['x'],
            'sam_spending': obl['sam_actual'],
            'usa_spending_actual': obl['usa_spending_actual'],
        }
        for obl in obligations
    ]


def _csv_other_expenditures(other_program_spending):
    return [
        {
            'x': spend['x'],
            'outlays': spend['outlays'],
            **(
                {'revenue_losses': spend['forgone_revenue']}
                if 'forgone_revenue' in spend
                else {}
            ),
        }
        for spend in other_program_spending
    ]


SAMPLE_PROGRAMS_DATA = [
    _program_page_data(
        '10.001',
        'Assistance Program',
        'assistance_listing',
        popular_name='Popular Name',
        sub_agency_name='Food and Nutrition Service',
        obligations=ASSISTANCE_OBLIGATIONS,
        outlays=ASSISTANCE_OUTLAYS,
        headline_amount=800000.0,
        gwo=GWO,
        pons=PONS,
        improper_payment_metrics={
            'current_year_details': [
                {'name': 'Test Payment Program', 'outlays': 10000000.0}
            ],
            'improper_payments_total': 500000,
            'improper_payments_percent': 5.0,
            'is_multiple': False,
            'sparkline': SPARKLINE,
        },
        related_programs=RELATED_PROGRAMS,
    ),
    _program_page_data(
        'C.1',
        'Contracts Program',
        'contracts',
        top_agency_name=None,
        outlays=CONTRACTS_OUTLAYS,
        headline_amount=2100000.0,
    ),
    _program_page_data(
        'S.1',
        'Government Service Program',
        'government_service',
        outlays=GOVERNMENT_SERVICE_OUTLAYS,
        headline_amount=3100000.0,
    ),
    _program_page_data(
        'I.1',
        'Interest Program',
        'interest',
        other_program_spending=INTEREST_SPENDING,
        headline_amount=5100000.0,
    ),
    _program_page_data(
        'TX.1',
        'Tax Expenditure Program',
        'tax_expenditure',
        other_program_spending=TAX_SPENDING,
        headline_amount=4100000.0,
    ),
]
SAMPLE_PROGRAMS_BY_ID = {program['id']: program for program in SAMPLE_PROGRAMS_DATA}
GOVERNMENT_WIDE_SPENDING_TOTAL = sum(
    program['headline_amount'] for program in SAMPLE_PROGRAMS_DATA
)

PROGRAM_DB_ROWS = [
    _program_row(program['id'], program['name'], program['program_type'])
    for program in SAMPLE_PROGRAMS_DATA
]
OBLIGATION_LOOKUP_ROWS = _obligation_lookup_rows('10.001', ASSISTANCE_OBLIGATIONS)
AMOUNT_LOOKUP_ROWS = (
    _amount_lookup_rows_from_outlays('10.001', ASSISTANCE_OUTLAYS)
    + _amount_lookup_rows_from_outlays('C.1', CONTRACTS_OUTLAYS)
    + _amount_lookup_rows_from_outlays('S.1', GOVERNMENT_SERVICE_OUTLAYS)
    + _amount_lookup_rows_from_other_spending('I.1', INTEREST_SPENDING)
    + _amount_lookup_rows_from_other_spending('TX.1', TAX_SPENDING)
)

EXPECTED_SHARED_DATA = {
    'cfo_agencies': [
        {
            'title': 'Department of Agriculture',
            'sub_categories': [
                {'title': 'Food and Nutrition Service'},
                {'title': 'Unspecified'},
            ],
        },
        {'title': 'Department of the Treasury'},
    ],
    'other_agencies': [
        {
            'title': 'Smithsonian Institution',
            'sub_categories': [{'title': 'Smithsonian Museums'}],
        }
    ],
    'applicant_types': [{'title': title} for title in ['Local Government', 'State Government']],
    'assistance_types': [
        {'title': title} for title in ['Formula Grants', 'Project Grants']
    ],
    'beneficiary_types': [{'title': title} for title in BENEFICIARY_TYPES],
    'categories': [
        {
            'title': 'Education',
            'sub_categories': [
                {'title': 'Higher Education'},
                {'title': 'K-12 Education'},
            ],
        },
        {
            'title': 'Health',
            'sub_categories': [{'title': 'Public Health'}],
        },
    ],
    'gwo_options': [{'title': GWO['gwo']}],
    'pon_options': [{'title': PONS[0]['pon']}],
}

CATEGORY_PAGE_AGENCIES = [
    {
        'title': 'Department of Agriculture',
        'total_num_programs': 1,
        'total_obs': SAMPLE_PROGRAMS_BY_ID['10.001']['headline_amount'],
    }
]
CATEGORY_PAGE_APPLICANT_TYPES = [
    {'title': 'State Government', 'total_num_programs': 1}
]
CATEGORIES_HIERARCHY = [
    {
        'title': 'Education',
        'permalink': '/category/education',
        'subcategories': [
            {
                'title': 'Higher Education',
                'permalink': '/category/education/higher-education',
            },
            {
                'title': 'K-12 Education',
                'permalink': '/category/education/k-12-education',
            },
        ],
    }
]


def _expenditures_from_sample(cursor, program_ids, fiscal_year):
    program_obs = {}
    for program_id in program_ids:
        program = SAMPLE_PROGRAMS_BY_ID.get(program_id)
        if program:
            program_obs[program_id] = float(program['headline_amount'])
    return program_obs, float(sum(program_obs.values()))


def _amounts_from_sample(cursor, program_id, fiscal_years):
    program = SAMPLE_PROGRAMS_BY_ID.get(program_id)
    if not program:
        return []
    return program.get('outlays') or []


def _gwo_pon_related_program_rows():
    return [
        {
            'id': program['id'],
            'name': program['name'],
            'agency_name': program['top_agency_name'],
            'program_type': program['program_type'],
        }
        for program in (
            SAMPLE_PROGRAMS_BY_ID['10.001'],
            SAMPLE_PROGRAMS_BY_ID['C.1'],
        )
    ]


def _where_used_from_sample(program_ids, fiscal_year):
    where_used = []
    for program_id in program_ids:
        program = SAMPLE_PROGRAMS_BY_ID[program_id]
        spending = program.get('outlays') or []
        expenditure_amount = next(
            (
                item.get('expenditure', 0.0)
                for item in spending
                if item.get('x') == fiscal_year
            ),
            0.0,
        )
        where_used.append(
            {
                'permalink': f"/program/{program['id']}",
                'name': program['name'],
                'agency': program['top_agency_name'] or 'Unspecified',
                'program_type': program['program_type'],
                'expenditure_amount': expenditure_amount,
            }
        )
    return where_used


def _agency_list_from_program_ids(cursor, program_ids, fiscal_year):
    if not program_ids:
        return []
    return CATEGORY_PAGE_AGENCIES


def _applicant_type_list_from_program_ids(cursor, program_ids):
    if not program_ids:
        return []
    return CATEGORY_PAGE_APPLICANT_TYPES


def _empty_fetchall(sql, params=None):
    return []


def _amount_lookup_fetchall(sql, params=None):
    if 'FROM program_amounts_lookup' in sql:
        return AMOUNT_LOOKUP_ROWS
    return []


def _agency_list_fetchall(sql, params=None):
    if 'FROM program_amounts_lookup' in sql:
        return _amount_lookup_fetchall(sql, params)
    if 'a1.agency_name as title' in sql:
        ids = set(params or [])
        return [
            {
                'title': program['top_agency_name'],
                'program_id': program['id'],
                'program_type': program['program_type'],
            }
            for program in SAMPLE_PROGRAMS_DATA
            if program['id'] in ids
        ]
    return []


def _related_programs_fetchall(sql, params=None):
    name = params[0] if params else None
    return {
        'Test Payment Program': [
            {'id': '10.002', 'name': 'Related Program'},
            {'id': 'C.1', 'name': 'Contracts Program'},
        ],
        'Other Payment Program': [
            {'id': 'C.1', 'name': 'Contracts Program'},
            {'id': '10.003', 'name': 'Another Related Program'},
        ],
    }.get(name, [])


def _taxonomy_totals_fetchone(sql, params=None):
    if 'COUNT(DISTINCT ptl.program_id)' not in sql:
        return None
    if params and params[0] == 'k12':
        return {
            'total_num_programs': 0,
            'total_num_agencies': 0,
            'total_num_applicant_types': 0,
        }
    return {
        'total_num_programs': 1,
        'total_num_agencies': 1,
        'total_num_applicant_types': 1,
    }


def _program_data_fetchall(sql, params=None):
    if 'FROM program p' in sql:
        return PROGRAM_DB_ROWS
    if 'FROM program_amounts_lookup' in sql and 'sam_actual_obligation' in sql:
        return OBLIGATION_LOOKUP_ROWS
    if 'FROM program_amounts_lookup' in sql:
        return _amount_lookup_fetchall(sql, params)
    return []


def _lookup_expenditure(program_id, fiscal_year):
    for row in AMOUNT_LOOKUP_ROWS:
        if row['id'] == program_id and str(row['fiscal_year']) == str(fiscal_year):
            return float(row['expenditure'])
    return 0.0


def _category_page_fetchall(sql, params=None):
    if 'FROM program_amounts_lookup' in sql:
        return _amount_lookup_fetchall(sql, params)
    if 'as parent_id' in sql:
        return [
            {
                'parent_id': 'education',
                'parent_name': 'Education',
                'sub_name': 'Higher Education',
            },
            {
                'parent_id': 'education',
                'parent_name': 'Education',
                'sub_name': 'K-12 Education',
            },
        ]
    if 'WHERE c.category = ?' in sql:
        if params and params[0] == 'Education':
            assistance = SAMPLE_PROGRAMS_BY_ID['10.001']
            return [
                {
                    'id': assistance['id'],
                    'program_type': assistance['program_type'],
                }
            ]
        return []
    if 'as program_type' in sql:
        ids = set(params or [])
        return [
            {'id': row['id'], 'program_type': row['program_type']}
            for row in PROGRAM_DB_ROWS
            if row['id'] in ids
        ]
    if 'FROM program' in sql:
        return [{'id': row['id']} for row in PROGRAM_DB_ROWS]
    return []


def _shared_data_fetchall(sql, params=None):
    agency_id = params[0] if params else None
    if 'is_cfo_act_agency = 1' in sql:
        return [
            {'id': 100000000, 'title': 'Department of Agriculture'},
            {'id': 200000000, 'title': 'Department of the Treasury'},
        ]
    if 'is_cfo_act_agency = 0' in sql:
        return [{'id': 300000000, 'title': 'Smithsonian Institution'}]
    if 'GROUP_CONCAT(p.id)' in sql:
        return {
            100000000: [
                {
                    'title': 'Food and Nutrition Service',
                    'program_ids': '10.001,10.002',
                }
            ],
            300000000: [{'title': 'Smithsonian Museums', 'program_ids': 'S.1'}],
        }.get(agency_id, [])
    if 'a.tier_2_agency_id IS NULL' in sql:
        return {
            100000000: [{'id': '10.999'}],
            300000000: [],
        }.get(agency_id, [])
    if 'JOIN agency a2 ON a.tier_2_agency_id = a2.id' in sql:
        return {
            100000000: [{'title': 'Food and Nutrition Service'}],
            200000000: [],
            300000000: [{'title': 'Smithsonian Museums'}],
        }.get(agency_id, [])
    if "c.type = 'applicant'" in sql:
        return EXPECTED_SHARED_DATA['applicant_types']
    if 'assistance_names' in sql:
        return EXPECTED_SHARED_DATA['assistance_types']
    if "c.type = 'beneficiary'" in sql:
        return EXPECTED_SHARED_DATA['beneficiary_types']
    if 'taxonomy_category' in sql:
        return [
            {
                'id': 'education',
                'title': 'Education',
                'sub_title': 'Higher Education',
            },
            {
                'id': 'education',
                'title': 'Education',
                'sub_title': 'K-12 Education',
            },
            {
                'id': 'health',
                'title': 'Health',
                'sub_title': 'Public Health',
            },
        ]
    if 'FROM gwo' in sql:
        return EXPECTED_SHARED_DATA['gwo_options']
    if 'FROM pon' in sql:
        return EXPECTED_SHARED_DATA['pon_options']
    return []


def _taxonomy_page_fetchall(sql, params=None):
    if 'FROM program_to_gwo' in sql:
        return ASSIGNED_GWO_ID_ROWS
    if 'FROM gwo' in sql:
        return ALL_GWO_ROWS
    return []


def _about_page_fetchone(sql, params=None):
    if 'FROM program_amounts_lookup' in sql:
        return {'total': GOVERNMENT_WIDE_SPENDING_TOTAL}
    if 'FROM gwo' in sql:
        return {'ct': len(ALL_GWO_ROWS)}
    if 'FROM pon' in sql:
        return {'ct': TOTAL_PON_COUNT}
    return None


def _category_markdown_fetchall(sql, params=None):
    assistance = SAMPLE_PROGRAMS_BY_ID['10.001']
    if 'COUNT(DISTINCT ptl.program_id)' in sql:
        return []
    if 'taxonomy_category.category AS title' in sql:
        return [{'title': 'Education', 'id': 'edu'}]
    if 'AS category_id' in sql:
        return [
            {'title': 'Higher Education', 'category_id': 'he'},
            {'title': 'K-12 Education', 'category_id': 'k12'},
        ]
    if 'taxonomy_category_id = ?' in sql:
        return [
            {
                'id': assistance['id'],
                'program_type': assistance['program_type'],
            }
        ]
    if 'taxonomy_focus_area_id = ?' in sql:
        if params and params[0] == 'he':
            return [
                {
                    'id': assistance['id'],
                    'program_type': assistance['program_type'],
                }
            ]
        return []
    return []


def _subcategory_markdown_fetchall(sql, params=None):
    assistance = SAMPLE_PROGRAMS_BY_ID['10.001']
    if 'COUNT(DISTINCT ptl.program_id)' in sql:
        return []
    if 'AS parent_title' in sql:
        return [
            {
                'id': 'he',
                'title': 'Higher Education',
                'parent_id': 'edu',
                'parent_title': 'Education',
            },
            {
                'id': 'k12',
                'title': 'K-12 Education',
                'parent_id': 'edu',
                'parent_title': 'Education',
            },
        ]
    if 'popular_name' in sql:
        if params and params[0] == 'he':
            return [
                {
                    'id': assistance['id'],
                    'title': assistance['name'],
                    'program_type': assistance['program_type'],
                    'popular_name': assistance['popular_name'],
                    'agency_name': assistance['top_agency_name'],
                }
            ]
        return []
    return []


def _gwo_markdown_fetchall(sql, params=None):
    assigned = ALL_GWO_ROWS[0]
    if 'gwo.gwo_definition' in sql:
        return [
            {
                'id': assigned['id'],
                'focus_area': assigned['focus_area'],
                'category': assigned['category'],
                'gwo': assigned['title'],
                'gwo_definition': assigned['definition'],
            }
        ]
    if 'WHERE gwo_id = ?' in sql:
        return _gwo_pon_related_program_rows()
    return []


def _pon_markdown_fetchall(sql, params=None):
    assigned = ALL_PON_ROWS[0]
    if 'pon.pon_definition' in sql:
        return [
            {
                'id': assigned['id'],
                'focus_area': assigned['focus_area'],
                'category': assigned['category'],
                'pon2': assigned['title'],
                'pon_definition': assigned['definition'],
            }
        ]
    if 'pon_id = ?' in sql:
        return _gwo_pon_related_program_rows()
    return []


class TestGenerateProgramData:

    @patch.object(load, 'get_related_programs', return_value=[])
    @patch.object(load, 'get_improper_payment_info', return_value=[])
    def test_generate_program_data(self, mock_ip_info, mock_related):
        """
        Test assembling program page data for each program type.
        Obligations, outlays, and other program spending should follow
        the program-type rules in generate_program_data.
        """
        result = load.generate_program_data(
            _query_aware_cursor(_program_data_fetchall), FISCAL_YEARS
        )
        programs_by_id = {program['id']: program for program in result}

        assert set(programs_by_id) == set(SAMPLE_PROGRAMS_BY_ID)

        for program_id, expected in SAMPLE_PROGRAMS_BY_ID.items():
            actual = programs_by_id[program_id]
            assert actual['program_type'] == expected['program_type']
            assert actual['obligations'] == expected['obligations']
            assert actual['outlays'] == expected['outlays']
            assert actual['other_program_spending'] == expected['other_program_spending']


class TestGenerateSharedData:

    def test_generate_shared_data(self):
        """
        Test assembling shared filter data used across website pages.
        """
        result = load.generate_shared_data(
            _query_aware_cursor(_shared_data_fetchall)
        )
        assert result == EXPECTED_SHARED_DATA


class TestGenerateSearchPage:

    def test_generate_search_page(self):
        """
        Test writing the search page from shared filter data.
        """
        fiscal_year = constants.LAST_COMPLETED_FISCAL_YEAR

        with tempfile.TemporaryDirectory() as output_dir:
            output_path = os.path.join(output_dir, 'search.md')
            load.generate_search_page(output_path, EXPECTED_SHARED_DATA, fiscal_year)

            page = _load_program_markdown(output_path)
            search_filters = {
                key: value
                for key, value in EXPECTED_SHARED_DATA.items()
                if key != 'pon_options'
            }
            assert page == {
                'title': 'Program search',
                'layout': 'search',
                'permalink': '/search.html',
                'fiscal_year': fiscal_year,
                **search_filters,
            }


class TestGenerateTaxonomyPage:

    def test_generate_taxonomy_page(self):
        """
        Test writing the taxonomy page with permalinks only for assigned GWOs.
        """
        with tempfile.TemporaryDirectory() as output_dir:
            output_path = os.path.join(output_dir, 'taxonomy.md')
            load.generate_taxonomy_page(
                _query_aware_cursor(_taxonomy_page_fetchall),
                output_path,
                EXPECTED_SHARED_DATA,
            )

            page = _load_program_markdown(output_path)
            assigned_gwo = ALL_GWO_ROWS[0]
            unassigned_gwo = ALL_GWO_ROWS[1]
            assert page == {
                'layout': 'taxonomy',
                'title': 'FPI Taxonomy',
                'permalink': '/about/taxonomy',
                'categories': EXPECTED_SHARED_DATA['categories'],
                'gwo_options': [
                    {
                        'title': assigned_gwo['title'],
                        'definition': assigned_gwo['definition'],
                        'permalink': '/gwo/GWO_1_2',
                    },
                    {
                        'title': unassigned_gwo['title'],
                        'definition': unassigned_gwo['definition'],
                    },
                ],
            }


class TestGenerateAboutMarkdownFiles:

    def test_generate_about_markdown_files(self):
        """
        Test writing about-fpi.md and about-terms.md.
        """
        fiscal_year = constants.LAST_COMPLETED_FISCAL_YEAR

        with tempfile.TemporaryDirectory() as output_dir:
            load.generate_about_markdown_files(
                _query_aware_cursor(_empty_fetchall, _about_page_fetchone),
                output_dir,
                SAMPLE_PROGRAMS_DATA,
                fiscal_year,
            )

            about_fpi = _load_program_markdown(
                os.path.join(output_dir, 'about-fpi.md')
            )
            assert about_fpi == {
                'title': 'About the FPI',
                'layout': 'about-fpi',
                'permalink': '/about/fpi',
                'fiscal_year': fiscal_year,
                'spending_total': GOVERNMENT_WIDE_SPENDING_TOTAL,
            }

            about_terms = _load_program_markdown(
                os.path.join(output_dir, 'about-terms.md')
            )
            assert about_terms == {
                'title': 'FPI Data, Terms & Concepts',
                'layout': 'about-terms',
                'permalink': '/about/terms',
                'gwo_count': len(ALL_GWO_ROWS),
                'pon_count': TOTAL_PON_COUNT,
            }


class TestGenerateHomePage:

    def test_generate_home_page(self):
        """
        Test writing the home page with government-wide totals and shared filters.
        """
        fiscal_year = constants.LAST_COMPLETED_FISCAL_YEAR

        with tempfile.TemporaryDirectory() as output_dir:
            output_path = os.path.join(output_dir, 'home.md')
            load.generate_home_page(
                _query_aware_cursor(_empty_fetchall, _about_page_fetchone),
                output_path,
                SAMPLE_PROGRAMS_DATA,
                EXPECTED_SHARED_DATA,
                fiscal_year,
            )

            page = _load_program_markdown(output_path)
            agencies_count = (
                len(EXPECTED_SHARED_DATA['cfo_agencies'])
                + len(EXPECTED_SHARED_DATA['other_agencies'])
            )
            assert page == {
                'title': 'Home',
                'layout': 'home',
                'permalink': '/',
                'fiscal_year': fiscal_year,
                'cfo_agencies': EXPECTED_SHARED_DATA['cfo_agencies'],
                'other_agencies': EXPECTED_SHARED_DATA['other_agencies'],
                'applicant_types': EXPECTED_SHARED_DATA['applicant_types'],
                'program_types': EXPECTED_SHARED_DATA['assistance_types'],
                'categories': EXPECTED_SHARED_DATA['categories'],
                'programs_count': f"{len(SAMPLE_PROGRAMS_DATA):,} ",
                'spending_total': GOVERNMENT_WIDE_SPENDING_TOTAL,
                'agencies_count': f"{agencies_count:,} ",
                'outcomes_count': f"{len(EXPECTED_SHARED_DATA['pon_options']):,} ",
            }


class TestGenerateCategoryPage:

    def test_generate_category_page(self):
        """
        Test writing the category index with spending by type and category stats.
        """
        fiscal_year = constants.LAST_COMPLETED_FISCAL_YEAR
        assistance = SAMPLE_PROGRAMS_BY_ID['10.001']

        totals_by_type = {}
        for program in SAMPLE_PROGRAMS_DATA:
            amount = _lookup_expenditure(program['id'], fiscal_year)
            totals_by_type[program['program_type']] = (
                totals_by_type.get(program['program_type'], 0.0) + amount
            )

        obligations_by_type = []
        for prog_type, total_obs in totals_by_type.items():
            if total_obs > 0:
                title = constants.PROGRAM_TYPE_MAPPING.get(prog_type, prog_type)
                if title == 'Major Acquisition Programs':
                    title = 'Acquisition Programs'
                obligations_by_type.append({
                    'title': title,
                    'total_obs': total_obs,
                })
        obligations_by_type.sort(key=lambda item: item['title'])

        with tempfile.TemporaryDirectory() as output_dir:
            output_path = os.path.join(output_dir, 'category.md')
            load.generate_category_page(
                _query_aware_cursor(_category_page_fetchall),
                SAMPLE_PROGRAMS_DATA,
                output_path,
                fiscal_year,
            )

            page = _load_program_markdown(output_path)
            education_obs = _lookup_expenditure(assistance['id'], fiscal_year)
            assert page['title'] == 'Categories'
            assert page['layout'] == 'category-index'
            assert page['permalink'] == '/category.html'
            assert page['fiscal_year'] == fiscal_year
            assert page['total_num_programs'] == len(SAMPLE_PROGRAMS_DATA)
            assert page['total_obs'] == sum(
                item['total_obs'] for item in obligations_by_type
            )
            assert page['obligations_by_type'] == obligations_by_type
            assert page['categories'] == [
                {'title': 'Education', 'permalink': '/category/education'}
            ]
            assert json.loads(page['categories_json']) == [
                {
                    'title': 'Education',
                    'total_num_programs': 1,
                    'total_obs': education_obs,
                    'permalink': '/category/education',
                }
            ]
            assert page['categories_hierarchy'] == CATEGORIES_HIERARCHY
            assert [item['title'] for item in page['obligations_by_type']] == [
                'Acquisition Programs',
                'Federal Financial Assistance',
                'Government Service Programs',
                'Interest on the Public Debt',
            ]
            assert 'Tax Expenditures' not in [
                item['title'] for item in page['obligations_by_type']
            ]


class TestGenerateCategoryMarkdownFiles:

    @patch.object(load, 'recreate_directory')
    @patch.object(load, 'get_categories_hierarchy', return_value=CATEGORIES_HIERARCHY)
    @patch.object(
        load,
        'generate_applicant_type_list',
        side_effect=_applicant_type_list_from_program_ids,
    )
    @patch.object(
        load, 'generate_agency_list', side_effect=_agency_list_from_program_ids
    )
    @patch.object(
        load,
        'get_assistance_listing_expenditures',
        side_effect=_expenditures_from_sample,
    )
    def test_generate_category_markdown_files(
        self,
        mock_expenditures,
        mock_agencies,
        mock_applicants,
        mock_hierarchy,
        mock_recreate_directory,
    ):
        """
        Test writing category markdown with populated and empty subcategories.
        """
        fiscal_year = constants.LAST_COMPLETED_FISCAL_YEAR
        assistance = SAMPLE_PROGRAMS_BY_ID['10.001']

        with tempfile.TemporaryDirectory() as output_dir:
            load.generate_category_markdown_files(
                _query_aware_cursor(_category_markdown_fetchall, _taxonomy_totals_fetchone),
                output_dir,
                fiscal_year,
            )

            mock_recreate_directory.assert_called_once_with(output_dir)

            page = _load_program_markdown(
                os.path.join(output_dir, 'education.md')
            )
            assert page['title'] == 'Education'
            assert page['permalink'] == '/category/education'
            assert page['fiscal_year'] == fiscal_year
            assert page['total_num_programs'] == 1
            assert page['total_num_sub_cats'] == 2
            assert page['total_num_agencies'] == 1
            assert page['total_num_applicant_types'] == 1
            assert page['total_obs'] == assistance['headline_amount']
            assert page['categories_subcategories'] == CATEGORIES_HIERARCHY
            assert json.loads(page['sub_cats']) == [
                {
                    'title': 'Higher Education',
                    'permalink': '/category/education/higher-education',
                    'total_num_programs': 1,
                    'total_obs': assistance['headline_amount'],
                },
                {
                    'title': 'K-12 Education',
                    'permalink': '/category/education/k-12-education',
                    'total_num_programs': 0,
                    'total_obs': 0.0,
                },
            ]
            assert json.loads(page['agencies']) == CATEGORY_PAGE_AGENCIES
            assert json.loads(page['applicant_types']) == (
                CATEGORY_PAGE_APPLICANT_TYPES
            )


class TestGenerateSubcategoryMarkdownFiles:

    @patch.object(load, 'recreate_directory')
    @patch.object(load, 'get_categories_hierarchy', return_value=CATEGORIES_HIERARCHY)
    @patch.object(
        load,
        'generate_applicant_type_list',
        side_effect=_applicant_type_list_from_program_ids,
    )
    @patch.object(
        load, 'generate_agency_list', side_effect=_agency_list_from_program_ids
    )
    @patch.object(
        load,
        'get_assistance_listing_expenditures',
        side_effect=_expenditures_from_sample,
    )
    def test_generate_subcategory_markdown_files(
        self,
        mock_expenditures,
        mock_agencies,
        mock_applicants,
        mock_hierarchy,
        mock_recreate_directory,
    ):
        """
        Test writing subcategory markdown, including empty focus areas.
        """
        fiscal_year = constants.LAST_COMPLETED_FISCAL_YEAR
        assistance = SAMPLE_PROGRAMS_BY_ID['10.001']

        with tempfile.TemporaryDirectory() as output_dir:
            load.generate_subcategory_markdown_files(
                _query_aware_cursor(_subcategory_markdown_fetchall, _taxonomy_totals_fetchone),
                output_dir,
                fiscal_year,
            )

            mock_recreate_directory.assert_called_once_with(output_dir)

            higher_ed = _load_program_markdown(
                os.path.join(output_dir, 'education---higher-education.md')
            )
            assert higher_ed['title'] == 'Higher Education'
            assert higher_ed['permalink'] == (
                '/category/education/higher-education'
            )
            assert higher_ed['parent_title'] == 'Education'
            assert higher_ed['parent_permalink'] == '/category/education'
            assert higher_ed['fiscal_year'] == fiscal_year
            assert higher_ed['total_num_programs'] == 1
            assert higher_ed['total_num_agencies'] == 1
            assert higher_ed['total_num_applicant_types'] == 1
            assert higher_ed['total_obs'] == assistance['headline_amount']
            assert higher_ed['categories_subcategories'] == CATEGORIES_HIERARCHY
            assert json.loads(higher_ed['agencies']) == CATEGORY_PAGE_AGENCIES
            assert json.loads(higher_ed['applicant_types']) == (
                CATEGORY_PAGE_APPLICANT_TYPES
            )
            assert json.loads(higher_ed['programs']) == [
                {
                    'cfda': assistance['id'],
                    'permalink': f"/program/{assistance['id']}",
                    'title': assistance['name'],
                    'popular_name': assistance['popular_name'],
                    'agency': assistance['top_agency_name'],
                    'total_obs': assistance['headline_amount'],
                    'program_type': assistance['program_type'],
                }
            ]

            k12 = _load_program_markdown(
                os.path.join(output_dir, 'education---k-12-education.md')
            )
            assert k12['title'] == 'K-12 Education'
            assert k12['permalink'] == '/category/education/k-12-education'
            assert k12['parent_title'] == 'Education'
            assert k12['parent_permalink'] == '/category/education'
            assert k12['fiscal_year'] == fiscal_year
            assert k12['total_num_programs'] == 0
            assert k12['total_num_agencies'] == 0
            assert k12['total_num_applicant_types'] == 0
            assert k12['total_obs'] == 0.0
            assert k12['categories_subcategories'] == CATEGORIES_HIERARCHY
            assert json.loads(k12['agencies']) == []
            assert json.loads(k12['applicant_types']) == []
            assert json.loads(k12['programs']) == []


class TestSummarizeRelatedPrograms:

    def test_empty_programs(self):
        assert load.summarize_related_programs([]) == {
            'total_expenditure': 0.0,
            'total_agencies': 0,
            'largest_program': None,
            'smallest_program': None,
        }
        assert load.summarize_related_programs(None)['total_agencies'] == 0

    def test_totals_largest_and_smallest(self):
        programs = [
            {
                'name': 'Middle',
                'permalink': '/program/m',
                'agency': 'Department of Agriculture',
                'expenditure_amount': 50,
            },
            {
                'name': 'Largest',
                'permalink': '/program/l',
                'agency': 'Department of Agriculture',
                'expenditure_amount': 100.5,
            },
            {
                'name': 'Smallest',
                'permalink': '/program/s',
                'agency': 'Department of the Treasury',
                'expenditure_amount': -10,
            },
        ]

        assert load.summarize_related_programs(programs) == {
            'total_expenditure': 140.5,
            'total_agencies': 2,
            'largest_program': {
                'name': 'Largest',
                'permalink': '/program/l',
                'expenditure_amount': 100.5,
            },
            'smallest_program': {
                'name': 'Smallest',
                'permalink': '/program/s',
                'expenditure_amount': -10.0,
            },
        }

    def test_tie_uses_alphabetical_name_then_list_order(self):
        same_amount = [
            {
                'name': 'Bravo',
                'permalink': '/program/b',
                'agency': 'Agency',
                'expenditure_amount': 10,
            },
            {
                'name': 'Alpha',
                'permalink': '/program/a',
                'agency': 'Agency',
                'expenditure_amount': 10,
            },
        ]
        summary = load.summarize_related_programs(same_amount)
        assert summary['total_agencies'] == 1
        assert summary['largest_program']['permalink'] == '/program/a'
        assert summary['smallest_program']['permalink'] == '/program/a'

        same_name = [
            {
                'name': 'Same',
                'permalink': '/program/first',
                'agency': 'Agency A',
                'expenditure_amount': 10,
            },
            {
                'name': 'Same',
                'permalink': '/program/second',
                'agency': 'Agency B',
                'expenditure_amount': 10,
            },
        ]
        summary = load.summarize_related_programs(same_name)
        assert summary['largest_program']['permalink'] == '/program/first'
        assert summary['smallest_program']['permalink'] == '/program/first'

    def test_missing_expenditure_counts_as_zero(self):
        summary = load.summarize_related_programs([
            {'name': 'Missing', 'permalink': '/program/m', 'agency': 'Agency'},
            {
                'name': 'Present',
                'permalink': '/program/p',
                'agency': 'Agency',
                'expenditure_amount': 5,
            },
        ])
        assert summary['total_expenditure'] == 5.0
        assert summary['largest_program']['name'] == 'Present'
        assert summary['smallest_program']['name'] == 'Missing'
        assert summary['smallest_program']['expenditure_amount'] == 0.0


class TestGenerateGwoMarkdownFiles:

    @patch.object(load, 'recreate_directory')
    @patch.object(load, 'get_amounts', side_effect=_amounts_from_sample)
    def test_generate_gwo_markdown_files(
        self, mock_amounts, mock_recreate_directory
    ):
        """
        Test writing GWO markdown for assigned objectives, including Unspecified agencies.
        """
        fiscal_year = constants.LAST_COMPLETED_FISCAL_YEAR
        assigned = ALL_GWO_ROWS[0]
        related_ids = ['10.001', 'C.1']

        with tempfile.TemporaryDirectory() as output_dir:
            load.generate_gwo_markdown_files(
                _query_aware_cursor(_gwo_markdown_fetchall),
                output_dir,
                fiscal_year,
            )

            mock_recreate_directory.assert_called_once_with(output_dir)
            assert sorted(os.listdir(output_dir)) == ['GWO_1_2.md']

            page = _load_program_markdown(
                os.path.join(output_dir, 'GWO_1_2.md')
            )
            where_used = _where_used_from_sample(related_ids, fiscal_year)
            assert page == {
                'permalink': GWO['permalink'],
                'title': assigned['title'],
                'gwo_id': assigned['id'],
                'focus_area': assigned['focus_area'],
                'category': assigned['category'],
                'definition': assigned['definition'],
                'where_used': where_used,
                'total_expenditure': 2900000.0,
                'total_agencies': 2,
                'largest_program': {
                    'name': 'Contracts Program',
                    'permalink': '/program/C.1',
                    'expenditure_amount': 2100000.0,
                },
                'smallest_program': {
                    'name': 'Assistance Program',
                    'permalink': '/program/10.001',
                    'expenditure_amount': 800000.0,
                },
            }


class TestGeneratePonMarkdownFiles:

    @patch.object(load, 'recreate_directory')
    @patch.object(load, 'get_amounts', side_effect=_amounts_from_sample)
    def test_generate_pon_markdown_files(
        self, mock_amounts, mock_recreate_directory
    ):
        """
        Test writing PON markdown for assigned outcomes, including Unspecified agencies.
        """
        fiscal_year = constants.LAST_COMPLETED_FISCAL_YEAR
        assigned = ALL_PON_ROWS[0]
        related_ids = ['10.001', 'C.1']

        with tempfile.TemporaryDirectory() as output_dir:
            load.generate_pon_markdown_files(
                _query_aware_cursor(_pon_markdown_fetchall),
                output_dir,
                fiscal_year,
            )

            mock_recreate_directory.assert_called_once_with(output_dir)
            assert sorted(os.listdir(output_dir)) == ['PON_1_2.md']

            page = _load_program_markdown(
                os.path.join(output_dir, 'PON_1_2.md')
            )
            where_used = _where_used_from_sample(related_ids, fiscal_year)
            assert page == {
                'permalink': PONS[0]['permalink'],
                'title': assigned['title'],
                'gwo_id': assigned['id'],
                'focus_area': assigned['focus_area'],
                'category': assigned['category'],
                'definition': assigned['definition'],
                'where_used': where_used,
                'total_expenditure': 2900000.0,
                'total_agencies': 2,
                'largest_program': {
                    'name': 'Contracts Program',
                    'permalink': '/program/C.1',
                    'expenditure_amount': 2100000.0,
                },
                'smallest_program': {
                    'name': 'Assistance Program',
                    'permalink': '/program/10.001',
                    'expenditure_amount': 800000.0,
                },
            }


class TestGenerateProgramMarkdownFiles:

    @patch.object(load, 'recreate_directory')
    def test_generate_program_markdown_files(self, mock_recreate_directory):
        """
        Test writing program markdown files with type-specific spending fields.
        """
        with tempfile.TemporaryDirectory() as output_dir:
            load.generate_program_markdown_files(
                output_dir, SAMPLE_PROGRAMS_DATA, FISCAL_YEARS
            )

            mock_recreate_directory.assert_called_once_with(output_dir)

            assistance_src = SAMPLE_PROGRAMS_BY_ID['10.001']
            assistance = _load_program_markdown(
                os.path.join(output_dir, '10.001.md')
            )
            assert assistance['title'] == assistance_src['name']
            assert assistance['layout'] == 'program'
            assert assistance['permalink'] == '/program/10.001.html'
            assert assistance['fiscal_year'] == constants.LAST_COMPLETED_FISCAL_YEAR
            assert assistance['cfda'] == assistance_src['id']
            assert assistance['popular_name'] == assistance_src['popular_name']
            assert assistance['agency'] == assistance_src['top_agency_name']
            assert assistance['sub-agency'] == assistance_src['sub_agency_name']
            assert assistance['program_type'] == 'assistance_listing'
            assert json.loads(assistance['obligations']) == assistance_src['obligations']
            assert json.loads(assistance['outlays']) == assistance_src['outlays']
            assert assistance['other_program_spending'] is None
            assert assistance['improper_payments'] == (
                assistance_src['improper_payment_metrics']['current_year_details']
            )
            assert assistance['improper_payments_total'] == 500000
            assert assistance['improper_payments_percent'] == 5.0
            assert assistance['improper_payments_is_multiple'] is False
            assert json.loads(assistance['improper_payments_sparkline']) == SPARKLINE
            assert assistance['improper_payments_related_programs'] == RELATED_PROGRAMS
            assert assistance['headline_amount'] == assistance_src['headline_amount']
            assert assistance['gwo'] == GWO
            assert assistance['pons'] == PONS

            contracts = _load_program_markdown(os.path.join(output_dir, 'C.1.md'))
            assert contracts['program_type'] == 'contracts'
            assert contracts['popular_name'] == ''
            assert contracts['agency'] == 'Unspecified'
            assert contracts['sub-agency'] == 'N/A'
            assert contracts['obligations'] is None
            assert json.loads(contracts['outlays']) == CONTRACTS_OUTLAYS
            assert contracts['other_program_spending'] is None

            government_service = _load_program_markdown(
                os.path.join(output_dir, 'S.1.md')
            )
            assert government_service['program_type'] == 'government_service'
            assert government_service['obligations'] is None
            assert json.loads(government_service['outlays']) == GOVERNMENT_SERVICE_OUTLAYS
            assert government_service['other_program_spending'] is None

            interest = _load_program_markdown(os.path.join(output_dir, 'I.1.md'))
            assert interest['program_type'] == 'interest'
            assert interest['obligations'] is None
            assert interest['outlays'] is None
            assert json.loads(interest['other_program_spending']) == INTEREST_SPENDING

            tax_expenditure = _load_program_markdown(
                os.path.join(output_dir, 'TX.1.md')
            )
            assert tax_expenditure['program_type'] == 'tax_expenditure'
            assert tax_expenditure['obligations'] is None
            assert tax_expenditure['outlays'] is None
            assert json.loads(tax_expenditure['other_program_spending']) == TAX_SPENDING


class TestGenerateProgramCsv:

    def test_generate_program_csv(self):
        """
        Test writing all-program-data.csv with type-specific spending columns.
        """
        with tempfile.TemporaryDirectory() as output_dir:
            output_path = os.path.join(output_dir, 'all-program-data.csv')
            load.generate_program_csv(output_path, SAMPLE_PROGRAMS_DATA, FISCAL_YEARS)

            with open(output_path, newline='', encoding='utf-8') as file:
                rows = list(csv.DictReader(file))

            assert [row['program_number'] for row in rows] == [
                program['id'] for program in SAMPLE_PROGRAMS_DATA
            ]

            assistance = rows[0]
            assistance_src = SAMPLE_PROGRAMS_BY_ID['10.001']
            assert assistance['title'] == assistance_src['name']
            assert assistance['popular_name'] == assistance_src['popular_name']
            assert assistance['agency'] == assistance_src['top_agency_name']
            assert assistance['sub-agency'] == assistance_src['sub_agency_name']
            assert assistance['objective'] == assistance_src['objective']
            assert assistance['sam_url'] == assistance_src['sam_url']
            assert assistance['usaspending_url'] == assistance_src['usaspending_url']
            assert assistance['grants_url'] == assistance_src['grants_url']
            assert assistance['assistance_types'] == ','.join(ASSISTANCE_TYPES)
            assert assistance['beneficiary_types'] == ','.join(BENEFICIARY_TYPES)
            assert assistance['applicant_types'] == ','.join(APPLICANT_TYPES)
            assert assistance['categories'] == ','.join(PROGRAM_CATEGORIES)
            assert json.loads(assistance['obligations']) == _csv_obligations(
                ASSISTANCE_OBLIGATIONS
            )
            assert json.loads(assistance['outlays']) == ASSISTANCE_OUTLAYS
            assert assistance['other expenditures'] == ''

            contracts = rows[1]
            assert contracts['program_number'] == 'C.1'
            assert contracts['popular_name'] == ''
            assert contracts['agency'] == 'Unspecified'
            assert contracts['sub-agency'] == 'N/A'
            assert contracts['obligations'] == ''
            assert json.loads(contracts['outlays']) == CONTRACTS_OUTLAYS
            assert contracts['other expenditures'] == ''

            government_service = rows[2]
            assert government_service['program_number'] == 'S.1'
            assert government_service['obligations'] == ''
            assert json.loads(government_service['outlays']) == GOVERNMENT_SERVICE_OUTLAYS
            assert government_service['other expenditures'] == ''

            interest = rows[3]
            assert interest['program_number'] == 'I.1'
            assert interest['obligations'] == ''
            assert interest['outlays'] == ''
            assert json.loads(interest['other expenditures']) == _csv_other_expenditures(
                INTEREST_SPENDING
            )

            tax_expenditure = rows[4]
            assert tax_expenditure['program_number'] == 'TX.1'
            assert tax_expenditure['obligations'] == ''
            assert tax_expenditure['outlays'] == ''
            assert json.loads(tax_expenditure['other expenditures']) == (
                _csv_other_expenditures(TAX_SPENDING)
            )


class TestGenerateProgramsTableJson:

    def test_generate_programs_table_json(self):
        """
        Test writing programs-table.json from shared program data.
        """
        fiscal_year = constants.LAST_COMPLETED_FISCAL_YEAR

        with tempfile.TemporaryDirectory() as output_dir:
            output_path = os.path.join(output_dir, 'programs-table.json')
            load.generate_programs_table_json(
                output_path, SAMPLE_PROGRAMS_DATA, fiscal_year
            )

            with open(output_path, encoding='utf-8') as file:
                content = file.read()
            rows = json.loads(content)

            assert [row['cfda'] for row in rows] == [
                'I.1', 'TX.1', 'S.1', 'C.1', '10.001'
            ]
            assert content == json.dumps(rows, separators=(',', ':'))

            rows_by_id = {row['cfda']: row for row in rows}
            for program in SAMPLE_PROGRAMS_DATA:
                row = rows_by_id[program['id']]
                assert row['title'] == program['name']
                assert row['permalink'] == f"/program/{program['id']}"
                assert row['obligations'] == program['headline_amount']
                assert row['programType'] == program['program_type']
                assert row['objectives'] == program['objective']
                assert row['gwo'] == (
                    [program['gwo']['gwo']] if program['gwo'] is not None else []
                )
                assert row['pons'] == [pon['pon'] for pon in program['pons']]
                assert row['popularName'] == program['popular_name']
                assert row['assistanceTypes'] == program['assistance_types']
                assert row['applicantTypes'] == program['applicant_types']
                assert row['categories'] == [
                    {
                        'title': 'Education',
                        'subCategory': {'title': 'Higher Education'},
                    }
                ]

            assert rows_by_id['10.001']['agency'] == {
                'title': 'Department of Agriculture',
                'subAgency': {'title': 'Food and Nutrition Service'},
            }
            assert rows_by_id['C.1']['agency'] == {
                'title': 'Unspecified',
                'subAgency': {'title': 'N/A'},
            }


class TestExportInflationPopulationFromCsv:

    def test_export_inflation_population_from_csv(self):
        """
        Test converting inflation and population CSV data into global_data.yml.
        """
        csv_content = (
            'Year,Inflation Rate Percentage,Population Growth Percentage\n'
            '2019,0.02,0.02\n'
            '2022,0.06,0.03\n'
        )
        expected = [
            {
                'Year': 2019,
                'InflationRatePercentage': 0.02,
                'PopulationGrowthPercentage': 0.02,
            },
            {
                'Year': 2022,
                'InflationRatePercentage': 0.06,
                'PopulationGrowthPercentage': 0.03,
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, 'inflation_and_population_growth.csv')
            yml_path = os.path.join(tmpdir, 'global_data.yml')
            with open(csv_path, 'w', encoding='utf-8') as file:
                file.write(csv_content)

            with patch.object(load, 'INFLATION_POPULATION_FILE_PATH', csv_path), \
                 patch.object(load, 'GLOBAL_DATA_YML_PATH', yml_path):
                load.export_inflation_population_from_csv()

            with open(yml_path, encoding='utf-8') as file:
                content = file.read()

            assert content.startswith('---\n')
            assert content.endswith('...\n')
            data = yaml.safe_load(content)
            assert data['InflationPopulation'] == expected


class TestExportGlobalDatesToYml:

    def test_export_global_dates_to_yml(self):
        """
        Test exporting fiscal year and source date constants to YAML.
        """
        expected = {
            'CURRENT_FISCAL_YEAR': constants.CURRENT_FISCAL_YEAR,
            'LAST_COMPLETED_FISCAL_YEAR': constants.LAST_COMPLETED_FISCAL_YEAR,
            'BASELINE_INFLATION_YEAR': constants.BASELINE_INFLATION_YEAR,
            'SPENDING_CHART_YEAR_RANGE': constants.SPENDING_CHART_YEAR_RANGE,
            'SITE_UPDATE_DATE': constants.SITE_UPDATE_DATE,
            'SAMGOV_ASSISTANCE_LISTINGS_DATE': constants.SAMGOV_ASSISTANCE_LISTINGS_DATE,
            'USASPENDING_TRANSACTION_DATE': constants.USASPENDING_TRANSACTION_DATE,
            'TREASURYGOV_TAX_EXPEND_DATE': constants.TREASURYGOV_TAX_EXPEND_DATE,
            'PAYMENTACCURACY_FY_DATE': constants.PAYMENTACCURACY_FY_DATE,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir)
            repo_root = MagicMock()
            website_dir = MagicMock()
            repo_root.__truediv__.return_value = website_dir
            website_dir.__truediv__.return_value = data_path

            with patch.object(load, 'Path') as mock_path_cls:
                mock_path_cls.return_value.resolve.return_value.parents.__getitem__.return_value = repo_root
                result = load.export_global_dates_to_yml()

            output_file = data_path / 'constants_global_dates.yml'
            assert result == output_file
            with open(output_file, encoding='utf-8') as file:
                data = yaml.safe_load(file)
            assert data == expected


class TestExportDataSourcesConfig:

    def test_export_data_sources_config(self):
        """
        Test exporting program data-source mappings to YAML.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            yml_path = os.path.join(tmpdir, 'data_sources.yml')

            with patch.object(load, 'DATA_SOURCES_YML_PATH', yml_path):
                load.export_data_sources_config()

            with open(yml_path, encoding='utf-8') as file:
                content = file.read()

            assert content.startswith('---\n')
            assert content.endswith('...\n')
            assert '&id' not in content
            data = yaml.safe_load(content)
            assert data == {'data_sources': load.build_data_sources_config()}
            assistance = data['data_sources']['assistance_listing']
            assert assistance['current_year']['obligations'] == 'SAM.gov'
            assert assistance['prior_year']['obligations'] == 'USAspending.gov'
            assert data['data_sources']['tax_expenditure']['current_year']['revenue_losses'] == (
                'USAspending.gov'
            )


class TestDataQualityGate:

    def test_ignore_blockers_flag_defaults_off(self):
        args = load.parse_args([])
        assert args.ignore_blockers is False

    def test_ignore_blockers_flag_is_parsed(self):
        args = load.parse_args(["--ignore-blockers"])
        assert args.ignore_blockers is True

    def test_main_stops_when_blockers_exist(self, tmp_path):
        qa_dir = tmp_path / "qa"
        qa_dir.mkdir()
        (qa_dir / "blockers.txt").write_text("BLOCKED:  example\n", encoding="utf-8")

        with patch.object(load, "QA_DIRECTORY", qa_dir), \
             patch.object(load.sqlite3, "connect") as connect:
            with pytest.raises(SystemExit) as exc:
                load.main()

        assert exc.value.code == 1
        connect.assert_not_called()

    def test_main_continues_when_ignore_blockers_is_specified(self, tmp_path):
        qa_dir = tmp_path / "qa"
        qa_dir.mkdir()
        (qa_dir / "blockers.txt").write_text("BLOCKED:  example\n", encoding="utf-8")

        with patch.object(load, "QA_DIRECTORY", qa_dir), \
             patch.object(load.sqlite3, "connect", side_effect=RuntimeError("past gate")):
            with pytest.raises(RuntimeError, match="past gate"):
                load.main(ignore_blockers=True)

    def test_main_continues_when_no_blockers(self, tmp_path):
        qa_dir = tmp_path / "qa"
        qa_dir.mkdir()

        with patch.object(load, "QA_DIRECTORY", qa_dir), \
             patch.object(load.sqlite3, "connect", side_effect=RuntimeError("past gate")):
            with pytest.raises(RuntimeError, match="past gate"):
                load.main()

