"""
This covers functions that pull data from SAM.gov and USAspending.gov.
I've tried to mock all external API calls

KNOWN ISSUES :
1. Hardcoded file paths in extract_categories_from_pdf
2. Need better error handling
"""

import io
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import requests

# Import the module
from data_processing import extract

class TestExtractAssistanceListing:
    
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_assistance_listing_success(self, mock_file, mock_get, mock_exists):
        # Mock search response
        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "_embedded": {
                "results": [
                    {"_id": "listing1"},
                    {"_id": "listing2"}
                ]
            }
        }
        
        # Mock individual listing responses
        listing_response1 = MagicMock()
        listing_response1.status_code = 200
        listing_response1.text = '{"data": {"programNumber": "10.001"}}'
        
        listing_response2 = MagicMock()
        listing_response2.status_code = 200
        listing_response2.text = '{"data": {"programNumber": "10.002"}}'
        
        # Set up the mock to return different responses
        mock_get.side_effect = [
            search_response, 
            listing_response1, 
            listing_response2,
            listing_response1,  # Add extra responses for any retry logic
            listing_response2
        ]
        
        # Call the function
        extract.extract_assistance_listing()
        
        # Check if the requests were made
        assert mock_get.call_count >= 3
        
        # Check if the file was opened for writing
        mock_file.assert_called_once()
    
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_extract_assistance_listing_network_error(self, mock_print, mock_file, mock_exists):
        """
        Custom mock to handle this properly.
        """
        # Mock search response
        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "_embedded": {
                "results": [
                    {"_id": "listing1"}
                ]
            }
        }
        
        # Create a custom get function that handles multiple calls
        original_get = requests.get
        call_count = 0
        
        def custom_get(*args, **kwargs):
            nonlocal call_count
            # First call - return search results
            if call_count == 0:
                call_count += 1
                return search_response
            # Second call - simulate connection error
            elif call_count == 1:
                call_count += 1
                raise requests.exceptions.ConnectionError("Connection failed")
            # All other calls - return empty response
            else:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = '{}'
                return mock_response
        
        # Apply our custom mock
        with patch('requests.get', side_effect=custom_get):
            # Call function - should handle the error 
            extract.extract_assistance_listing()
            
            # Verify error handling happened
            assert mock_print.called
            calls = [call for call in mock_print.call_args_list if "Error: Connection" in str(call)]
            assert len(calls) > 0

class TestExtractDictionary:
    
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_dictionary_success(self, mock_file, mock_get, mock_exists, sample_dictionary_data):
        """
        Test successful extraction of SAM.gov dictionary.
        """
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(sample_dictionary_data)
        mock_get.return_value = mock_response
        
        # Call the function
        extract.extract_dictionary()
        
        # Check if the request was made correctly
        mock_get.assert_called_once()
        
        # Check if the file was opened 
        mock_file.assert_called_once()
    
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('requests.get')
    def test_extract_dictionary_error(self, mock_get, mock_exists):
        """
        Test handling of errors during dictionary extraction.
        """
        # Simulate request error
        mock_get.side_effect = requests.exceptions.RequestException("Request failed")
        
        # Verify function raises the error
        with pytest.raises(requests.exceptions.RequestException):
            extract.extract_dictionary()

class TestExtractOrganizations:
    
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_organizations_success(self, mock_file, mock_get, mock_exists, sample_organizations_data):
        """
        Test successful extraction of organizations.
        """
        # Mock search response
        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "_embedded": {
                "results": [
                    {"_id": "result1", "organizationHierarchy": [{"organizationId": "org1"}]},
                    {"_id": "result2", "organizationHierarchy": [{"organizationId": "org2"}]}
                ]
            }
        }
        
        # Mock organization responses
        org_response1 = MagicMock()
        org_response1.status_code = 200
        org_response1.json.return_value = {
            "_embedded": [{"org": sample_organizations_data[0]}]
        }
        
        org_response2 = MagicMock()
        org_response2.status_code = 200
        org_response2.json.return_value = {
            "_embedded": [{"org": sample_organizations_data[1]}]
        }
        
        # Set up the mock to return different responses
        mock_get.side_effect = [search_response, org_response1, org_response2]
        
        # Call the function
        extract.extract_organizations()
        
        # Check if the requests were made correctly
        assert mock_get.call_count == 3
        
        # Check if the file was opened
        mock_file.assert_called_once()
    
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('requests.get')
    def test_extract_organizations_error(self, mock_get, mock_exists):
        """
        Test handling of errors during organization extraction.
        """
        # Mock search response
        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "_embedded": {
                "results": [
                    {"_id": "result1", "organizationHierarchy": [{"organizationId": "org1"}]}
                ]
            }
        }
        
        # Simulate error on second request
        mock_get.side_effect = [
            search_response,
            requests.exceptions.RequestException("Request failed")
        ]
        
        # Verify function raises the error
        with pytest.raises(requests.exceptions.RequestException):
            extract.extract_organizations()

class TestExtractUSASpendingAwardHashes:
    
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('requests.post')
    @patch('requests.get')
    @patch('json.dumps')
    def test_extract_usaspending_award_hashes_success(self, mock_dumps, mock_get, mock_post, mock_file, mock_load, mock_exists):
        """
        Test successful extraction of USAspending award hashes.
        """
        # Mock load assistance listings
        mock_load.return_value = [
            {"data": {"programNumber": "10.001"}}
        ]
        
        # Mock CFDA autocomplete response
        cfda_response = MagicMock()
        cfda_response.status_code = 200
        cfda_response.json.return_value = {
            "results": [
                {
                    "program_number": "10.001",
                    "program_title": "Sample Program",
                    "identifier": "10.001"
                }
            ]
        }
        
        # Mock filter response
        filter_response = MagicMock()
        filter_response.status_code = 200
        filter_response.json.return_value = {"hash": "abc123hash"}
        
        # One get and one post
        mock_get.return_value = cfda_response
        mock_post.return_value = filter_response
        
        # Set up the dumps return value
        mock_dumps.return_value = '{"10.001": "abc123hash"}'
        
        # Call the function
        extract.extract_usaspending_award_hashes()
        
        # Verify the file is written
        mock_file.assert_called()
    
    @pytest.mark.xfail(reason="Issue #2: extract_usaspending_award_hashes doesn't handle connection errors")
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_usaspending_award_hashes_connection_error_current(self, mock_file, mock_load, mock_exists):
        """
        This test is expected to fail until error handling is implemented.
        """
        # Mock load assistance listings
        mock_load.return_value = [
            {"data": {"programNumber": "10.001"}}
        ]
        
        # Set up patching for multiple components
        with patch('requests.get') as mock_get, \
            patch('requests.post') as mock_post:
            
            # Mock autocomplete response
            cfda_response = MagicMock()
            cfda_response.status_code = 200
            cfda_response.json.return_value = {
                "results": [
                    {
                        "program_number": "10.001",
                        "program_title": "Sample Program",
                        "identifier": "10.001"
                    }
                ]
            }
            mock_get.return_value = cfda_response
            
            # Make post raise a connection error
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            # Shouldn't raise an exception
            extract.extract_usaspending_award_hashes()

    @pytest.mark.xfail(reason="Issue #2: extract_usaspending_award_hashes_connection_error_expected doesn't handle connection errors")
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('time.sleep')
    @patch('builtins.print')
    def test_extract_usaspending_award_hashes_connection_error_expected(self, mock_print, mock_sleep, mock_file, mock_load, mock_exists):
        """
        This test verifies that errors are handled
        """
        # Mock load assistance listings
        mock_load.return_value = [
            {"data": {"programNumber": "10.001"}}
        ]
        
        # Set up patching for multiple components
        with patch('requests.get') as mock_get, \
            patch('requests.post') as mock_post:
            
            # Mock autocomplete response
            cfda_response = MagicMock()
            cfda_response.status_code = 200
            cfda_response.json.return_value = {
                "results": [
                    {
                        "program_number": "10.001",
                        "program_title": "Sample Program",
                        "identifier": "10.001"
                    }
                ]
            }
            mock_get.return_value = cfda_response
            
            # Make post raise a connection error
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            # Run the function
            extract.extract_usaspending_award_hashes()
            
            # Verify error handling happened
            assert mock_print.called, "Error was not properly logged"
            assert mock_sleep.called, "No retry was attempted"

class TestCleanJSONData:
    
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('json.load')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_clean_json_data_success(self, mock_file, mock_dump, mock_load, mock_exists):
        """
        Test successful cleaning of JSON data.
        """
        # Sample data, needs to be corrected
        sample_data = {
            "program": {
                "name": "lndian Health Service"
            }
        }
        
        # Expected cleaned data
        expected_clean_data = {
            "program": {
                "name": "Indian Health Service"
            }
        }
        
        # Mock load to return our sample data
        mock_load.return_value = sample_data
        
        # Call the function
        extract.clean_json_data("test.json")
        
        # Check if file was opened 
        assert mock_file.call_count == 2
        
        # Check if dumb was called and cleaned data
        mock_dump.assert_called_once()
    
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_clean_json_data_file_not_found(self, mock_file, mock_exists):

        with pytest.raises(FileNotFoundError):
            extract.clean_json_data("nonexistent.json")

class TestCleanAllData:
    
    @patch('data_processing.extract.DISK_DIRECTORY', '')
    @patch('data_processing.extract.SOURCE_DIRECTORY', '')
    @patch('data_processing.extract.EXTRACTED_DIRECTORY', '')
    @patch('os.path.exists', return_value=True)
    @patch('data_processing.extract.clean_json_data')
    def test_clean_all_data_success(self, mock_clean_json_data, mock_exists):
        """
        Test successful cleaning of all data files.
        """
        # Call the function
        extract.clean_all_data()
        
        # Check if clean_json_data was called for each file
        assert mock_clean_json_data.call_count == 2
        mock_clean_json_data.assert_any_call("assistance-listings.json")
        mock_clean_json_data.assert_any_call("dictionary.json")