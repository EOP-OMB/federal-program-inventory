"""
This tests our transformation functions that process the extracted data.
The transform stage is the most complex part of our ETL pipeline.

KNOWN ISSUES :
1. Hard-coded database connection
2. Need better error handling
"""

import os
import json
import csv
import sqlite3
import pytest
from unittest.mock import patch, mock_open, MagicMock, ANY

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

# Import pandas
import pandas as pd

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
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.DictReader')
    def test_load_usaspending_initial_files(self, mock_reader, mock_file, mock_listdir):
        """
        Testing the main USASpending data load function.
        This is complex because it reads from multiple CSV files and loads into SQLite.
        """
        # Reset mocks to ensure test independence
        transform.temp_cur.reset_mock()
        transform.temp_conn.reset_mock()
        
        # Mock the directory listings to return just one test file for each type
        mock_listdir.side_effect = [
            ['assistance_data.csv'],  # Assistance files
            ['contract_data.csv']     # Contract files
        ]
        
        # Create both assistance and contract data
        mock_assistance_data = [
            {
                'assistance_transaction_unique_key': 'trans123',
                'assistance_award_unique_key': 'award123',
                'federal_action_obligation': '100000',
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
                'federal_action_obligation': '200000',
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
        
        # Set up the reader to return different data depending on which file is being read
        mock_reader.side_effect = [mock_assistance_data, mock_contract_data]
        
        # Call the function
        transform.load_usaspending_initial_files()
        
        # Make sure tables were created
        assert transform.temp_cur.execute.call_count >= 2
        
        # Check for table creation SQL
        create_calls = [
            call for call in transform.temp_cur.execute.call_args_list 
            if 'CREATE TABLE' in str(call) 
        ]
        assert len(create_calls) >= 2
        
        # Check that data was insetrted
        insert_calls = [
            call for call in transform.temp_cur.execute.call_args_list 
            if 'INSERT INTO' in str(call)
        ]
        assert len(insert_calls) >= 2  # Should insert both assistance and contract data
        
        # Verify commit
        assert transform.temp_conn.commit.call_count > 0

    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.DictReader')
    def test_load_usaspending_delta_files(self, mock_reader, mock_file, mock_listdir):
        """
        Test that processing delta files that have updates and deletes.
        Checking the correction_delete_ind field.
        """
        # Reset mocks to make sure test is independent
        transform.temp_cur.reset_mock()
        transform.temp_conn.reset_mock()
        
        # Mock directory listing
        mock_listdir.side_effect = [
            ['delta_assistance.csv'],  # Assistance delta files
            ['delta_contract.csv']     # Contract delta files
        ]
        
        # Mock assistance CSV data with correction indicators
        mock_assistance_data = [
            # Delete
            {
                'assistance_transaction_unique_key': 'trans123',
                'correction_delete_ind': 'D'
            },
            # Change
            {
                'assistance_transaction_unique_key': 'trans456',
                'assistance_award_unique_key': 'award456',
                'federal_action_obligation': '100000',
                'total_outlayed_amount_for_overall_award': '80000',
                'action_date_fiscal_year': '2023',
                'prime_award_transaction_place_of_performance_cd_current': 'CA01',
                'cfda_number': '10.001',
                'assistance_type_code': '02',
                'correction_delete_ind': 'C'
            }
        ]
        
        # Mock contract CSV data
        mock_contract_data = [
            # Delete
            {
                'contract_transaction_unique_key': 'ctrans123',
                'correction_delete_ind': 'D'
            },
            # Change
            {
                'contract_transaction_unique_key': 'ctrans456',
                'contract_award_unique_key': 'caward456',
                'federal_action_obligation': '200000',
                'total_outlayed_amount_for_overall_award': '150000',
                'action_date_fiscal_year': '2023',
                'funding_agency_code': 'AG01',
                'funding_agency_name': 'Department of Agriculture',
                'funding_sub_agency_code': 'AG02',
                'funding_sub_agency_name': 'Food and Nutrition Service',
                'funding_office_code': 'OFF01',
                'funding_office_name': 'Main Office',
                'prime_award_transaction_place_of_performance_cd_current': 'CA01',
                'award_type_code': 'A',
                'correction_delete_ind': 'C'
            }
        ]
        
        # Return different data for different files
        mock_reader.side_effect = [mock_assistance_data, mock_contract_data]
        
        # Call the function
        transform.load_usaspending_delta_files()
        
        # Check DELETE operations
        delete_calls = [
            call for call in transform.temp_cur.execute.call_args_list 
            if 'DELETE' in str(call)
        ]
        assert len(delete_calls) >= 4  # 2 for assistance + 2 for contracts
        
        # Check INSERT operations 
        insert_calls = [
            call for call in transform.temp_cur.execute.call_args_list 
            if 'INSERT' in str(call)
        ]
        assert len(insert_calls) >= 2  # 1 for assistance + 1 for contracts
        
        # Verify commit
        assert transform.temp_conn.commit.call_count > 0

class TestTransformAndAggregateData:
    
    def test_transform_and_insert_usaspending_aggregation_data(self):
        """
        Test aggregation of USASpending data for analysis.
        Large SQL queries.
        """
        # Reset mock call counts
        transform.cur.reset_mock()
        transform.conn.reset_mock()
        
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
        # Reset mocks
        transform.cur.reset_mock()
        transform.conn.reset_mock()
        
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
        # Reset mocks
        transform.cur.reset_mock()
        transform.conn.reset_mock()
        
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

class TestLoadCategoryAndSubCategory:
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.reader')
    def test_load_category_and_sub_category(self, mock_csv_reader, mock_file):
        """
        Test loading category mappings from the program-to-function-sub-function.csv file.
        Creates the category hierarchy and links programs to categories.
        """
        # Reset mocks
        transform.cur.reset_mock()
        transform.conn.reset_mock()
        
        # Sample CSV data with program-category-subcategory mappings
        mock_csv_reader.return_value = [
            ['10.001', 'Education', 'Higher Education'],
            ['10.002', 'Education', 'K-12 Education'],
            ['10.003', 'Health', 'Public Health']
        ]
        
        # Call the function
        transform.load_category_and_sub_category()
        
        # Verify parent categories were inserted
        parent_category_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'INSERT INTO category' in str(call) and 'None' in str(call)
        ]
        assert len(parent_category_calls) >= 2  # Education and Health
        
        # Verify sub-categories were inserted
        sub_category_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'INSERT INTO category' in str(call) and 'None' not in str(call)
        ]
        assert len(sub_category_calls) >= 3  # Higher Ed, K-12, Public Health
        
        # Verify programs and categories were linked
        program_category_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'INSERT INTO program_to_category' in str(call)
        ]
        assert len(program_category_calls) >= 3  # One for each program
        
        # Verify commit
        transform.conn.commit.assert_called()

class TestLoadAdditionalPrograms:
    
    @patch('os.path.exists', return_value=True)
    @patch('pandas.read_csv')
    def test_load_additional_programs(self, mock_read_csv, mock_path_exists):
        """
        Test loading additional programs from CSV.
        """
        # Reset mocks
        transform.cur.reset_mock()
        transform.conn.reset_mock()
        
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
    
    
    @patch('os.path.exists', return_value=False)
    @patch('builtins.print')
    def test_load_additional_programs_file_not_found(self, mock_print, mock_path_exists):
        """
        Test handling the case where the additional programs file doesn't exist.
        Should exit without error.
        """
        # Reset mocks
        transform.cur.reset_mock()
        transform.conn.reset_mock()
        
        # Call the function
        transform.load_additional_programs()
        
        # Verify not found message
        mock_print.assert_called_once()
        
        # Should not try to create tables or insert data
        assert transform.cur.execute.call_count == 0
        assert transform.conn.commit.call_count == 0

class TestLoadImproperPaymentMapping:
    
    @patch('os.path.exists', return_value=True)
    @patch('pandas.read_csv')
    @patch('builtins.print')
    def test_load_improper_payment_mapping(self, mock_print, mock_read_csv, mock_path_exists):
        """
        Test loading improper payment mapping data from CSV.
        """
        # Reset mocks
        transform.cur.reset_mock()
        transform.conn.reset_mock()
        
        # Sample DataFrame for improper payments
        mock_df = pd.DataFrame({
            'program_id': ['10.001', '10.002'],
            'improper_payment_program_name': ['Program A', 'Program B'],
            'outlays': ['$1,000,000', '$2,000,000'],
            'improper_payment_amount': ['$50,000', '$100,000'],
            'insufficient_documentation_amount': ['$10,000', '$20,000'],
            'high_priority_program': [1, 0]
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
        assert len(insert_calls) >= 2  # One per program
        
        # Verify commit
        transform.conn.commit.assert_called()
        
        # Verify success message
        assert mock_print.call_count >= 1
    
    @patch('os.path.exists', return_value=False)
    @patch('builtins.print')
    def test_load_improper_payment_mapping_file_not_found(self, mock_print, mock_path_exists):
        """
        Test handling the case where the improper payment mapping file doesn't exist.
        Should exit without error.
        """
        # Reset mocks
        transform.cur.reset_mock()
        transform.conn.reset_mock()
        
        # Call the function
        transform.load_improper_payment_mapping()
        
        # Verify not found message
        mock_print.assert_called_once()
        
        # Should not try to create tables or insert data
        assert transform.cur.execute.call_count == 2
        # Should not execute any INSERT statements
        insert_calls = [
            call for call in transform.cur.execute.call_args_list 
            if 'INSERT INTO' in str(call)
        ]
        assert len(insert_calls) == 0
