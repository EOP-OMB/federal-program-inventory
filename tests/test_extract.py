import pytest
from unittest.mock import patch, mock_open
import requests

from conftest import http_response
from data_processing import extract


@pytest.fixture(scope="class", autouse=True)
def extract_paths():
    """Keep extract I/O pointed at empty paths for every test class in this module."""
    with patch("data_processing.extract.DISK_DIRECTORY", ""), \
         patch("data_processing.extract.SOURCE_DIRECTORY", ""), \
         patch("data_processing.extract.EXTRACTED_DIRECTORY", ""), \
         patch("os.path.exists", return_value=True):
        yield


class TestExtractAssistanceListing:
    
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_assistance_listing_success(self, mock_file, mock_get):
        search_response = http_response({
            "_embedded": {
                "results": [
                    {"_id": "listing1"},
                    {"_id": "listing2"}
                ]
            }
        })
        listing_response1 = http_response({"data": {"programNumber": "10.001"}})
        listing_response2 = http_response({"data": {"programNumber": "10.002"}})
        
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
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_extract_assistance_listing_network_error(self, mock_print, mock_file):
        """
        Custom mock to handle this properly.
        """
        search_response = http_response({
            "_embedded": {
                "results": [
                    {"_id": "listing1"}
                ]
            }
        })
        
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
                return http_response({})
        
        # Apply our custom mock
        with patch('requests.get', side_effect=custom_get):
            # Call function - should handle the error 
            extract.extract_assistance_listing()
            
            # Verify error handling happened
            assert mock_print.called
            calls = [call for call in mock_print.call_args_list if "Error: Connection" in str(call)]
            assert len(calls) > 0

class TestExtractIPData:

    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_ip_data_success(self, mock_file, mock_get):
        """
        Test successful extraction of PaymentAccuracy.gov IP mapping data.
        """
        mock_get.return_value = http_response(
            text="agency,program,aln\nUSDA,Program A,10.001\n"
        )

        extract.extract_ip_data()

        mock_get.assert_called_once()
        mock_file.assert_called_once()

    @patch('requests.get')
    def test_extract_ip_data_error(self, mock_get):
        """
        Test handling of errors during IP data extraction.
        """
        mock_get.side_effect = requests.exceptions.RequestException("Request failed")

        with pytest.raises(requests.exceptions.RequestException):
            extract.extract_ip_data()

class TestExtractDictionary:
    
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_dictionary_success(self, mock_file, mock_get, sample_dictionary_data):
        """
        Test successful extraction of SAM.gov dictionary.
        """
        mock_get.return_value = http_response(sample_dictionary_data)
        
        # Call the function
        extract.extract_dictionary()
        
        # Check if the request was made correctly
        mock_get.assert_called_once()
        
        # Check if the file was opened 
        mock_file.assert_called_once()
    
    @patch('requests.get')
    def test_extract_dictionary_error(self, mock_get):
        """
        Test handling of errors during dictionary extraction.
        """
        # Simulate request error
        mock_get.side_effect = requests.exceptions.RequestException("Request failed")
        
        # Verify function raises the error
        with pytest.raises(requests.exceptions.RequestException):
            extract.extract_dictionary()

class TestExtractOrganizations:
    
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_organizations_success(self, mock_file, mock_get, sample_organizations_data):
        """
        Test successful extraction of organizations.
        """
        search_response = http_response({
            "_embedded": {
                "results": [
                    {"_id": "result1", "organizationHierarchy": [{"organizationId": "org1"}]},
                    {"_id": "result2", "organizationHierarchy": [{"organizationId": "org2"}]}
                ]
            }
        })
        org_response1 = http_response({
            "_embedded": [{"org": sample_organizations_data[0]}]
        })
        org_response2 = http_response({
            "_embedded": [{"org": sample_organizations_data[1]}]
        })
        
        # Set up the mock to return different responses
        mock_get.side_effect = [search_response, org_response1, org_response2]
        
        # Call the function
        extract.extract_organizations()
        
        # Check if the requests were made correctly
        assert mock_get.call_count == 3
        
        # Check if the file was opened
        mock_file.assert_called_once()
    
    @patch('requests.get')
    def test_extract_organizations_error(self, mock_get):
        """
        Test handling of errors during organization extraction.
        """
        search_response = http_response({
            "_embedded": {
                "results": [
                    {"_id": "result1", "organizationHierarchy": [{"organizationId": "org1"}]}
                ]
            }
        })
        
        # Simulate error on second request
        mock_get.side_effect = [
            search_response,
            requests.exceptions.RequestException("Request failed")
        ]
        
        # Verify function raises the error
        with pytest.raises(requests.exceptions.RequestException):
            extract.extract_organizations()

class TestExtractUSASpendingAwardHashes:
    
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('requests.post')
    @patch('requests.get')
    @patch('json.dumps')
    def test_extract_usaspending_award_hashes_success(self, mock_dumps, mock_get, mock_post, mock_file, mock_load):
        """
        Test successful extraction of USAspending award hashes.
        """
        # Mock load assistance listings
        mock_load.return_value = [
            {"data": {"programNumber": "10.001"}}
        ]
        
        cfda_response = http_response({
            "results": [
                {
                    "program_number": "10.001",
                    "program_title": "Sample Program",
                    "identifier": "10.001"
                }
            ]
        })
        filter_response = http_response({"hash": "abc123hash"})
        
        # One get and one post
        mock_get.return_value = cfda_response
        mock_post.return_value = filter_response
        
        # Set up the dumps return value
        mock_dumps.return_value = '{"10.001": "abc123hash"}'
        
        # Call the function
        extract.extract_usaspending_award_hashes()
        
        # Verify the file is written
        mock_file.assert_called()
    
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('time.sleep')
    def test_extract_usaspending_award_hashes_connection_error_current(self, mock_sleep, mock_file, mock_load):
        """
        After the hash request retries are exhausted, the function raises.
        """
        # Mock load assistance listings
        mock_load.return_value = [
            {"data": {"programNumber": "10.001"}}
        ]

        cfda_response = http_response({
            "results": [
                {
                    "program_number": "10.001",
                    "program_title": "Sample Program",
                    "identifier": "10.001"
                }
            ]
        })

        def post_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            if "autocomplete/cfda" in url:
                return cfda_response
            raise requests.exceptions.ConnectionError("Connection failed")

        with patch("requests.post", side_effect=post_side_effect):
            with pytest.raises(RuntimeError, match="exceeded maximum tries"):
                extract.extract_usaspending_award_hashes()

class TestCleanJSONData:
    
    @patch('json.load')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_clean_json_data_success(self, mock_file, mock_dump, mock_load):
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
    
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_clean_json_data_file_not_found(self, mock_file, mock_exists):

        with pytest.raises(FileNotFoundError):
            extract.clean_json_data("nonexistent.json")

class TestCleanAllData:
    
    @patch('data_processing.extract.clean_json_data')
    def test_clean_all_data_success(self, mock_clean_json_data):
        """
        Test successful cleaning of all data files.
        """
        # Call the function
        extract.clean_all_data()
        
        # Check if clean_json_data was called for each file
        assert mock_clean_json_data.call_count == 2
        mock_clean_json_data.assert_any_call("assistance-listings.json")
        mock_clean_json_data.assert_any_call("dictionary.json")
