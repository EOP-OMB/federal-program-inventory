"""
This is a simple set of tests to make sure constants are properly defined
"""

import pytest
import re
from datetime import datetime
# Import the module
from data_processing import constants

class TestConstants:
    """Tests for our constants module"""
    def test_fiscal_year_defined(self):
        """
        Check that the global fiscal year/date variables are defined.
        """
        # Todo: add tests for all of the newly created global variables and run the tests. 
        assert hasattr(constants, 'LAST_COMPLETED_FISCAL_YEAR')
        assert isinstance(constants.LAST_COMPLETED_FISCAL_YEAR, str)
        assert hasattr(constants, 'CURRENT_FISCAL_YEAR')
        assert isinstance(constants.CURRENT_FISCAL_YEAR, str)
        assert hasattr(constants, 'SITE_UPDATE_DATE')
        assert isinstance(constants.SITE_UPDATE_DATE, str)
        assert hasattr(constants, 'SAMGOV_ASSISTANCE_LISTINGS_DATE')
        assert isinstance(constants.SAMGOV_ASSISTANCE_LISTINGS_DATE, str)
        assert hasattr(constants, 'USASPENDING_TRANSACTION_DATE')
        assert isinstance(constants.USASPENDING_TRANSACTION_DATE, str)
        assert hasattr(constants, 'TREASURYGOV_TAX_EXPEND_DATE')
        assert isinstance(constants.TREASURYGOV_TAX_EXPEND_DATE, str)
        assert hasattr(constants, 'PAYMENTACCURACY_FY_DATE')
        assert isinstance(constants.PAYMENTACCURACY_FY_DATE, str)
        # Should be a 4-digit year
        assert len(constants.LAST_COMPLETED_FISCAL_YEAR) == 4
        assert constants.LAST_COMPLETED_FISCAL_YEAR.isdigit()
        assert len(constants.CURRENT_FISCAL_YEAR) == 4
        assert constants.CURRENT_FISCAL_YEAR.isdigit()
        assert len(constants.PAYMENTACCURACY_FY_DATE) == 4
        assert constants.PAYMENTACCURACY_FY_DATE.isdigit()
        

        # Helper to check 'Month Day, Year' format and real date
        def assert_valid_month_day_year(date_str, label):
            match = re.match(r"^([A-Z][a-z]+) (\d{1,2}), (\d{4})$", date_str)
            assert match is not None, f"{label} format should be 'Month Day, Year'"
            month = match.group(1)
            day = int(match.group(2))
            year = int(match.group(3))
            try:
                datetime.strptime(f"{month} {day} {year}", "%B %d %Y")
            except ValueError:
                assert False, f"{label} '{date_str}' is not a valid calendar date"

        # Check all relevant date constants
        assert_valid_month_day_year(constants.SITE_UPDATE_DATE, "SITE_UPDATE_DATE")
        assert_valid_month_day_year(constants.SAMGOV_ASSISTANCE_LISTINGS_DATE, "SAMGOV_ASSISTANCE_LISTINGS_DATE")
        assert_valid_month_day_year(constants.USASPENDING_TRANSACTION_DATE, "USASPENDING_TRANSACTION_DATE")
        assert_valid_month_day_year(constants.TREASURYGOV_TAX_EXPEND_DATE, "TREASURYGOV_TAX_EXPEND_DATE")
    
    def test_agency_display_names(self):
        """
        Test the agency display name mapping.
        """
        assert hasattr(constants, 'AGENCY_DISPLAY_NAMES')
        assert isinstance(constants.AGENCY_DISPLAY_NAMES, dict)
        assert len(constants.AGENCY_DISPLAY_NAMES) > 0

        # Test that each key and value is a non-empty string
        for key, value in constants.AGENCY_DISPLAY_NAMES.items():
            assert key is not None, f"Key is None"
            assert isinstance(key, str), f"Key is not a string: {type(key)}"
            assert len(key) > 0, f"Key is an empty string"
            assert value is not None, f"Value for key '{key}' is None"
            assert isinstance(value, str), f"Value for key '{key}' is not a string: {type(value)}"
            assert len(value) > 0, f"Value for key '{key}' is an empty string"
    
    def test_assistance_type_display_names(self):
        """
        Test the assistance type display name mapping.
        """
        assert hasattr(constants, 'ASSISTANCE_TYPE_DISPLAY_NAMES')
        assert isinstance(constants.ASSISTANCE_TYPE_DISPLAY_NAMES, dict)
        assert len(constants.ASSISTANCE_TYPE_DISPLAY_NAMES) > 0

        # Test that each key and value is a non-empty string
        for key, value in constants.ASSISTANCE_TYPE_DISPLAY_NAMES.items():
            assert key is not None, f"Key is None"
            assert isinstance(key, str), f"Key is not a string: {type(key)}"
            assert len(key) > 0, f"Key is an empty string"
            assert value is not None, f"Value for key '{key}' is None"
            assert isinstance(value, str), f"Value for key '{key}' is not a string: {type(value)}"
            assert len(value) > 0, f"Value for key '{key}' is an empty string"
    
    def test_cfo_act_agency_names(self):
        """
        Test the CFO Act agency list.
        """
        assert hasattr(constants, 'CFO_ACT_AGENCY_NAMES')
        assert isinstance(constants.CFO_ACT_AGENCY_NAMES, list)
        assert len(constants.CFO_ACT_AGENCY_NAMES) > 0
        
        # Test that each item is a non-empty string
        for agency in constants.CFO_ACT_AGENCY_NAMES:
            assert agency is not None, f"Agency item is None"
            assert isinstance(agency, str), f"Agency item is not a string: {type(agency)}"
            assert len(agency) > 0, f"Agency item is an empty string"
    
    def test_program_type_mapping(self):
        """
        Test the program type display mapping.
        """
        assert hasattr(constants, 'PROGRAM_TYPE_MAPPING')
        assert isinstance(constants.PROGRAM_TYPE_MAPPING, dict)
        assert len(constants.PROGRAM_TYPE_MAPPING) > 0
        
        # Test that each key and value is a non-empty string
        for key, value in constants.PROGRAM_TYPE_MAPPING.items():
            assert key is not None, f"Key is None"
            assert isinstance(key, str), f"Key is not a string: {type(key)}"
            assert len(key) > 0, f"Key is an empty string"
            assert value is not None, f"Value for key '{key}' is None"
            assert isinstance(value, str), f"Value for key '{key}' is not a string: {type(value)}"
            assert len(value) > 0, f"Value for key '{key}' is an empty string"