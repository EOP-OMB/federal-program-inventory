#!/bin/bash
# tests/entrypoint.sh

set -e

echo "Data pipeline tests container starting..."

# Check if TEST_ENV is true
if [ "${TEST_ENV}" != "true" ]; then
    echo "TEST_ENV is not set to 'true'. Skipping data pipeline tests."
    exit 0
fi

echo "TEST_ENV is true. Running data pipeline tests..."

# Run pytest and capture exit code
EXIT_CODE=0

python -m pytest test_constants.py

# Exit with appropriate code
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ DATA PIPELINE TESTS FAILED"
    echo "One or more pytest tests failed. Check the test output above for details."
    exit $EXIT_CODE
else
    echo ""
    echo "✅ All data pipeline tests passed!"
    exit 0
fi

