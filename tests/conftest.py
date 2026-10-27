"""
This file contains all the test fixtures and mock setup we need for testing
the data processing modules. I'm using pytest fixtures to avoid repeating
setup code across different test files.
"""
import os
import sys
import json
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

# Project root to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Making sure constants is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data_processing')))

os.environ['ETL_EXTRACT_DISK_DIRECTORY'] = '/'
os.environ['ETL_EXTRACT_SOURCE_DIRECTORY'] = 'data_processing/source'
os.environ['ETL_EXTRACT_EXTRACTED_DIRECTORY'] = 'data_processing/extracted'
os.environ.setdefault('ETL_TRANSFORM_TEMP_DB_DISK_DIRECTORY', '/tmp/')
os.environ.setdefault('ETL_TRANSFORM_TEMP_DB_FILE_PATH', 'temp_data.db')
os.environ.setdefault('ETL_TRANSFORM_TRANSFORMED_FILES_DIRECTORY', '/tmp/')
os.environ.setdefault('ETL_TRANSFORM_TRANSFORMED_DB_FILE_PATH', 'transformed_data.db')
os.environ.setdefault('ETL_TRANSFORM_USASPENDING_DISK_DIRECTORY', '/tests/fixtures/transform/usaspending/')
os.environ.setdefault('ETL_TRANSFORM_EXTRACTED_FILES_DIRECTORY', 'tests/fixtures/transform/extracted/')
os.environ.setdefault('ETL_TRANSFORM_ASSISTANCE_ZIP_FILE_DIRECTORY', '/tests/fixtures/transform/usaspending/assistance/')
os.environ.setdefault('ETL_TRANSFORM_CONTRACT_ZIP_FILE_DIRECTORY', '/tests/fixtures/transform/usaspending/contracts/')
os.environ.setdefault('ETL_TRANSFORM_UNZIP_TMP_DIRECTORY', '/tmp/unzip/')


def http_response(payload=None, text=None, status_code=200):
    """Build a mock requests.Response with status, text, and json()."""
    response = MagicMock()
    response.status_code = status_code
    if payload is not None:
        response.json.return_value = payload
        response.text = json.dumps(payload) if text is None else text
    else:
        response.json.return_value = {}
        response.text = "" if text is None else text
    response.raise_for_status.return_value = None
    return response


@pytest.fixture(autouse=True)
def patch_paths():
    """Patch file paths to prevent file access issues."""
    with patch.object(os.path, 'exists', return_value=True), \
         patch.object(os, 'makedirs', return_value=None):
        yield

@pytest.fixture
def sample_dictionary_data():
    """Sample data from SAM.gov."""
    return {
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
                                    "value": "Formula Grant Sub-type"
                                }
                            ]
                        },
                        {
                            "element_id": "02",
                            "value": "PROJECT GRANTS",
                            "elements": []
                        }
                    ]
                },
                {
                    "id": "applicant_types",
                    "elements": [
                        {
                            "element_id": "01",
                            "value": "State Government"
                        },
                        {
                            "element_id": "02",
                            "value": "Local Government"
                        }
                    ]
                },
                {
                    "id": "beneficiary_types",
                    "elements": [
                        {
                            "element_id": "01",
                            "value": "Individual/Family"
                        },
                        {
                            "element_id": "02",
                            "value": "Minority group"
                        }
                    ]
                }
            ]
        }
    }

@pytest.fixture
def sample_organizations_data():
    """Sample data from SAM.gov."""
    return [
        {
            "orgKey": "100000000",
            "name": "Department of Agriculture",
            "agencyName": "AGRICULTURE, DEPARTMENT OF",
            "l1OrgKey": "100000000",
            "l2OrgKey": None
        },
        {
            "orgKey": "100001234",
            "name": "Food and Nutrition Service",
            "agencyName": None,
            "l1OrgKey": "100000000",
            "l2OrgKey": "100001234"
        }
    ]

# Add version of tabula
@pytest.fixture(autouse=True)
def patch_tabula():
    with patch('tabula.read_pdf', return_value=[pd.DataFrame()]), \
         patch.dict(sys.modules, {'tabula': MagicMock(__version__='1.0.0')}):
        yield
