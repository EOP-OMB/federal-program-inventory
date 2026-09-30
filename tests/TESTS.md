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
- [ ] Transform data-quality checks pass on valid inputs
- [ ] Acquisitions and services fail for an invalid agency
- [ ] Additional programs fail when interest is missing
- [ ] GWO assignment fails for an invalid GWO
- [ ] PON assignment fails for an invalid PON
- [ ] Improper-payment mapping fails when a name is missing from the page
- [ ] Inflation and population growth fail when a year is missing
- [ ] Taxonomy GWO crosswalk fails when columns are missing
- [ ] Taxonomy PON crosswalk fails when columns are missing
- [ ] Dictionary load fails for invalid JSON
- [ ] USAspending program search hashes fail for invalid JSON

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
- [ ] Generate GWO markdown files
- [ ] Generate PON markdown files
- [ ] Generate program markdown files
- [ ] Generate the program CSV
- [ ] Generate programs table JSON
- [ ] Export inflation and population from CSV
- [ ] Export global dates to YAML
- [ ] Export data sources config

## `test_e2e.py`

- [ ] Extract, then transform, then load produce expected website and indexer outputs
