# Federal Program Inventory - Unit Test Suite

This directory contains unit tests for the Federal Program Inventory data processing pipeline. 

# Test Structure

conftest.py: Contains shared fixtures and test setup
test_extract.py: Tests for data extraction functionality
test_transform.py: Tests for data transformation functionality
test_load.py: Tests for data loading/generation functionality
test_constants.py: Tests for constants and configuration

Run all tests: pytest
Run with coverage report: pytest --cov=data_processing
Run a specific test file: pytest tests/test_extract.py
Run for detailed HTML coverage report(will create html folder): pytest --cov=data_processing --cov-report=html


# What These Tests Cover

Each test focuses on one specific functionality, and I've tried to cover both the "happy path" and edge cases.
Tests check:
- Data extraction from external sources (with mocked network requests)
- Data validation and cleaning
- Transformation logic: normalization and categorization
- Data loading to CSV and JSON files
- Utility functions for config loading and formatting


# Notes on Mocking

- File system operations (using unittest.mock.patch)
- External API calls to SAM.gov and USASpending.gov
- Database operations (using in-memory SQLite)
- This way is more reliable and efficient

Using pytest's mocking to avoid:
- Real network requests
- Actual file operations
- Dependencies between tests


# Adding New Tests

- Create test functions with a clear descriptive names that explain what they're testing
- Test happy path and edge case scenarios
- Use fixtures from conftest.py
- Keep tests independent of each other
