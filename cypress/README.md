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