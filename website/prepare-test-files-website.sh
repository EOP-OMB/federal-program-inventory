#!/bin/bash

set -e

CYPRESS_MD_DIR="cypress/md"
CYPRESS_DATA_DIR="cypress/data"
WEBSITE_PAGES_DIR="app/pages"
WEBSITE_DATA_DIR="app/_data"
TEST_PAGES_DIR="${WEBSITE_PAGES_DIR}/tests"

if [ "${TEST_ENV}" != "true" ]; then
    echo "TEST_ENV is not set to 'true'. Skipping test file preparation."
    exit 0
fi

echo "Preparing test markdown files..."

mkdir -p "${TEST_PAGES_DIR}"

if [ ! -d "${CYPRESS_MD_DIR}" ] || [ -z "$(ls -A ${CYPRESS_MD_DIR}/*.md 2>/dev/null)" ]; then
    echo "No markdown files found in ${CYPRESS_MD_DIR}"
    exit 0
fi

# Copy and modify each markdown file
for md_file in "${CYPRESS_MD_DIR}"/*.md; do
    if [ -f "${md_file}" ]; then
        filename=$(basename "${md_file}")
        echo "Processing ${filename}..."

        cp "${md_file}" "${TEST_PAGES_DIR}/${filename}"

        # Extract filename without extension for permalink
        markdown_filename="${filename%.md}"

        # Add the permalink if it does not exist (recommended)
        if ! grep -q "^permalink:" "${TEST_PAGES_DIR}/${filename}"; then
            # Add permalink after the first --- (end of frontmatter)
            # Find the line number of the second ---
            second_dash_line=$(grep -n "^---$" "${TEST_PAGES_DIR}/${filename}" | sed -n '2p' | cut -d: -f1)
            if [ -n "${second_dash_line}" ]; then
                # Insert permalink before the closing ---
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    # macOS uses BSD sed
                    sed -i '' "${second_dash_line}i\\
permalink: test/${markdown_filename}.html
" "${TEST_PAGES_DIR}/${filename}"
                else
                    # Linux uses GNU sed
                    sed -i "${second_dash_line}i permalink: test/${markdown_filename}.html" "${TEST_PAGES_DIR}/${filename}"
                fi
            else
                # If no frontmatter structure, add it
                echo "permalink: test/${markdown_filename}.html" >> "${TEST_PAGES_DIR}/${filename}"
            fi
        fi

        echo "  → Copied to ${TEST_PAGES_DIR}/${filename} with permalink: test/${markdown_filename}.html"
    fi
done

# Copy data files
if [ -d "${CYPRESS_DATA_DIR}" ]; then
    echo "Copying test environment data files..."
    for data_file in "${CYPRESS_DATA_DIR}"/*.yml; do
        if [ -f "${data_file}" ]; then
            filename=$(basename "${data_file}")
            echo "  → Copying ${filename} to ${WEBSITE_DATA_DIR}/"
            cp -f "${data_file}" "${WEBSITE_DATA_DIR}/${filename}"
        fi
    done
fi

echo "Test markdown files prepared in ${TEST_PAGES_DIR}"


