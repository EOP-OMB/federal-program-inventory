#!/bin/bash

set -e

CYPRESS_INDEXER_DATA="/cypress/programs-table.json"
INDEXER_DATA_DIR="/app/indexer"

if [ "${TEST_ENV}" != "true" ]; then
    echo "TEST_ENV is not set to 'true'. Skipping test file preparation."
    exit 0
fi

echo "Preparing json file..."

filename=$(basename "${CYPRESS_INDEXER_DATA}")
cp -f "${CYPRESS_INDEXER_DATA}" "${INDEXER_DATA_DIR}/${filename}"

echo "Test data loaded into indexer json file."


