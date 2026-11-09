# Data pipeline tests

Automated tests run in the `data-pipeline-tests` container (`pytest` via `tests/entrypoint.sh`).

## `test_constants.py`

- [ ] Fiscal year and date constants are defined and valid
- [ ] Agency display names mapping is populated
- [ ] Assistance type display names mapping is populated
- [ ] CFO Act agency names list is populated
- [ ] Program type mapping is populated

## `test_extract.py`

- [ ] Extract assistance listings succeeds
- [ ] Extract assistance listings handles a network error
- [ ] Extract improper-payment data succeeds
- [ ] Extract improper-payment data handles an error
- [ ] Extract SAM.gov dictionary succeeds
- [ ] Extract SAM.gov dictionary handles an error
- [ ] Extract organizations succeeds
- [ ] Extract organizations handles an error
- [ ] Extract USAspending award hashes succeeds
- [ ] Extract USAspending award hashes handles a connection error
- [ ] Clean a JSON extract succeeds
- [ ] Clean a JSON extract handles a missing file
- [ ] Clean all extracted data succeeds

## `test_transform.py`

- [ ] Convert a normal string to a URL slug
- [ ] Convert a string with special characters to a URL slug
- [ ] Convert an empty string to a URL slug
- [ ] Load USAspending initial files
- [ ] Transform and insert USAspending aggregation data
- [ ] Load agency data
- [ ] Load SAM category data
- [ ] Load SAM programs
- [ ] Load acquisitions and services
- [ ] Load category and subcategory data
- [ ] Load additional programs
- [ ] Load improper-payment mapping
- [ ] Stop transform when data quality blockers exist
- [ ] Continue transform when data quality checks pass
- [ ] `--ignore-blockers` defaults off
- [ ] `--ignore-blockers` is accepted
- [ ] Continue transform when `--ignore-blockers` is specified
- [ ] Stop transform when blockers are found after transform
- [ ] Continue transform when blockers are found after transform and `--ignore-blockers` is specified
- [ ] Duplicate assignment is not stored
- [ ] Assignment with a missing parent is rejected

## `test_load.py`

- [ ] Recreate a directory that does not yet exist
- [ ] Recreate a directory that already exists
- [ ] Get assistance program obligations
- [ ] Get other program amounts for tax expenditures
- [ ] Get other program amounts for interest
- [ ] Get combined program amounts
- [ ] Get assistance listing expenditures when data is present
- [ ] Get assistance listing expenditures when data is empty
- [ ] Generate the agency list
- [ ] Generate the applicant type list
- [ ] Convert a string to a URL slug
- [ ] Get the categories hierarchy
- [ ] Get improper-payment info
- [ ] Calculate improper-payment metrics
- [ ] Get related programs
- [ ] Generate program data
- [ ] Generate shared data
- [ ] Generate the search page
- [ ] Generate the taxonomy page
- [ ] Generate about markdown files
- [ ] Generate the home page
- [ ] Generate the category page
- [ ] Generate category markdown files
- [ ] Generate subcategory markdown files
- [ ] Summarize related programs when empty
- [ ] Summarize related programs totals, largest, and smallest
- [ ] Summarize related programs ties by name then list order
- [ ] Summarize related programs missing expenditure as zero
- [ ] Generate PFA markdown files
- [ ] Generate program markdown files
- [ ] Generate the program CSV
- [ ] Generate programs table JSON
- [ ] Export inflation and population from CSV
- [ ] Export global dates to YAML
- [ ] Export data sources config
- [ ] `--ignore-blockers` defaults off
- [ ] `--ignore-blockers` is accepted
- [ ] Stop load when data quality blockers exist
- [ ] Continue load when `--ignore-blockers` is specified
- [ ] Continue load when data quality blockers are absent

## `test_check_data_quality.py`

- [ ] Invalid PFAs do not create a CSV or blocker when PFAs are valid
- [ ] Invalid PFAs create a CSV and blocker when PFAs are invalid
- [ ] Invalid ALNs do not create a CSV or blocker when ALNs are valid
- [ ] Invalid ALNs create a CSV and do not write a blocker when ALNs are invalid
- [ ] Invalid agencies do not create a CSV or blocker when agencies are valid
- [ ] Invalid agencies create a CSV and blocker when an agency is invalid
- [ ] Invalid program types do not create a CSV or blocker when program types are valid
- [ ] Invalid program types create a CSV and blocker when a program type is invalid
- [ ] Duplicate IDs do not create a CSV or blocker when IDs are unique
- [ ] Duplicate IDs create a CSV and blocker when an ID is duplicated
- [ ] Hyphenated duplicate-id fields do not collide
- [ ] Missing inflation year does not create a CSV or blocker when the year is present
- [ ] Missing inflation year creates a CSV and blocker when the year is missing
- [ ] Additional programs do not create a CSV or blocker when IN. and TC. programs exist
- [ ] Additional programs create a CSV and blocker when the IN. program is missing
- [ ] Additional programs create a CSV and blocker when the TC. program is missing
- [ ] Possibly truncated ALNs do not create a CSV when the check passes
- [ ] Possibly truncated ALNs create a CSV when records fail
- [ ] Possibly truncated ALNs write blockers when records fail
- [ ] Amounts with scientific notation do not create a CSV when the check passes
- [ ] Amounts with scientific notation create a CSV when records fail
- [ ] Amounts with scientific notation write blockers when records fail
- [ ] CSV headers are correct across all files
- [ ] CSV headers are incorrect in a file
- [ ] CSV column counts are correct across all files
- [ ] CSV column count is incorrect in one file
- [ ] An unexpected error records a blocker and returns
- [ ] Unmapped-program report lists programs missing a PFA
- [ ] Unmapped-program report does not raise when it cannot be written

## `test_e2e.py`

- [ ] Extract, then transform, then load produce expected website and indexer outputs
