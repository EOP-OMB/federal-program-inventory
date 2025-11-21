# Data Dictionary

This document describes the database schema and data structures used in the OMB Federal Program Inventory (FPI) data transformation process.

> **See also**: [Entity Relationship Diagram (ERD)](ERD.md) for visual representation of table relationships.

## Database Overview

The transformation process uses SQLite databases to store:
- Extracted program data from SAM.gov
- USASpending.gov financial data
- Taxonomy classifications (GWO, PON, Categories, Focus Areas)
- Additional program data from supplementary sources

## Tables

### agency

Stores agency and sub-agency information from SAM.gov organizations data.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, NOT NULL | Unique identifier for the agency (from SAM.gov orgKey) |
| agency_name | TEXT | | Display name of the agency |
| tier_1_agency_id | INTEGER | FOREIGN KEY REFERENCES agency(id) | Reference to parent tier 1 agency |
| tier_2_agency_id | INTEGER | FOREIGN KEY REFERENCES agency(id) | Reference to parent tier 2 agency |
| is_cfo_act_agency | INTEGER | NOT NULL, DEFAULT 0 | Boolean flag (0/1) indicating if this is a CFO Act agency |

**Source**: `organizations.json` from SAM.gov  
**API**: 
- https://sam.gov/api/prod/sgs/v1/search/?index=cfda&page=0&mode=search&size=10000&is_active=true

**Notes**: 
- Agency names are normalized using `constants.AGENCY_DISPLAY_NAMES`
- CFO Act agencies are identified using `constants.CFO_ACT_AGENCY_NAMES`
- Self-referential foreign keys allow hierarchical agency structures
- Data is extracted using SAM.gov's frontend APIs (not officially documented)

---

### category

Stores categorical classifications including assistance types, applicant types, and beneficiary types.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | TEXT | PRIMARY KEY, NOT NULL | Unique identifier for the category element |
| type | TEXT | PRIMARY KEY, NOT NULL | Category type: 'assistance', 'applicant', or 'beneficiary' |
| name | TEXT | NOT NULL | Display name of the category |
| parent_id | TEXT | FOREIGN KEY REFERENCES category(id, type) | Reference to parent category (for hierarchical categories) |

**Source**: `dictionary.json` from SAM.gov  
**API**: 
- https://sam.gov/api/prod/fac/v1/programs/dictionaries?ids=match_percent,assistance_type,applicant_types,assistance_usage_types,beneficiary_types,cfr200_requirements&size=&filterElementIds=&keyword=

**Notes**:
- Composite primary key (id, type)
- Assistance types can have parent-child relationships
- Applicant and beneficiary types are flat (no parent_id)
- Data is extracted using SAM.gov's frontend APIs (not officially documented)

---

### program

Core table storing program information from SAM.gov assistance listings.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | TEXT | PRIMARY KEY, NOT NULL | Program identifier (CFDA number) |
| agency_id | INTEGER | FOREIGN KEY REFERENCES agency(id) | Reference to the administering agency |
| name | TEXT | | Official program title |
| popular_name | TEXT | | Alternative/popular name for the program |
| objective | TEXT | | Program description |
| sam_url | TEXT | | URL to program page on SAM.gov |
| usaspending_awards_hash | TEXT | | Hash for USASpending.gov search URL |
| usaspending_awards_url | TEXT | | Full URL to USASpending.gov search results |
| grants_url | TEXT | | URL to Grants.gov search page |
| program_type | TEXT | | Type: 'assistance_listing', 'interest', 'tax_expenditure' |
| is_subpart_f | BOOLEAN | | Boolean flag indicating Subpart F compliance requirement |
| rules_regulations | TEXT | | Description of rules and regulations |

**Source**: `assistance-listings.json` from SAM.gov and `additional-programs.csv`  
**API**: 
- https://sam.gov/api/prod/sgs/v1/search/?index=cfda&page=0&mode=search&size=10000&is_active=true

**Notes**:
- Popular name comes from `alternativeNames[0]` in SAM.gov data
- USASpending URLs are constructed from hashes in `usaspending-program-search-hashes.json`
- Subpart F flag is determined from compliance questions in SAM.gov data
- Data is extracted using SAM.gov's frontend APIs (not officially documented)

---

### program_authorization

Stores program authorization information (acts, statutes, public laws, USC, executive orders).

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| program_id | TEXT | FOREIGN KEY REFERENCES program(id), NOT NULL | Reference to the program |
| text | TEXT | | Formatted authorization text |
| url | TEXT | | URL to the authorization document (GovInfo.gov) |

**Source**: `assistance-listings.json` from SAM.gov  
**API**: 
- https://sam.gov/api/prod/sgs/v1/search/?index=cfda&page=0&mode=search&size=10000&is_active=true

**Notes**:
- Multiple authorization types can be combined into a single text field
- URLs are generated for statutes, public laws, and USC references when numeric values are available
- Format: "Act Title, Part, Section, Description. Stat. Volume Page. Pub. L. Congress Number. Title U.S.C. § Section. Executive Order details."
- Data is extracted using SAM.gov's frontend APIs (not officially documented)

---

### program_result

Stores program accomplishments/results by fiscal year.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| program_id | TEXT | FOREIGN KEY REFERENCES program(id), NOT NULL | Reference to the program |
| fiscal_year | INTEGER | NOT NULL | Fiscal year of the result |
| result | TEXT | NOT NULL | Description of the program result/accomplishment |

**Source**: `assistance-listings.json` from SAM.gov  
**API**: 
- https://sam.gov/api/prod/sgs/v1/search/?index=cfda&page=0&mode=search&size=10000&is_active=true

**Notes**:
- Composite primary key (program_id, fiscal_year)
- Data comes from `financial.accomplishments.list` in SAM.gov data
- Data is extracted using SAM.gov's frontend APIs (not officially documented)

---

### program_sam_spending

Stores spending data from SAM.gov (obligations) by program, assistance type, and fiscal year.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| program_id | TEXT | FOREIGN KEY REFERENCES program(id), NOT NULL | Reference to the program |
| assistance_type | TEXT | | Assistance type identifier |
| category_type | TEXT | | Category type (typically 'assistance') |
| fiscal_year | INTEGER | NOT NULL | Fiscal year |
| is_actual | INTEGER | NOT NULL | Boolean flag: 1 = actual, 0 = estimate |
| amount | REAL | NOT NULL | Spending amount in dollars |

**Source**: `assistance-listings.json` from SAM.gov  
**API**: 
- https://sam.gov/api/prod/sgs/v1/search/?index=cfda&page=0&mode=search&size=10000&is_active=true

**Notes**:
- Composite primary key (program_id, assistance_type, fiscal_year, is_actual)
- Uses `ON CONFLICT DO UPDATE SET amount=amount+?` to handle duplicates
- Foreign key to category table for assistance_type validation
- Data is extracted using SAM.gov's frontend APIs (not officially documented)

---

### program_to_category

Junction table linking programs to their categorical classifications.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| program_id | TEXT | FOREIGN KEY REFERENCES program(id), NOT NULL | Reference to the program |
| category_id | TEXT | NOT NULL | Category identifier |
| category_type | TEXT | NOT NULL | Category type: 'assistance', 'applicant', or 'beneficiary' |

**Source**: `assistance-listings.json` from SAM.gov  
**API**: 
- https://sam.gov/api/prod/sgs/v1/search/?index=cfda&page=0&mode=search&size=10000&is_active=true

**Notes**:
- Composite primary key (program_id, category_id, category_type)
- Links programs to assistance types, applicant types, and beneficiary types
- Uses `ON CONFLICT DO NOTHING` to prevent duplicate entries
- Data is extracted using SAM.gov's frontend APIs (not officially documented)

---

### taxonomy_category

Stores taxonomy category classifications (e.g., "Business and Commerce", "Health").

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | TEXT | PRIMARY KEY, NOT NULL | Unique identifier for the taxonomy category |
| category | TEXT | NOT NULL, UNIQUE | Category name (dashes replaced with en-dashes) |

**Source**: `Taxonomy_GWO_crosswalk.csv` and `Taxonomy_PON_crosswalk.csv`  
**Notes**:
- Dashes are replaced with en-dashes (U+2013) for consistency
- Used as parent for focus areas

---

### taxonomy_focus_area

Stores taxonomy focus area classifications (subcategories within taxonomy categories).

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | TEXT | PRIMARY KEY, NOT NULL | Unique identifier for the focus area (FA Code) |
| focus_area | TEXT | NOT NULL, UNIQUE | Focus area name (dashes replaced with en-dashes) |
| category_id | TEXT | FOREIGN KEY REFERENCES taxonomy_category(id), NOT NULL | Reference to parent taxonomy category |

**Source**: `Taxonomy_GWO_crosswalk.csv` and `Taxonomy_PON_crosswalk.csv`  
**Notes**:
- Dashes are replaced with en-dashes for consistency
- Links to taxonomy_category as parent

---

### gwo

Stores Government-Wide Outcomes (GWO) definitions and classifications.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | TEXT | PRIMARY KEY, NOT NULL | GWO identifier |
| gwo | TEXT | NOT NULL | GWO name/title |
| gwo_definition | TEXT | NOT NULL | Full definition of the GWO |
| focus_area_id | TEXT | FOREIGN KEY REFERENCES taxonomy_focus_area(id), NOT NULL | Reference to the focus area this GWO belongs to |

**Source**: `Taxonomy_GWO_crosswalk.csv`  
**Notes**:
- Each GWO is associated with a focus area
- Used for program classification via program_to_gwo table

---

### pon

Stores Program Outcome Numbers (PON) definitions and classifications.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | TEXT | PRIMARY KEY, NOT NULL | PON identifier |
| pon2 | TEXT | NOT NULL | PON name/title |
| pon_definition | TEXT | NOT NULL | Full definition of the PON |
| focus_area_id | TEXT | FOREIGN KEY REFERENCES taxonomy_focus_area(id), NOT NULL | Reference to the focus area this PON belongs to |

**Source**: `Taxonomy_PON_crosswalk.csv`  
**Notes**:
- Each PON is associated with a focus area
- Used for program classification via program_to_pon table

---

### program_to_gwo

Junction table linking programs to Government-Wide Outcomes (GWO).

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| program_id | TEXT | FOREIGN KEY REFERENCES program(id), NOT NULL | Reference to the program (CFDA number) |
| gwo_id | TEXT | FOREIGN KEY REFERENCES gwo(id), NOT NULL | Reference to the GWO |

**Source**: `FPI_GWO_assignment.csv`  
**Notes**:
- Maps programs to their assigned GWOs
- Multiple GWOs can be assigned to a single program

---

### program_to_pon

Junction table linking programs to Program Outcome Numbers (PON).

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| program_id | TEXT | FOREIGN KEY REFERENCES program(id), NOT NULL | Reference to the program (CFDA number) |
| pon_id | TEXT | FOREIGN KEY REFERENCES pon(id), NOT NULL | Reference to the PON |

**Source**: `FPI_PON_assignment.csv`  
**Notes**:
- Maps programs to their assigned PONs
- Multiple PONs can be assigned to a single program

---

### usaspending_assistance

Temporary table storing raw USASpending.gov assistance transaction data.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| assistance_transaction_unique_key | TEXT | PRIMARY KEY, NOT NULL | Unique transaction identifier |
| assistance_award_unique_key | TEXT | | Unique award identifier |
| federal_action_obligation | REAL | | Obligation amount for this transaction |
| total_outlayed_amount_for_overall_award | REAL | | Total outlayed amount for the entire award |
| action_date_fiscal_year | INTEGER | | Fiscal year of the transaction action date |
| prime_award_transaction_place_of_performance_cd_current | TEXT | | Congressional district code |
| cfda_number | TEXT | | CFDA program number |
| assistance_type_code | INTEGER | | Assistance type code |

**Source**: USASpending.gov CSV files
**Notes**:
- Stored in temporary database (`temp_data.db`)
- Used for aggregation into final tables
- Delta files can update or delete records
- Data downloaded from [USASpending.gov Award Data Archive](https://www.usaspending.gov/download_center/award_data_archive)

---

### usaspending_contract

Temporary table storing raw USASpending.gov contract transaction data.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| contract_transaction_unique_key | TEXT | PRIMARY KEY, NOT NULL | Unique transaction identifier |
| contract_award_unique_key | TEXT | | Unique award identifier |
| federal_action_obligation | REAL | | Obligation amount for this transaction |
| total_outlayed_amount_for_overall_award | REAL | | Total outlayed amount for the entire award |
| action_date_fiscal_year | INTEGER | | Fiscal year of the transaction action date |
| funding_agency_code | TEXT | | Funding agency code |
| funding_agency_name | TEXT | | Funding agency name |
| funding_sub_agency_code | TEXT | | Funding sub-agency code |
| funding_sub_agency_name | TEXT | | Funding sub-agency name |
| funding_office_code | TEXT | | Funding office code |
| funding_office_name | TEXT | | Funding office name |
| prime_award_transaction_place_of_performance_cd_current | TEXT | | Congressional district code |
| award_type_code | TEXT | | Award type code |

**Source**: USASpending.gov CSV files
**Notes**:
- Stored in temporary database (`temp_data.db`)
- Currently not aggregated into final tables (may be used for future features)
- Data downloaded from [USASpending.gov Award Data Archive](https://www.usaspending.gov/download_center/award_data_archive)

---

### usaspending_assistance_obligation_aggregation

Aggregated obligation data from USASpending.gov by program, fiscal year, assistance type, and congressional district.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| cfda_number | TEXT | FOREIGN KEY REFERENCES program(id), NOT NULL | Program identifier (CFDA number) |
| action_date_fiscal_year | INTEGER | NOT NULL | Fiscal year of the transaction |
| assistance_type_code | INTEGER | NOT NULL | Assistance type code |
| congressional_district | TEXT | | Congressional district code |
| obligations | REAL | NOT NULL | Sum of federal_action_obligation for this grouping |

**Source**: Aggregated from `usaspending_assistance` table
**Notes**:
- Aggregated using `GROUP BY cfda_number, action_date_fiscal_year, assistance_type_code, congressional_district`
- Sums `federal_action_obligation` for each group
- Source data downloaded from USASpending.gov Award Data Archives

---

### usaspending_assistance_outlay_aggregation

Aggregated outlay and obligation data from USASpending.gov by program and award first fiscal year.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| cfda_number | TEXT | FOREIGN KEY REFERENCES program(id), NOT NULL | Program identifier (CFDA number) |
| award_first_fiscal_year | INTEGER | NOT NULL | First fiscal year of transactions for the award |
| outlay | REAL | NOT NULL | Sum of total_outlayed_amount_for_overall_award |
| obligation | REAL | NOT NULL | Sum of federal_action_obligation |

**Source**: Aggregated from `usaspending_assistance` table
**Notes**:
- Uses `MIN(action_date_fiscal_year)` as `award_first_fiscal_year` to ensure consistent date attribution
- Aggregates by award first, then by program and fiscal year
- Methodology differs from obligation aggregation to allow consistent outlay/obligation comparison
- Source data downloaded from USASpending.gov Award Data Archives

---

### other_program_spending

Stores spending data for programs not in SAM.gov (interest on public debt, tax expenditures).

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| program_id | TEXT | FOREIGN KEY REFERENCES program(id), NOT NULL | Reference to the program |
| fiscal_year | INTEGER | NOT NULL | Fiscal year |
| outlays | REAL | | Outlay amount |
| forgone_revenue | REAL | | Forgone revenue amount (for tax expenditures) |
| source | TEXT | NOT NULL | Source of the data (e.g., 'additional-programs.csv') |
| focus_area_id | TEXT | FOREIGN KEY REFERENCES taxonomy_focus_area(id), NOT NULL | Reference to the focus area for taxonomy classification |

**Source**: `additional-programs.csv`  
**Notes**:
- Composite primary key (program_id, fiscal_year)
- Used for interest on public debt and tax expenditure programs
- Columns named with fiscal year pattern: `{year}_outlays`, `{year}_foregone_revenue`
- See the data_processing/README.md for further details on data sources

---

### improper_payment_mapping

Stores improper payment data mapped to programs.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| program_id | TEXT | FOREIGN KEY REFERENCES program(id), NOT NULL | Reference to the program |
| improper_payment_program_name | TEXT | | Name of the program in improper payment reporting |
| outlays | DECIMAL | | Program outlays amount |
| improper_payment_amount | DECIMAL | | Total improper payment amount |
| insufficient_documentation_amount | DECIMAL | | Amount attributed to insufficient documentation |
| high_priority_program | INTEGER | | Boolean flag (0/1) indicating high priority program status |

**Source**: `improper-payment-program-mapping.csv`  
**Notes**:
- Monetary values are cleaned (removes $ and commas) before insertion
- High priority flag is converted from boolean to integer
- Source data generated from paymentaccuracy.gov

---

## Views

### program_taxonomy_lookup

A view that provides a lookup of programs to their taxonomy classifications (category and focus area).

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| program_id | TEXT | Program identifier |
| taxonomy_focus_area_id | TEXT | Focus area identifier |
| taxonomy_category_id | TEXT | Taxonomy category identifier |

**Definition**: Union of two queries:
1. Programs linked via GWO assignments: `program → program_to_gwo → gwo → taxonomy_focus_area → taxonomy_category`
2. Programs linked via other_program_spending: `other_program_spending → taxonomy_focus_area → taxonomy_category`

**Notes**:
- Provides unified view of program taxonomy regardless of classification method
- Used for generating taxonomy-based program listings

---

## Data Types Reference

### SQLite Data Types Used

- **INTEGER**: Whole numbers (used for IDs, fiscal years, boolean flags)
- **TEXT**: Character strings (used for names, descriptions, URLs, identifiers)
- **REAL**: Floating-point numbers (used for monetary amounts)
- **DECIMAL**: Numeric values with decimal precision (used for improper payment amounts)
- **BOOLEAN**: Stored as INTEGER (0 or 1) in SQLite

### Python Data Transformations

- **Boolean values**: Stored as INTEGER (0/1) in database, converted from Python booleans
- **URL generation**: Constructed from base URLs and identifiers/hashes
- **Text normalization**: 
  - Dashes replaced with en-dashes (U+2013) in taxonomy data
  - Whitespace stripped from CSV data
  - Agency names normalized using constants
- **Monetary values**: Cleaned by removing $ and commas, converted to float/real

---

## Foreign Key Relationships

```
agency
  ├── tier_1_agency_id → agency(id)
  └── tier_2_agency_id → agency(id)

category
  └── (type, parent_id) → category(id, type)

program
  └── agency_id → agency(id)

program_authorization
  └── program_id → program(id)

program_result
  └── program_id → program(id)

program_sam_spending
  ├── program_id → program(id)
  └── (assistance_type, category_type) → category(id, type)

program_to_category
  ├── program_id → program(id)
  └── (category_id, category_type) → category(id, type)

taxonomy_focus_area
  └── category_id → taxonomy_category(id)

gwo
  └── focus_area_id → taxonomy_focus_area(id)

pon
  └── focus_area_id → taxonomy_focus_area(id)

program_to_gwo
  ├── program_id → program(id)
  └── gwo_id → gwo(id)

program_to_pon
  ├── program_id → program(id)
  └── pon_id → pon(id)

usaspending_assistance_obligation_aggregation
  └── cfda_number → program(id)

usaspending_assistance_outlay_aggregation
  └── cfda_number → program(id)

other_program_spending
  ├── program_id → program(id)
  └── focus_area_id → taxonomy_focus_area(id)

improper_payment_mapping
  └── program_id → program(id)
```

---

## Data Sources

| Source | File(s) | Tables Populated |
|--------|---------|------------------|
| SAM.gov | `organizations.json` | `agency` |
| SAM.gov | `dictionary.json` | `category` |
| SAM.gov | `assistance-listings.json` | `program`, `program_authorization`, `program_result`, `program_sam_spending`, `program_to_category` |
| SAM.gov | `usaspending-program-search-hashes.json` | Used to construct `program.usaspending_awards_url` |
| USASpending.gov | CSV files in `ASSISTANCE_EXTRACTED_FILES_DIRECTORY` and `ASSISTANCE_DELTA_FILES_DIRECTORY` | `usaspending_assistance` (temporary) |
| USASpending.gov | CSV files in `CONTRACT_EXTRACTED_FILES_DIRECTORY` and `CONTRACT_DELTA_FILES_DIRECTORY` | `usaspending_contract` (temporary) |
| Taxonomy Data | `Taxonomy_GWO_crosswalk.csv` | `taxonomy_category`, `taxonomy_focus_area`, `gwo` |
| Taxonomy Data | `Taxonomy_PON_crosswalk.csv` | `taxonomy_category`, `taxonomy_focus_area`, `pon` |
| Program Assignments | `FPI_GWO_assignment.csv` | `program_to_gwo` |
| Program Assignments | `FPI_PON_assignment.csv` | `program_to_pon` |
| Additional Programs | `additional-programs.csv` | `program`, `other_program_spending`, `taxonomy_category`, `taxonomy_focus_area` |
| Improper Payments | `improper-payment-program-mapping.csv` | `improper_payment_mapping` |

---

## Notes on Data Processing

### Agency Hierarchy
- Agencies can have tier 1 and tier 2 parent agencies
- CFO Act agencies are identified at the top level (where `orgKey == l1OrgKey`)
- Agency names are normalized using display name mappings

### Category Types
- **assistance**: Types of financial assistance (grants, loans, etc.)
- **applicant**: Types of eligible applicants
- **beneficiary**: Types of program beneficiaries

### Program Types
- **assistance_listing**: Standard SAM.gov assistance listings
- **interest**: Interest on the public debt programs
- **tax_expenditure**: Tax expenditure programs
- **acquisition_contract**: Acquisition contracts programs (derived from contracts)
- **government_service**: Government service programs (derived from contracts)

### Spending Data Aggregation
- SAM.gov spending: Stored at transaction level with actual/estimate flags
- USASpending.gov obligations: Aggregated by program, fiscal year, assistance type, and congressional district
- USASpending.gov outlays: Aggregated by program, award key, and fiscal year

### Taxonomy Classification
- Programs can be classified via GWO assignments or via focus area in other_program_spending
- The `program_taxonomy_lookup` view unifies both classification methods

---

## Version Information

**Last Updated**: Generated from `transform.py` on 2025-11-17

**Primary Database File**: `transformed/transformed_data.db`

**Temporary Database File**: `transformed/temp_data.db` (deleted after processing)