# Use a base Python image
FROM python:3.14-slim
ARG http_proxy
ARG https_proxy
ARG no_proxy
ARG TEST_ENV=false

ENV http_proxy=$http_proxy \
    https_proxy=$https_proxy \
    no_proxy=$no_proxy \
    HTTP_PROXY=$http_proxy \
    HTTPS_PROXY=$https_proxy \
    NO_PROXY=$no_proxy

WORKDIR /app/indexer/
COPY ./requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make the test indexer file available
COPY ./prepare-test-files-indexer.sh /prepare-test-files-indexer.sh
COPY ./cypress /cypress
COPY ./ /app/indexer

RUN if [ "${TEST_ENV}" = "true" ]; then \
        echo "Test profile detected. Preparing test json file..."; \
        chmod +x /prepare-test-files-indexer.sh && \
        cd / && \
        TEST_ENV=true /prepare-test-files-indexer.sh || echo "Warning: prepare-test-files-indexer.sh failed"; \
    else \
        echo "Test profile not active. Skipping test file preparation."; \
    fi

USER 1000:1000

# Set the default command to run the Python script
CMD ["python", "index_programs.py"]