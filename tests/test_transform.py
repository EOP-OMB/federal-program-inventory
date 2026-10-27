"""
This tests our transformation functions that process the extracted data.
The transform stage is the most complex part of our ETL pipeline.

KNOWN ISSUES :
1. Hard-coded database connection
2. Need better error handling
"""

import os
import json
import sqlite3
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open, MagicMock

# Mock the sqlite3.connect
# This helps with error when connecting to non-existent database files
with patch('sqlite3.connect', return_value=MagicMock()):
    # Import the module 
    from data_processing import transform
    
    # Also patch the database connections in the module
    transform.temp_conn = MagicMock()
    transform.temp_cur = MagicMock()
    transform.conn = MagicMock()
    transform.cur = MagicMock()

import pandas as pd


@pytest.fixture(autouse=True)
def reset_transform_mocks():
    """Clear shared transform connection mock call history between tests."""
    transform.cur.reset_mock()
    transform.conn.reset_mock()
    transform.temp_cur.reset_mock()
    transform.temp_conn.reset_mock()
    yield

class TestConvertToURLString:
    
    def test_convert_to_url_string_normal(self):
        """
        Testing string conversion - should replace spaces with hyphens
        and make everything lowercase
        """
        result = transform.convert_to_url_string("Sample Category Name")
        assert result == "sample-category-name"
    
    def test_convert_to_url_string_special_chars(self):
        """
        Testing strings with special characters 
        """
        result = transform.convert_to_url_string("Sample & Category (Name)")
        assert result == "sample---category--name-"
    
    def test_convert_to_url_string_empty(self):
        """Testing empty strings don't break anything"""
        result = transform.convert_to_url_string("")
        assert result == ""

class TestLoadUSASpendingFiles:
    
    @patch('os.listdir')
    @patch('os.remove')
    @patch('shutil.rmtree')
    @patch('zipfile.ZipFile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.DictReader')
    def test_load_usaspending_initial_files(
        self, mock_reader, mock_file, mock_zipfile, mock_rmtree, mock_remove, mock_listdir
    ):
        """
        Testing the main USAspending data load function.
        Zip archives are extracted to a temp directory, then CSVs are loaded.
        """
        mock_listdir.side_effect = [
            ['assistance.zip'],
            ['assistance_data.csv'],
            ['contracts.zip'],
            ['contract_data.csv'],
        ]

        mock_assistance_data = [
            {
                'assistance_transaction_unique_key': 'trans123',
                'assistance_award_unique_key': 'award123',
                'generated_pragmatic_obligations': '100000',
                'total_outlayed_amount_for_overall_award': '80000',
                'action_date_fiscal_year': '2023',
                'prime_award_transaction_place_of_performance_cd_current': 'CA01',
                'cfda_number': '10.001',
                'assistance_type_code': '02'
            }
        ]

        mock_contract_data = [
            {
                'contract_transaction_unique_key': 'ctrans123',
                'contract_award_unique_key': 'caward123',
                'generated_pragmatic_obligations': '200000',
                'total_outlayed_amount_for_overall_award': '150000',
                'action_date_fiscal_year': '2023',
                'funding_agency_code': 'AG01',
                'funding_agency_name': 'Department of Agriculture',
                'funding_sub_agency_code': 'AG02',
                'funding_sub_agency_name': 'Food and Nutrition Service',
                'funding_office_code': 'OFF01',
                'funding_office_name': 'Main Office',
                'prime_award_transaction_place_of_performance_cd_current': 'CA01',
                'award_type_code': 'A'
            }
        ]

        mock_reader.side_effect = [mock_assistance_data, mock_contract_data]

        transform.load_usaspending_initial_files()

        mock_zipfile.assert_any_call(
            transform.ASSISTANCE_ZIP_FILE_DIRECTORY + 'assistance.zip', 'r'
        )
        mock_zipfile.assert_any_call(
            transform.CONTRACT_ZIP_FILE_DIRECTORY + 'contracts.zip', 'r'
        )
        mock_zipfile.return_value.__enter__.return_value.extractall.assert_called()

        create_calls = [
            call for call in transform.temp_cur.execute.call_args_list
            if 'CREATE TABLE' in str(call)
        ]
        assert len(create_calls) >= 2

        insert_calls = [
            call for call in transform.temp_cur.execute.call_args_list
            if 'INSERT INTO' in str(call)
        ]
        assert len(insert_calls) == 2
        assert insert_calls[0].args[1] == [
            'trans123', 'award123', '100000', '80000', '2023', 'CA01', '10.001', '02'
        ]
        assert insert_calls[1].args[1] == [
            'ctrans123', 'caward123', '200000', '150000', '2023',
            'AG01', 'Department of Agriculture', 'AG02', 'Food and Nutrition Service',
            'OFF01', 'Main Office', 'CA01', 'A'
        ]

        assert transform.temp_conn.commit.call_count > 0

class TestTransformAndAggregateData:
    
    def test_transform_and_insert_usaspending_aggregation_data(self):
        """
        Test aggregation of USAspending data for analysis.
        Large SQL queries.
        """
        # Call the function
        transform.transform_and_insert_usaspending_aggregation_data()
        
        # Check that obligation tables were created
        obligation_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'OBLIGATION' in str(call).upper()
        ]
        assert len(obligation_calls) >= 3  # Should DROP, CREATE, and INSERT
        
        # Check that outlay tables were created
        outlay_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'OUTLAY' in str(call).upper()
        ]
        assert len(outlay_calls) >= 3  # Should DROP, CREATE, and INSERT
        
        # Verify two commits
        assert transform.conn.commit.call_count == 2

class TestLoadAgency:
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_agency(self, mock_json_load, mock_file):
        """
        Test loading agency data from organizations.json.
        Check handling of CFO Act agencies and agency display name mapping.
        """
        # Sample agency data
        mock_json_load.return_value = [
            {
                "orgKey": "100000",
                "name": "Department of Example",
                "agencyName": "EXAMPLE, DEPARTMENT OF",
                "l1OrgKey": "100000",
                "l2OrgKey": None
            },
            {
                "orgKey": "100001",
                "name": "Bureau of Examples",
                "agencyName": None,
                "l1OrgKey": "100000",
                "l2OrgKey": "100001"
            }
        ]
        
        # Mock constants mapping
        original_agency_display_names = transform.constants.AGENCY_DISPLAY_NAMES
        original_cfo_act_agency_names = transform.constants.CFO_ACT_AGENCY_NAMES
        
        transform.constants.AGENCY_DISPLAY_NAMES = {
            "EXAMPLE, DEPARTMENT OF": "Department of Example"
        }
        transform.constants.CFO_ACT_AGENCY_NAMES = [
            "Department of Example"
        ]
        
        try:
            # Call the function
            transform.load_agency()
            
            # Verify SQL statements related to the agency table were executed
            agency_table_calls = [
                call for call in transform.cur.execute.call_args_list
                if 'agency' in str(call).lower()
            ]
            assert len(agency_table_calls) >= 2  # Should have at least drop, create
            
            # Verify both agencies were inserted
            insert_calls = [
                call for call in transform.cur.execute.call_args_list 
                if 'INSERT INTO agency' in str(call)
            ]
            assert len(insert_calls) >= 2
            
            # Verify CFO Act flag inserted correctly
            assert any(['100000' in str(call) and '1' in str(call) 
                    for call in transform.cur.execute.call_args_list])
            
            # Verify commit
            transform.conn.commit.assert_called()
        finally:
            # Restore constants
            transform.constants.AGENCY_DISPLAY_NAMES = original_agency_display_names
            transform.constants.CFO_ACT_AGENCY_NAMES = original_cfo_act_agency_names

class TestLoadSAMCategory:
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_sam_category(self, mock_json_load, mock_file):
        """
        Test loading the assistance types, applicant types, and beneficiary types
        from SAM.gov's data dictionary.
        """
        # Sample dictionary data
        mock_json_load.return_value = {
            "_embedded": {
                "jSONObjectList": [
                    {
                        "id": "assistance_type",
                        "elements": [
                            {
                                "element_id": "01",
                                "value": "FORMULA GRANTS",
                                "elements": [
                                    {
                                        "element_id": "01A",
                                        "value": "Formula Subgrant"
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "id": "applicant_types",
                        "elements": [
                            {
                                "element_id": "01",
                                "value": "State Government"
                            }
                        ]
                    },
                    {
                        "id": "beneficiary_types",
                        "elements": [
                            {
                                "element_id": "01",
                                "value": "Individual/Family"
                            }
                        ]
                    }
                ]
            }
        }
        
        # Mock display names mapping
        original_assistance_type_display_names = transform.constants.ASSISTANCE_TYPE_DISPLAY_NAMES
        transform.constants.ASSISTANCE_TYPE_DISPLAY_NAMES = {
            "FORMULA GRANTS": "Formula Grants"
        }
        
        try:
            # Call the function
            transform.load_sam_category()
            
            # Check for any category table SQL operations 
            category_table_calls = [
                call for call in transform.cur.execute.call_args_list 
                if 'category' in str(call).lower()
            ]
            assert len(category_table_calls) >= 1  # At least some operations on the table
            
            # Verify all category types were inserted
            insert_calls = [
                call for call in transform.cur.execute.call_args_list 
                if 'INSERT INTO category' in str(call)
            ]
            assert len(insert_calls) >= 4  # multiple inserts
            
            # Verify the assistance type name
            assert any(['Formula Grants' in str(call) 
                    for call in transform.cur.execute.call_args_list])
            
            
            transform.conn.commit.assert_called()
        finally:
            # Restore constants
            transform.constants.ASSISTANCE_TYPE_DISPLAY_NAMES = original_assistance_type_display_names

def _sam_listing(program_number, listing_id=None, **data_overrides):
    listing = {
        "id": listing_id or f"id-{program_number}",
        "data": {
            "programNumber": program_number,
            "organizationId": "123456",
            "title": "Program Title",
            "objective": "Objective",
            "compliance": {
                "CFR200Requirements": {"questions": []},
                "documents": {},
            },
            "financial": {
                "accomplishments": {},
                "obligations": [],
            },
            "authorizations": {},
            "eligibility": {
                "applicant": {"types": []},
                "beneficiary": {"types": []},
            },
        },
    }
    listing["data"].update(data_overrides)
    return listing


def _auth_types(act=None, statute=None, public_law=None, usc=None, eo=None):
    return {
        "act": act,
        "statute": statute,
        "publicLaw": public_law,
        "USC": usc,
        "executiveOrder": eo,
    }


class TestLoadSAMPrograms:

    @patch('data_processing.transform.load_acquisitions_and_services')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_sam_programs(self, mock_json_load, mock_file, mock_acquisitions):
        """
        Test SAM.gov program loading, covering popular names, results,
        authorization types/URLs, spending actual vs estimate, and category maps.
        """
        listing_with_popular_name = _sam_listing(
            "10.001",
            title="  Sample Program  ",
            alternativeNames=["Popular Name"],
            compliance={
                "CFR200Requirements": {
                    "questions": [{"code": "subpartF", "isSelected": True}]
                },
                "documents": {"description": "Sample rules"},
            },
            financial={
                "accomplishments": {
                    "list": [{"fiscalYear": 2023, "description": "Sample result"}]
                },
                "obligations": [
                    {
                        "assistanceType": "01",
                        "values": [
                            {"year": 2023, "actual": 1000000},
                            {"year": 2024, "estimate": 1200000},
                            {"year": 2025, "actual": 0},
                        ],
                    }
                ],
            },
            authorizations={
                "list": [
                    {
                        "authorizationTypes": _auth_types(act=True),
                        "act": {
                            "title": "Sample Act",
                            "part": "Part 100",
                            "section": "Section 5",
                            "description": "Sample description",
                        },
                    }
                ]
            },
            eligibility={
                "applicant": {"types": ["01"]},
                "beneficiary": {"types": ["02"]},
            },
        )

        listing_without_optional_fields = _sam_listing("10.002")
        del listing_without_optional_fields["data"]["title"]

        listing_empty_auth_and_results = _sam_listing(
            "10.003",
            alternativeNames=[""],
            compliance={
                "CFR200Requirements": {
                    "questions": [
                        {"code": "other", "isSelected": True},
                        {"code": "subpartF", "isSelected": 1},
                    ]
                },
                "documents": {},
            },
            financial={
                "accomplishments": {
                    "list": [{"description": "No year"}]
                },
                "obligations": [{"values": []}],
            },
            authorizations={
                "list": [
                    {
                        "authorizationTypes": _auth_types(
                            act=True, statute=True, public_law=True, usc=True, eo=True
                        ),
                        "act": {
                            "title": None,
                            "part": None,
                            "section": None,
                            "description": None,
                        },
                        "statute": {"volume": None, "page": None},
                        "publicLaw": {"congressCode": None, "number": None},
                        "USC": {"title": None, "section": None},
                        "executiveOrder": {
                            "title": None,
                            "part": None,
                            "section": None,
                            "description": None,
                        },
                    }
                ]
            },
        )

        listing_statute_sets_url = _sam_listing(
            "10.004",
            authorizations={
                "list": [
                    {
                        "authorizationTypes": _auth_types(
                            act=True, statute=True, public_law=True, usc=True, eo=True
                        ),
                        "act": {
                            "title": None,
                            "part": "",
                            "section": None,
                            "description": "  Act desc  ",
                        },
                        "statute": {"volume": "117", "page": "123"},
                        "publicLaw": {"congressCode": "117", "number": "21"},
                        "USC": {"title": "42", "section": "1234"},
                        "executiveOrder": {
                            "title": "EO Title.",
                            "part": "",
                            "section": "",
                            "description": "",
                        },
                    }
                ]
            },
        )

        listing_public_law_url = _sam_listing(
            "10.005",
            authorizations={
                "list": [
                    {
                        "authorizationTypes": _auth_types(public_law=True),
                        "publicLaw": {"congressCode": "118", "number": "5"},
                    }
                ]
            },
        )

        listing_usc_numeric_url = _sam_listing(
            "10.006",
            authorizations={
                "list": [
                    {
                        "authorizationTypes": _auth_types(usc=True),
                        "USC": {"title": "42", "section": "1234"},
                    }
                ]
            },
        )

        listing_usc_extracted_section = _sam_listing(
            "10.007",
            authorizations={
                "list": [
                    {
                        "authorizationTypes": _auth_types(usc=True),
                        "USC": {"title": "7", "section": "123c"},
                    }
                ]
            },
        )

        listing_non_numeric_and_missing_objects = _sam_listing(
            "10.008",
            alternativeNames=["Name"],
            authorizations={
                "list": [
                    {
                        "authorizationTypes": _auth_types(
                            act=True, statute=True, public_law=True, usc=True, eo=True
                        ),
                        "statute": {"volume": "XII", "page": "iv"},
                        "publicLaw": {"congressCode": "abc", "number": "def"},
                        "USC": {"title": "7", "section": "abc"},
                    }
                ]
            },
            financial={
                "accomplishments": {"list": []},
                "obligations": [
                    {"assistanceType": ""},
                    {"assistanceType": "02", "values": [{"year": 2023}]},
                ],
            },
        )

        listing_usc_non_numeric_title = _sam_listing(
            "10.009",
            financial={
                "accomplishments": {
                    "list": [{"fiscalYear": 0, "description": "Zero year"}]
                },
                "obligations": [],
            },
            authorizations={
                "list": [
                    {
                        "authorizationTypes": _auth_types(usc=True, statute=True),
                        "statute": {"volume": None, "page": "9"},
                        "USC": {"title": "Title", "section": "5"},
                    }
                ]
            },
        )

        mock_json_load.side_effect = [
            {"10.001": "abc123hash"},
            [
                listing_with_popular_name,
                listing_without_optional_fields,
                listing_empty_auth_and_results,
                listing_statute_sets_url,
                listing_public_law_url,
                listing_usc_numeric_url,
                listing_usc_extracted_section,
                listing_non_numeric_and_missing_objects,
                listing_usc_non_numeric_title,
            ],
        ]

        transform.load_sam_programs()

        mock_acquisitions.assert_called_once()
        transform.conn.commit.assert_called()

        def insert_params(table_name):
            needle = f"INSERT INTO {table_name}"
            params = []
            for execute_call in transform.cur.execute.call_args_list:
                if not execute_call.args:
                    continue
                sql = execute_call.args[0]
                if needle not in sql:
                    continue
                after = sql.split(needle, 1)[1]
                if after and after[0] not in " \n\t":
                    continue
                params.append(execute_call.args[1])
            return params

        program_by_id = {row[0]: row for row in insert_params("program")}
        assert program_by_id["10.001"][2] == "Sample Program"
        assert program_by_id["10.001"][3] == "Popular Name"
        assert program_by_id["10.001"][6] == "abc123hash"
        assert program_by_id["10.001"][10] is True
        assert program_by_id["10.002"][2] is None
        assert program_by_id["10.002"][3] is None
        assert program_by_id["10.002"][6] == ""
        assert program_by_id["10.002"][10] is False
        assert program_by_id["10.003"][3] is None
        assert program_by_id["10.003"][10] is False
        assert program_by_id["10.008"][3] == "Name"

        assert ["10.001", 2023, "Sample result"] in insert_params("program_result")
        result_program_ids = [row[0] for row in insert_params("program_result")]
        assert "10.003" not in result_program_ids
        assert "10.009" not in result_program_ids

        auth_by_id = {row[0]: row for row in insert_params("program_authorization")}
        assert auth_by_id["10.001"][2] is None
        assert "Sample Act" in auth_by_id["10.001"][1]
        assert auth_by_id["10.001"][1].endswith(".")
        assert auth_by_id["10.004"][2] == "https://www.govinfo.gov/link/statute/117/123"
        assert "Pub. L. 117, 21" in auth_by_id["10.004"][1]
        assert auth_by_id["10.004"][1].endswith(".")
        assert auth_by_id["10.005"][2] == "https://www.govinfo.gov/link/plaw/118/public/5"
        assert auth_by_id["10.006"][2] == "https://www.govinfo.gov/link/uscode/42/1234"
        assert auth_by_id["10.007"][2] == "https://www.govinfo.gov/link/uscode/7/123"
        assert auth_by_id["10.008"][2] is None
        assert "XII Stat. iv" in auth_by_id["10.008"][1]
        assert auth_by_id["10.009"][2] is None
        assert "10.002" not in auth_by_id
        assert auth_by_id["10.003"][1] == "."
        assert auth_by_id["10.003"][2] is None

        spending = insert_params("program_sam_spending")
        assert ["10.001", "01", "assistance", 2023, 1, 1000000, 1000000] in spending
        assert ["10.001", "01", "assistance", 2024, 0, 1200000, 1200000] in spending
        spending_years = [(row[0], row[3]) for row in spending]
        assert ("10.001", 2025) not in spending_years

        categories = insert_params("program_to_category")
        assert ["10.001", "01", "assistance"] in categories
        assert ["10.001", "02", "beneficiary"] in categories
        assert ["10.001", "01", "applicant"] in categories
        assert ["10.008", "02", "assistance"] in categories
        assert ["10.008", "", "assistance"] not in categories


class TestLoadAcquisitionsAndServices:

    @patch('pandas.read_csv')
    def test_load_acquisitions_and_services(self, mock_read_csv):
        """
        Test loading contract and government-service programs from
        acquisitions_and_services.csv, including latest-year program rows
        and all-year outlay aggregation rows.
        """
        mock_read_csv.return_value = pd.DataFrame({
            'Program ID': ['C.1', 'C.1', 'S.1'],
            'Agency ID': [100, 100, 200],
            'Program Name': ['  Contract Program  ', '  Contract Program  ', 'Service Program'],
            'Popular Name': ['CP', 'CP', 'SP'],
            'Program Description': ['Contract desc', 'Contract desc', 'Service desc'],
            'Program Type': ['Contracts', 'Contracts', 'Government Service'],
            'Fiscal Year': [2024, 2025, 2025],
            'Outlay_Sum': [10.0, 20.0, float('nan')],
            'Obligation_Sum': [30.0, 40.0, 50.0],
            'Authorization': ['NDAA', 'NDAA', 'Service Act'],
            'Authorization URL': [
                'https://example.gov/ndaa',
                'https://example.gov/ndaa',
                'https://example.gov/service',
            ],
        })

        transform.load_acquisitions_and_services()

        assert mock_read_csv.call_args.args[0].endswith('acquisitions_and_services.csv')

        def insert_params(table_name):
            needle = f"INSERT INTO {table_name}"
            params = []
            for execute_call in transform.cur.execute.call_args_list:
                if not execute_call.args:
                    continue
                sql = execute_call.args[0]
                if needle not in sql:
                    continue
                after = sql.split(needle, 1)[1]
                if after and after[0] not in " \n\t(":
                    continue
                params.append(list(execute_call.args[1]))
            return params

        program_by_id = {row[0]: row for row in insert_params("program")}
        assert set(program_by_id) == {'C.1', 'S.1'}
        assert program_by_id['C.1'][1] == 100
        assert program_by_id['C.1'][2] == 'Contract Program'
        assert program_by_id['C.1'][3] == 'CP'
        assert program_by_id['C.1'][4] == 'Contract desc'
        assert program_by_id['C.1'][5:9] == [None, None, None, None]
        assert program_by_id['C.1'][9] == 'contracts'
        assert program_by_id['C.1'][10] == 0
        assert program_by_id['C.1'][11] is None
        assert program_by_id['S.1'][1] == 200
        assert program_by_id['S.1'][2] == 'Service Program'
        assert program_by_id['S.1'][9] == 'government_service'

        auth_by_id = {row[0]: row for row in insert_params("program_authorization")}
        assert auth_by_id['C.1'] == ['C.1', 'NDAA', 'https://example.gov/ndaa']
        assert auth_by_id['S.1'] == ['S.1', 'Service Act', 'https://example.gov/service']

        categories = insert_params("program_to_category")
        assert ['C.1', 'contracts', 'assistance'] in categories
        assert ['S.1', 'government_service', 'assistance'] in categories
        assert len(categories) == 2

        delete_params = [
            list(execute_call.args[1])
            for execute_call in transform.cur.execute.call_args_list
            if execute_call.args and 'DELETE FROM usaspending_assistance_outlay_aggregation' in execute_call.args[0]
        ]
        assert ['C.1'] in delete_params
        assert ['S.1'] in delete_params
        assert len(delete_params) == 2

        outlays = insert_params("usaspending_assistance_outlay_aggregation")
        assert ['C.1', 2025, 20.0, 40.0] in outlays
        assert ['C.1', 2024, 10.0, 30.0] in outlays
        assert ['S.1', 2025, 0, 50.0] in outlays
        assert len(outlays) == 3


class TestLoadCategoryAndSubCategory:
    
    @patch('pandas.read_csv')
    def test_load_category_and_sub_category(self, mock_read_csv):
        """
        Test loading taxonomy categories and focus areas from GWO/PON
        crosswalks and program GWO assignments.
        """
        gwo_crosswalk = pd.DataFrame({
            'Category Code': ['ED', 'HE'],
            'Category': ['Education', 'Health'],
            'FA Code': ['ED.FA1', 'HE.FA1'],
            'Focus Area': ['Higher Education', 'Public Health'],
            'GWO ID': ['GWO.ED1', 'GWO.HE1'],
            'GWO': ['Improve Higher Education', 'Improve Public Health'],
            'GWO Definition': ['Education GWO definition', 'Health GWO definition'],
        })
        pon_crosswalk = pd.DataFrame({
            'PON ID': ['PON.1'],
            'Category Code': ['ED'],
            'Category': ['Education'],
            'FA Code': ['ED.FA1'],
            'Focus Area': ['Higher Education'],
            'PON2': ['Expand Access'],
            'PON Definition': ['PON definition'],
        })
        gwo_assignment = pd.DataFrame({
            'al_#': ['10.001', '10.002'],
            'GWO ID': ['GWO.ED1', 'GWO.HE1'],
        })
        pon_assignment = pd.DataFrame({
            'al_#': ['10.001'],
            'PON ID': ['PON.1'],
        })
        mock_read_csv.side_effect = [
            gwo_crosswalk, pon_crosswalk, gwo_assignment, pon_assignment
        ]

        transform.load_taxonomy_and_assignments()

        read_paths = [call.args[0] for call in mock_read_csv.call_args_list]
        assert any(path.endswith('Taxonomy_GWO_crosswalk.csv') for path in read_paths)
        assert any(path.endswith('Taxonomy_PON_crosswalk.csv') for path in read_paths)
        assert any(path.endswith('FPI_GWO_assignment.csv') for path in read_paths)
        assert any(path.endswith('FPI_PON_assignment.csv') for path in read_paths)

        sql_calls = [call.args[0] for call in transform.cur.execute.call_args_list if call.args]
        assert any('CREATE TABLE taxonomy_category' in sql for sql in sql_calls)
        assert any('CREATE TABLE taxonomy_focus_area' in sql for sql in sql_calls)
        assert any('CREATE VIEW program_taxonomy_lookup' in sql for sql in sql_calls)

        def insert_params(table_name):
            needle = f'INSERT INTO {table_name}'
            return [
                call.args[1]
                for call in transform.cur.execute.call_args_list
                if call.args and needle in call.args[0]
            ]

        assert ['ED', 'Education'] in insert_params('taxonomy_category')
        assert ['HE', 'Health'] in insert_params('taxonomy_category')

        assert ['ED.FA1', 'Higher Education', 'ED'] in insert_params('taxonomy_focus_area')
        assert ['HE.FA1', 'Public Health', 'HE'] in insert_params('taxonomy_focus_area')

        assert ['GWO.ED1', 'Improve Higher Education', 'Education GWO definition', 'ED.FA1'] in insert_params('gwo')
        assert ['GWO.HE1', 'Improve Public Health', 'Health GWO definition', 'HE.FA1'] in insert_params('gwo')

        assert ['10.001', 'GWO.ED1'] in insert_params('program_to_gwo')
        assert ['10.002', 'GWO.HE1'] in insert_params('program_to_gwo')

        transform.conn.commit.assert_called()

class TestLoadAdditionalPrograms:
    
    @patch('os.path.exists', return_value=True)
    @patch('pandas.read_csv')
    def test_load_additional_programs(self, mock_read_csv, mock_path_exists):
        """
        Test loading additional programs from CSV.
        """
         # Sample DataFrame for additional programs 
        mock_df = pd.DataFrame({
        '`': ['TX001', 'I001'],  # This gets renamed to 'program.id'
        'name': ['Tax Credit', 'Interest Program'],  # This gets renamed to 'program.name'
        'type': ['tax_expenditure', 'interest'],  # This gets renamed to 'program_to_category.category_type'
        'agency': ['Department of Treasury', 'Department of Treasury'],
        'subagency': [None, None],
        'category': ['Economics', 'Economics'],
        'subcategory': ['Tax Policy', 'Debt Management'],
        'description': ['Tax credit description', 'Interest program description'],
        'assistance_type': ['Tax Expenditures', 'Interest'],
        '2023_outlays': [0, 5000000],
        '2023_foregone_revenue': [2000000, 0]

        })
        mock_read_csv.return_value = mock_df
        
        # Mock the agency ID response
        transform.cur.fetchall.return_value = [
            (123, 'Department of Treasury', None, None, 1)
        ]
        
        # Call the function
        transform.load_additional_programs()
        
        # Verify spending table was created
        table_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'CREATE TABLE other_program_spending' in str(call)
        ]
        assert len(table_calls) >= 1
        
        # Verify program data was inserted
        program_insert_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'INSERT INTO program' in str(call)
        ]
        assert len(program_insert_calls) >= 2  # One per program
        
        # Verify spending data was inserted
        spending_insert_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'INSERT INTO other_program_spending' in str(call)
        ]
        assert len(spending_insert_calls) >= 2  # One per program
        
        # Verify commit
        transform.conn.commit.assert_called()

class TestLoadImproperPaymentMapping:
    
    @patch('os.path.exists', return_value=True)
    @patch('pandas.read_csv')
    @patch('builtins.print')
    def test_load_improper_payment_mapping(self, mock_print, mock_read_csv, mock_path_exists):
        """
        Test loading improper payment mapping data from CSV.
        """
        # Sample DataFrame matching improper-payment-program-mapping.csv.
        # Dollar columns are in millions; load_improper_payment_mapping multiplies by 1e6.
        mock_df = pd.DataFrame({
            'program_id': ['10.001', '10.002'],
            'improper_payment_program_name': ['Program A', 'Program B'],
            'agency': ['USDA', 'USDA'],
            'fiscal_year': [2023, 2023],
            'outlays': [1.0, 2.0],
            'improper_payment_amount': [0.05, 0.10],
            'start_date': ['2022-10-01', '2022-10-01'],
            'end_date': ['2023-09-30', '2023-09-30'],
            'insufficient_documentation_amount': [0.01, 0.02],
            'slug': ['program-a', 'program-b']
        })
        mock_read_csv.return_value = mock_df
        
        # Call the function
        transform.load_improper_payment_mapping()
        
        # Verify improper payment table was created
        table_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'CREATE TABLE improper_payment_mapping' in str(call)
        ]
        assert len(table_calls) >= 1
        
        # Verify data was inserted
        insert_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'INSERT INTO improper_payment_mapping' in str(call)
        ]
        assert len(insert_calls) == 2

        insert_params = [call.args[1] for call in insert_calls]
        assert insert_params[0] == (
            '10.001', 'Program A', 'USDA', 2023,
            1000000.0, 50000.0, '2022-10-01', '2023-09-30', 10000.0, 'program-a'
        )
        assert insert_params[1] == (
            '10.002', 'Program B', 'USDA', 2023,
            2000000.0, 100000.0, '2022-10-01', '2023-09-30', 20000.0, 'program-b'
        )
        
        # Verify commit
        transform.conn.commit.assert_called()
        
        # Verify success message
        assert mock_print.call_count >= 1


class TestDataQualityGate:
    def test_main_stops_when_blockers_exist(self, tmp_path):
        qa_dir = tmp_path / "qa"
        qa_dir.mkdir()
        (qa_dir / "stale.csv").write_text("old\n", encoding="utf-8")

        def write_blocker(output_directory):
            (Path(output_directory) / "blockers.txt").write_text(
                "BLOCKED:  example\n",
                encoding="utf-8",
            )

        with patch.object(transform, "QA_DIRECTORY", qa_dir), \
             patch.object(
                 transform.check_data_quality_before_transform, "main", side_effect=write_blocker
             ), \
             patch.object(transform, "load_usaspending_initial_files") as load:
            with pytest.raises(SystemExit) as exc:
                transform.main()

        assert exc.value.code == 1
        load.assert_not_called()
        assert not (qa_dir / "stale.csv").exists()
        assert (qa_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  example\n"
        )

    def test_main_continues_when_no_blockers(self, tmp_path):
        qa_dir = tmp_path / "qa"
        with patch.object(transform, "QA_DIRECTORY", qa_dir), \
             patch.object(transform.check_data_quality_before_transform, "main") as quality, \
             patch.object(transform, "load_usaspending_initial_files") as load, \
             patch.object(
                 transform, "transform_and_insert_usaspending_aggregation_data"
             ), \
             patch.object(transform, "load_agency"), \
             patch.object(transform, "load_sam_category"), \
             patch.object(transform, "load_sam_programs"), \
             patch.object(transform, "load_taxonomy_and_assignments"), \
             patch.object(transform, "load_additional_programs"), \
             patch.object(transform, "load_improper_payment_mapping"), \
             patch.object(transform, "load_views"), \
             patch.object(transform, "remove_orphaned_records"):
            transform.main()

        quality.assert_called_once_with(qa_dir)
        load.assert_called_once()
        assert qa_dir.is_dir()
        assert not (qa_dir / "blockers.txt").exists()

    def test_ignore_blockers_flag_defaults_off(self):
        args = transform.parse_args([])
        assert args.ignore_blockers is False

    def test_ignore_blockers_flag_is_parsed(self):
        args = transform.parse_args(["--ignore-blockers"])
        assert args.ignore_blockers is True

    def test_main_continues_when_ignore_blockers_is_specified(self, tmp_path):
        qa_dir = tmp_path / "qa"
        qa_dir.mkdir()

        def write_blocker(output_directory):
            (Path(output_directory) / "blockers.txt").write_text(
                "BLOCKED:  example\n",
                encoding="utf-8",
            )

        with patch.object(transform, "QA_DIRECTORY", qa_dir), \
             patch.object(
                 transform.check_data_quality_before_transform, "main", side_effect=write_blocker
             ), \
             patch.object(transform, "load_usaspending_initial_files") as load, \
             patch.object(
                 transform, "transform_and_insert_usaspending_aggregation_data"
             ), \
             patch.object(transform, "load_agency"), \
             patch.object(transform, "load_sam_category"), \
             patch.object(transform, "load_sam_programs"), \
             patch.object(transform, "load_taxonomy_and_assignments"), \
             patch.object(transform, "load_additional_programs"), \
             patch.object(transform, "load_improper_payment_mapping"), \
             patch.object(transform, "load_views"), \
             patch.object(transform, "remove_orphaned_records"):
            transform.main(ignore_blockers=True)

        load.assert_called_once()
        assert (qa_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  example\n"
        )

    def test_main_stops_when_blockers_exist_after_transform(self, tmp_path):
        qa_dir = tmp_path / "qa"

        def write_blocker(output_directory, connection):
            (Path(output_directory) / "blockers.txt").write_text(
                "BLOCKED:  after\n",
                encoding="utf-8",
            )

        with patch.object(transform, "QA_DIRECTORY", qa_dir), \
             patch.object(transform.check_data_quality_before_transform, "main"), \
             patch.object(transform, "load_usaspending_initial_files") as load, \
             patch.object(
                 transform, "transform_and_insert_usaspending_aggregation_data"
             ), \
             patch.object(transform, "load_agency"), \
             patch.object(transform, "load_sam_category"), \
             patch.object(transform, "load_sam_programs"), \
             patch.object(transform, "load_taxonomy_and_assignments"), \
             patch.object(transform, "load_additional_programs"), \
             patch.object(transform, "load_improper_payment_mapping"), \
             patch.object(transform, "load_views"), \
             patch.object(transform, "remove_orphaned_records"), \
             patch.object(
                 transform.check_data_quality_after_transform,
                 "main",
                 side_effect=write_blocker,
             ):
            with pytest.raises(SystemExit) as exc:
                transform.main()

        assert exc.value.code == 1
        load.assert_called_once()
        assert (qa_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  after\n"
        )

    def test_main_ignores_blockers_after_transform_when_requested(self, tmp_path):
        qa_dir = tmp_path / "qa"

        def write_blocker(output_directory, connection):
            (Path(output_directory) / "blockers.txt").write_text(
                "BLOCKED:  after\n",
                encoding="utf-8",
            )

        with patch.object(transform, "QA_DIRECTORY", qa_dir), \
             patch.object(transform.check_data_quality_before_transform, "main"), \
             patch.object(transform, "load_usaspending_initial_files"), \
             patch.object(
                 transform, "transform_and_insert_usaspending_aggregation_data"
             ), \
             patch.object(transform, "load_agency"), \
             patch.object(transform, "load_sam_category"), \
             patch.object(transform, "load_sam_programs"), \
             patch.object(transform, "load_taxonomy_and_assignments"), \
             patch.object(transform, "load_additional_programs"), \
             patch.object(transform, "load_improper_payment_mapping"), \
             patch.object(transform, "load_views"), \
             patch.object(transform, "remove_orphaned_records"), \
             patch.object(
                 transform.check_data_quality_after_transform,
                 "main",
                 side_effect=write_blocker,
             ):
            transform.main(ignore_blockers=True)

        assert (qa_dir / "blockers.txt").read_text(encoding="utf-8") == (
            "BLOCKED:  after\n"
        )


class TestAssignmentConstraints:

    def _connection(self):
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript("""
            CREATE TABLE program (id TEXT PRIMARY KEY);
            CREATE TABLE gwo (id TEXT PRIMARY KEY);
            CREATE TABLE pon (id TEXT PRIMARY KEY);
            INSERT INTO program VALUES ('10.001');
            INSERT INTO gwo VALUES ('GWO.ND3');
            INSERT INTO pon VALUES ('PON.N50');
        """)
        connection.execute(transform.PROGRAM_TO_GWO_CREATE_TABLE_SQL)
        connection.execute(transform.PROGRAM_TO_PON_CREATE_TABLE_SQL)
        return connection

    def test_duplicate_assignment_is_not_stored(self):
        connection = self._connection()
        connection.execute(
            transform.PROGRAM_TO_GWO_INSERT_TABLE_SQL, ("10.001", "GWO.ND3")
        )
        connection.execute(
            transform.PROGRAM_TO_GWO_INSERT_TABLE_SQL, ("10.001", "GWO.ND3")
        )
        stored = connection.execute("SELECT COUNT(*) FROM program_to_gwo").fetchone()
        assert stored[0] == 1
        connection.close()

    def test_missing_parent_is_rejected(self):
        connection = self._connection()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                transform.PROGRAM_TO_GWO_INSERT_TABLE_SQL, ("missing", "GWO.ND3")
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                transform.PROGRAM_TO_PON_INSERT_TABLE_SQL, ("10.001", "PON.MISSING")
            )
        connection.close()
