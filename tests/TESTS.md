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
- [ ] Generate GWO markdown files
- [ ] Generate PON markdown files
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

- [ ] Invalid GWOs do not create a CSV or blocker when GWOs are valid
- [ ] Invalid GWOs create a CSV and blocker when GWOs are invalid
- [ ] Invalid PONs do not create a CSV or blocker when PONs are valid
- [ ] Invalid PONs create a CSV and blocker when PONs are invalid
- [ ] Excessive PON assignments do not create a CSV or blocker when every program has 3 or fewer
- [ ] Excessive PON assignments create a CSV and blocker when a program has more than 3
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
- [ ] Unmapped-program report lists programs missing a GWO or PON
- [ ] Unmapped-program report does not raise when it cannot be written

### Verify excessive PON assignments

`check_data_quality_before_transform.py` flags any program in `FPI_PON_assignment.csv` with more than 3 PON assignments. `transform.py` runs that check before it loads data. A finding writes `excessive_pon_assignments.csv` (`aln`, `pon`) and appends a `BLOCKED:` line to `blockers.txt`, which stops transform unless `--ignore-blockers` is set. A program with exactly 3 assignments passes. Blank PON cells do not count.

1. From the repository root, run:
   `python -m pytest tests/test_check_data_quality.py::TestExcessivePonAssignments -q`
2. Confirm both tests pass.
3. In `test_does_not_create_csv_or_blocker_when_assignments_are_within_limit`, `10.001` and `10.002` each have 3 PON assignments. `10.002` also has a blank PON cell. The test expects no `excessive_pon_assignments.csv` and no `blockers.txt`.
4. In `test_creates_csv_and_blocker_when_a_program_has_more_than_three`, `10.002` has exactly 3 assignments, `10.003` has 4, and `10.004` has 5. The test expects `excessive_pon_assignments.csv` to list only `10.003` and `10.004`, one row per assignment, with the header `aln,pon`. It also expects `blockers.txt` to contain `BLOCKED:  2 programs have more than 3 PON assignments`.
5. Run the check against the extracted files:
   `python data_processing/check_data_quality_before_transform.py /tmp/fpi-pon-qa`
6. `data_processing/extracted/FPI_PON_assignment.csv` has the header `al_#,PON ID` and no assignment rows. The check must not write `/tmp/fpi-pon-qa/excessive_pon_assignments.csv`, and `blockers.txt` must not contain a line about programs having more than 3 PON assignments. Other data-quality findings can still be written.

## `test_e2e.py`

- [ ] Extract, then transform, then load produce expected website and indexer outputs
