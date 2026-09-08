#!/bin/bash

set -e

echo "Cypress container starting..."

# Check if TEST_ENV is true
if [ "${TEST_ENV}" != "true" ]; then
    echo "TEST_ENV is not set to 'true'. Skipping Cypress tests."
    exit 0
fi

echo "TEST_ENV is true. Preparing test markdown files..."

echo "Starting Cypress tests..."

# Run Cypress tests and capture exit code
EXIT_CODE=0
npm run cypress:run || EXIT_CODE=$?

# Cleanup test markdown files
echo "Cleaning up test markdown files..."

# Exit with appropriate code
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ CYPRESS TESTS FAILED"
    echo "One or more Cypress tests failed. Check the test output above for details."
    echo "Screenshots and videos (if enabled) are available in cypress/reports/"
    exit $EXIT_CODE
else
    echo ""
    echo "✅ All Cypress tests passed!"
    exit 0
fi


