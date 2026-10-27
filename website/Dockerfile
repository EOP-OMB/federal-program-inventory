# Stage 1: Build the static HTML / CSS / JS bundle
#          This stage is responsible for using Jekyll to build the static
#          files that are ultimately served by nginx. This is not the final
#          image.
FROM ruby:3.2.2 AS build-image
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
ENV NODE_VERSION=18.17.1
ENV NVM_DIR=/root/.nvm
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
ARG http_proxy
ARG https_proxy
ARG no_proxy

ENV http_proxy=$http_proxy \
    https_proxy=$https_proxy \
    no_proxy=$no_proxy \
    HTTP_PROXY=$http_proxy \
    HTTPS_PROXY=$https_proxy \
    NO_PROXY=$no_proxy

WORKDIR /app
COPY ./Gemfile /app/Gemfile
COPY ./package.json /app/package.json
COPY ./requirements.txt /app/requirements.txt
COPY ./generate_csv.py /app/generate_csv.py
COPY ./transformed_data.db /app/transformed_data.db
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y curl git && \
    apt-get install -y curl git && \
    #command below is needed when ZScaler is active. Will remove before pushing code to main/release.
    git config --global http.sslVerify false && \
    curl -k -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash && \
    . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION} && \
    . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION} && \
    #command below is needed when ZScaler is active. Will remove before pushing code to main/release.
    npm config set strict-ssl false && \
    npm install --legacy-peer-deps chart.js

RUN apt-get install -y python3 python3-pip python3-venv && \
    python3 -m venv /app/.venv && \
    /app/.venv/bin/pip install --no-cache-dir -r /app/requirements.txt && \
    /app/.venv/bin/python /app/generate_csv.py

RUN bundle install

COPY ./prepare-test-files-website.sh /prepare-test-files-website.sh
COPY ./cypress /cypress
COPY ./ /app

# Use test data and md files in test environment
RUN if [ "${TEST_ENV}" = "true" ]; then \
        echo "Test profile detected. Preparing test markdown files..."; \
        chmod +x /prepare-test-files-website.sh && \
        cd / && \
        TEST_ENV=true /prepare-test-files-website.sh || echo "Warning: prepare-test-files-website.sh failed"; \
    else \
        echo "Test profile not active. Skipping test file preparation."; \
    fi

RUN bundle exec jekyll build && \
    npx gulp updateUswds

RUN BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") && \
    echo "<!-- Deployment Date: ${BUILD_DATE} -->" >> /app/_site/index.html

# The hardened nginx runtime has no shell, so choose the config here.
ARG USE_LOCAL_API=false
RUN if [ "${TEST_ENV}" = "true" ] || [ "${USE_LOCAL_API}" = "true" ]; then \
      cp /app/nginx.conf.local /app/nginx.runtime.conf; \
    else \
      cp /app/nginx.conf /app/nginx.runtime.conf; \
    fi

# Stage 2: Red Hat Hardened nginx. No shell or package manager.
#          Serves the static files generated in Stage 1.
FROM registry.access.redhat.com/hi/nginx:1.30 AS runtime-image
ARG http_proxy
ARG https_proxy
ARG no_proxy

ENV http_proxy=$http_proxy \
    https_proxy=$https_proxy \
    no_proxy=$no_proxy \
    HTTP_PROXY=$http_proxy \
    HTTPS_PROXY=$https_proxy \
    NO_PROXY=$no_proxy

COPY --from=build-image /app/nginx.runtime.conf /etc/nginx/nginx.conf
COPY --from=build-image /app/_site /usr/share/nginx/html
COPY --from=build-image /app/_dynamic /usr/share/nginx/html/assets/files
EXPOSE 8080