# Federal Program Inventory - E2E Suite

This directory contains e2e tests for the Federal Program Inventory data processing pipeline.  Run the tests by doing the following:
* Set `TEST_ENV` environment variable to `true` (can also be stored in a local .env file)
* Run `docker compose --profile test up --build`

If baseline screenshots need to be updated:
* Delete screenshots that need updating from the `cypress/cypress-image-diff-screenshots/baseline`
  * Screenshots will generally have the name `<test filename without .js extension>-<first parameter in compareSnapshot call>.png`
* Run `docker compose --profile test up --build`
* Review the screenshots in `cypress/cypress-image-diff-screenshots/baseline`
* Stage the changes to `cypress/cypress-image-diff-screenshots/baseline` with other changes

Data updates typically should not impact tests.  However, when / if they do, consider updating `website/prepare-test-files-website.sh` or `website/cypress` to ensure that a stable dataset is used for each batch of tests.  The `website/cypress/data` directory is used to override global variables, and `website/cypress/pages` is used to overwrite data for specific pages.