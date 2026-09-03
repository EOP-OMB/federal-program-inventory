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

### Updating baselines from the GitHub runner (recommended)

PR CI uses the same Linux runner that compares screenshots. To regenerate baselines there:

1. Open (or update) your pull request.
2. Add the `update-screenshots` label.
3. Wait for **PR Build Test** to finish (adding the label triggers a run; you can also re-run the workflow).
4. CI clears existing baselines, recreates them, commits them to your PR branch, and removes the label.
5. Review the PNG changes in the PR diff and merge when ready.

Without that label, CI only compares against committed baselines.

To skip visual comparisons entirely in a local/CI Cypress run, set `SKIP_SCREENSHOT_COMPARISON=true` (passed through as `CYPRESS_SKIP_SCREENSHOT_COMPARISON`).

Data updates typically should not impact tests.  However, when / if they do, consider updating `website/prepare-test-files-website.sh` or `website/cypress` to ensure that a stable dataset is used for each batch of tests.  The `website/cypress/data` directory is used to override global variables, and `website/cypress/pages` is used to overwrite data for specific pages.
