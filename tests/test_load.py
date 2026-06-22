"""
This tests our functions that generate markdown files for the static website.
These functions are what create all the program pages, category pages, etc.

KNOWN ISSUES:
1. clean_string doesn't normalize internal whitespace
2. Hardcoded database path in database connection
"""

import os
import json
import yaml
import pytest
from unittest.mock import patch, mock_open, MagicMock, ANY
import sqlite3

# Mock the sqlite3.connect function
# This helps with error when connecting to non-existent database files
with patch('sqlite3.connect', return_value=MagicMock()):
    # Import the module
    from data_processing import load

class TestEnsureDirectoryExists:

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_ensure_directory_exists_new_dir(self, mock_makedirs, mock_exists):
        """
        Test creating a directory that doesn't exist.
        Make sure output directories are available.
        """
        # Setup mock to say the directory doesn't exist
        mock_exists.return_value = False
        
        # Call the function
        load.ensure_directory_exists('/test/directory')
        
        # Verify makedirs was called
        mock_makedirs.assert_called_once_with('/test/directory')
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_ensure_directory_exists_existing_dir(self, mock_makedirs, mock_exists):
        """Test handling of directories that already exist - should do nothing"""
        # Setup mock to say the directory exists
        mock_exists.return_value = True
        
        # Call the function
        load.ensure_directory_exists('/test/directory')
        
        # Verify makedirs was NOT called
        mock_makedirs.assert_not_called()

class TestGetAssistanceProgramObligations:
    
    def test_get_assistance_program_obligations(self):
        """
        Test getting obligation data for assistance programs.
        This should collect data from both SAM.gov and USASpending.
        """
        # Create a mock cursor
        mock_cursor = MagicMock()
        
        # Set up mock cursor responses for different queries
        def execute_side_effect(query, params):
            if "program_sam_spending" in query and "is_actual = 1" in query:
                # Actual amount query
                mock_cursor.fetchone.return_value = {'actual_amount': 1000000}
            elif "usaspending_assistance_obligation_aggregation" in query:
                # USA spending obligations
                mock_cursor.fetchone.return_value = {'total_obligations': 1200000}
            else:
                mock_cursor.fetchone.return_value = None
        
        mock_cursor.execute.side_effect = execute_side_effect
        
        # Call the function with our test program
        result = load.get_assistance_program_obligations(
            mock_cursor, '10.001', ['2023', '2024'])
        
        # Verify the results
        assert len(result) == 2  # Two fiscal years
        assert result[0]['x'] == '2023'
        assert result[0]['sam_actual'] == 1000000.0
        assert result[0]['usa_spending_actual'] == 1200000.0

class TestGetOtherProgramObligations:
    
    def test_get_other_program_obligations_tax_expenditure(self):
        """
        Test getting obligation data for tax expenditure programs.
        These have both outlays and forgone revenue.
        """
        # Create a mock cursor
        mock_cursor = MagicMock()
        
        # Set up cursor response
        mock_cursor.fetchone.return_value = {
            'fiscal_year': 2023,
            'outlays': 0,
            'forgone_revenue': 2000000,
            'source': 'additional-programs.csv'
        }
        
        # Call the function for a tax expenditure program
        result = load.get_other_program_obligations(
            mock_cursor, 'TX001', ['2023'], 'tax_expenditure')
        
        # Verify the results
        assert len(result) == 1
        assert result[0]['x'] == '2023'
        assert result[0]['outlays'] == 0.0
        assert result[0]['forgone_revenue'] == 2000000.0
    
    def test_get_other_program_obligations_interest(self):
        """
        Test getting obligation data for interest programs.
        These only have outlays, no forgone revenue.
        """
        # Create a mock cursor
        mock_cursor = MagicMock()
        
        # Set up cursor response
        mock_cursor.fetchone.return_value = {
            'fiscal_year': 2023,
            'outlays': 5000000,
            'forgone_revenue': 0,
            'source': 'additional-programs.csv'
        }
        
        # Call the function for an interest program
        result = load.get_other_program_obligations(
            mock_cursor, 'I001', ['2023'], 'interest')
        
        # Verify the results
        assert len(result) == 1
        assert result[0]['x'] == '2023'
        assert result[0]['outlays'] == 5000000.0
        assert 'forgone_revenue' not in result[0]  # Should not be present for interest programs

class TestGetOutlaysData:
    
    def test_get_outlays_data(self):
        """
        Test getting outlays data for programs.
        This should return both outlays and their corresponding obligations.
        """
        # Create a mock cursor
        mock_cursor = MagicMock()
        
        # Set up cursor response
        mock_cursor.fetchone.return_value = {
            'total_outlay': 800000,
            'total_obligation': 1000000
        }
        
        # Call the function
        result = load.get_outlays_data(
            mock_cursor, '10.001', ['2023', '2024'])
        
        # Verify the results
        assert len(result) == 2  # Two fiscal years
        assert result[0]['x'] == '2023'
        assert result[0]['outlay'] == 800000.0
        assert result[0]['obligation'] == 1000000.0

class TestGetAssistanceListingObligations:
    
    def test_get_assistance_listing_obligations_with_data(self):
        """
        Test getting obligations for assistance listings with actual data.
        This should handle both actual and estimated amounts.
        """
        # Create a mock cursor
        mock_cursor = MagicMock()
        
        # Mock cursor fetchall response for program obligations
        mock_cursor.fetchall.return_value = [
            {'program_id': '10.001', 'total_obs': 1000000},
            {'program_id': '10.002', 'total_obs': 2000000}
        ]
        
        # Call the function
        program_obs, total_obs = load.get_assistance_listing_obligations(
            mock_cursor, ['10.001', '10.002'], '2023')
        
        # Verify the results
        assert len(program_obs) == 2  # Two programs
        assert program_obs['10.001'] == 1000000.0
        assert program_obs['10.002'] == 2000000.0
        assert total_obs == 3000000.0
    
    def test_get_assistance_listing_obligations_empty(self):
        """Test handling of empty program list - should return empty results"""
        # Create a mock cursor
        mock_cursor = MagicMock()
        
        # Call the function with empty list
        program_obs, total_obs = load.get_assistance_listing_obligations(
            mock_cursor, [], '2023')
        
        # Verify the results
        assert program_obs == {}
        assert total_obs == 0.0


class TestGenerateApplicantTypeList:
    
    def test_generate_applicant_type_list(self):
        """
        Test generating a list of applicant types with program counts.
        This is used for filtering on the website.
        """
        # Create a mock cursor
        mock_cursor = MagicMock()
        
        # Mock query response
        mock_cursor.fetchall.return_value = [
            {'title': 'State Government', 'total_num_programs': 10},
            {'title': 'Local Government', 'total_num_programs': 5}
        ]
        
        # Call the function
        result = load.generate_applicant_type_list(
            mock_cursor, ['10.001', '10.002'])
        
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

class TestCleanString:
    @pytest.mark.xfail(reason="Issue #1: clean_string doesn't normalize internal whitespace")
    def test_clean_string(self):
        """
        Test the string cleaning function.
        This removes newlines and excessive whitespace.
        """
        assert load.clean_string("Hello\nWorld") == "HelloWorld"
        assert load.clean_string("  Too much  space  ") == "Too much space"
        assert load.clean_string("No\r\nProblems\rHere") == "NoProblemsHere"
        assert load.clean_string("") == ""

class TestGetCategoriesHierarchy:
    
    def test_get_categories_hierarchy(self):
        
        # Create a mock cursor
        mock_cursor = MagicMock()
        
        # Setup mock response with multiple categories and subcategories
        mock_cursor.fetchall.return_value = [
            {'parent_id': 'education', 'parent_name': 'Education', 'sub_name': 'Higher Education'},
            {'parent_id': 'education', 'parent_name': 'Education', 'sub_name': 'K-12 Education'},
            {'parent_id': 'health', 'parent_name': 'Health', 'sub_name': 'Public Health'}
        ]
        
        # Call the function
        result = load.get_categories_hierarchy(mock_cursor)
        
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
        This should include related programs information.
        """
        # Create a mock cursor
        mock_cursor = MagicMock()
        
        # Setup mock responses - first for the main query
        mock_cursor.fetchall.side_effect = [
            # First query - improper payment data
            [
                {
                    'improper_payment_program_name': 'Test Payment Program',
                    'outlays': 10000000, 
                    'improper_payments': 500000,
                    'insufficient_payment': 100000,
                    'high_priority': 1
                }
            ],
            # Second query - related programs
            [
                {'id': '10.002', 'name': 'Related Program'}
            ]
        ]
        
        # Call the function
        result = load.get_improper_payment_info(mock_cursor, '10.001')
        
        # Verify the results
        assert len(result) == 1
        assert result[0]['name'] == 'Test Payment Program'
        assert result[0]['outlays'] == 10000000.0
        assert result[0]['improper_payments'] == 500000.0
        assert result[0]['insufficient_payment'] == 100000.0
        assert result[0]['high_priority'] is True
        
        # Check related programs
        assert len(result[0]['related_programs']) == 1
        assert result[0]['related_programs'][0]['id'] == '10.002'
        assert result[0]['related_programs'][0]['name'] == 'Related Program'
        assert result[0]['related_programs'][0]['permalink'] == '/program/10.002'

    