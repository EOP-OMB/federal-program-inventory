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
import sqlite3
from unittest.mock import MagicMock, patch

# Project root to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Making sure constants is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data_processing')))

os.environ['ETL_EXTRACT_DISK_DIRECTORY'] = '/'
os.environ['ETL_EXTRACT_SOURCE_DIRECTORY'] = 'data_processing/source'
os.environ['ETL_EXTRACT_EXTRACTED_DIRECTORY'] = 'data_processing/extracted'

@pytest.fixture(autouse=True)
def patch_paths():
    """Patch file paths to prevent file access issues."""
    with patch.object(os.path, 'exists', return_value=True), \
         patch.object(os, 'makedirs', return_value=None):
        yield

@pytest.fixture
def sample_assistance_listing():
    """Sample data for testing."""
    return {
        "id": "sample-id",
        "data": {
            "programNumber": "10.001",
            "title": "Sample Program",
            "organizationId": "123456",
            "objective": "Sample objective text",
            "alternativeNames": ["Popular Name"],
            "compliance": {
                "CFR200Requirements": {
                    "questions": [
                        {"code": "subpartF", "isSelected": True}
                    ]
                },
                "documents": {
                    "description": "Sample rules text"
                }
            },
            "financial": {
                "accomplishments": {
                    "list": [
                        {"fiscalYear": 2023, "description": "Sample result"}
                    ]
                },
                "obligations": [
                    {
                        "assistanceType": "01",
                        "values": [
                            {"year": 2023, "actual": 1000000, "estimate": None},
                            {"year": 2024, "actual": None, "estimate": 1200000}
                        ]
                    }
                ]
            },
            "authorizations": {
                "list": [
                    {
                        "authorizationTypes": {
                            "act": True,
                            "statute": None,
                            "publicLaw": None,
                            "USC": None,
                            "executiveOrder": None
                        },
                        "act": {
                            "title": "Sample Act",
                            "part": "Part 100",
                            "section": "Section 5",
                            "description": "Sample description"
                        }
                    }
                ]
            },
            "eligibility": {
                "applicant": {
                    "types": ["01", "02"]
                },
                "beneficiary": {
                    "types": ["01", "02"]
                }
            }
        }
    }

@pytest.fixture
def sample_raw_data():
    """Sample data for testing extraction functions."""
    return pd.DataFrame({
        'program_name': ['Program A', 'Program B', 'Program C'],
        'agency': ['Agency X', 'Agency Y', 'Agency Z'],
        'funding_amount': [1000000, 2000000, 3000000],
        'description': ['Description A', 'Description B', 'Description C']
    })

@pytest.fixture
def sample_transformed_data():
    """Sample data for testing transform functions."""
    return pd.DataFrame({
        'program_id': ['A001', 'B002', 'C003'],
        'program_name': ['Program A', 'Program B', 'Program C'],
        'agency_id': ['X', 'Y', 'Z'],
        'agency_name': ['Agency X', 'Agency Y', 'Agency Z'],
        'funding_amount': [1000000, 2000000, 3000000],
        'description': ['Description A', 'Description B', 'Description C'],
        'category': ['Grants', 'Loans', 'Direct Payments']
    })

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

@pytest.fixture
def sample_usaspending_hash_data():
    """Sample USASpending.gov hash data."""
    return {
        "10.001": "abc123hash",
        "10.002": "def456hash"
    }

@pytest.fixture
def mock_sqlite_connection():
    """Create an in-memory SQLite database for testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

@pytest.fixture
def mock_sqlite_cursor(mock_sqlite_connection):
    """Get a cursor for the in-memory SQLite database."""
    return mock_sqlite_connection.cursor()

@pytest.fixture
def setup_temp_db(mock_sqlite_connection, mock_sqlite_cursor):
    # Create agency table
    mock_sqlite_cursor.execute('''
        CREATE TABLE agency (
            id INTEGER PRIMARY KEY,
            agency_name TEXT,
            tier_1_agency_id INTEGER,
            tier_2_agency_id INTEGER,
            is_cfo_act_agency INTEGER DEFAULT 0
        )
    ''')
    
    # Create program table
    mock_sqlite_cursor.execute('''
        CREATE TABLE program (
            id TEXT PRIMARY KEY,
            agency_id INTEGER,
            name TEXT,
            popular_name TEXT,
            objective TEXT,
            sam_url TEXT,
            usaspending_awards_hash TEXT,
            usaspending_awards_url TEXT,
            grants_url TEXT,
            program_type TEXT,
            is_subpart_f BOOLEAN,
            rules_regulations TEXT
        )
    ''')
    
    # Create category table
    mock_sqlite_cursor.execute('''
        CREATE TABLE category (
            id TEXT NOT NULL,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            parent_id TEXT,
            PRIMARY KEY(id, type)
        )
    ''')
    
    # Create program_to_category table
    mock_sqlite_cursor.execute('''
        CREATE TABLE program_to_category (
            program_id TEXT NOT NULL,
            category_id TEXT NOT NULL,
            category_type TEXT NOT NULL,
            PRIMARY KEY (program_id, category_id, category_type)
        )
    ''')
    
    # Create program_sam_spending table
    mock_sqlite_cursor.execute('''
        CREATE TABLE program_sam_spending (
            program_id TEXT NOT NULL,
            assistance_type TEXT,
            fiscal_year INTEGER NOT NULL,
            is_actual INTEGER NOT NULL,
            amount REAL NOT NULL,
            PRIMARY KEY (program_id, assistance_type, fiscal_year, is_actual)
        )
    ''')
    
    # Insert sample data
    mock_sqlite_cursor.execute('''
        INSERT INTO agency VALUES (100000000, "Department of Agriculture", 100000000, NULL, 1)
    ''')
    
    mock_sqlite_cursor.execute('''
        INSERT INTO program VALUES (
            "10.001", 100000000, "Sample Program", "Popular Name", 
            "Sample objective text", "https://sam.gov/fal/sample-id/view",
            "abc123hash", "https://www.usaspending.gov/search/?hash=abc123hash",
            "https://grants.gov/search-grants?cfda=10.001", "assistance_listing", 1,
            "Sample rules text"
        )
    ''')
    
    mock_sqlite_cursor.execute('''
        INSERT INTO category VALUES ("01", "assistance", "Formula Grants", NULL)
    ''')
    
    mock_sqlite_cursor.execute('''
        INSERT INTO program_to_category VALUES ("10.001", "01", "assistance")
    ''')
    
    mock_sqlite_cursor.execute('''
        INSERT INTO program_sam_spending VALUES ("10.001", "01", 2023, 1, 1000000)
    ''')
    
    mock_sqlite_connection.commit()
    
    return mock_sqlite_connection

@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    with patch('os.path.exists', return_value=True), \
         patch('os.makedirs'), \
         patch('builtins.open', new_callable=MagicMock):
        yield

@pytest.fixture
def mock_requests():
    """Mock requests for API calls."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        # Configure default responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        
        yield {
            'get': mock_get,
            'post': mock_post,
            'response': mock_response
        }

# Add version of tabula
@pytest.fixture(autouse=True)
def patch_tabula():
    with patch('tabula.read_pdf', return_value=[pd.DataFrame()]), \
         patch.dict(sys.modules, {'tabula': MagicMock(__version__='1.0.0')}):
        yield