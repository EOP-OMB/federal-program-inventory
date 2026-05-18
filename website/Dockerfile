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

WORKDIR /app
COPY ./Gemfile /app/Gemfile
COPY ./package.json /app/package.json
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y curl git && \
    curl -k -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash && \
    . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION} && \
    . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION} && \
    npm install --legacy-peer-deps chart.js && \
    bundle install

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

# Stage 2: Build the final nginx image
#          This stage is responsible for building the final nginx image that
#          contains the static files generated in Stage 1.
FROM nginxinc/nginx-unprivileged:alpine AS runtime-image
ARG http_proxy
ARG https_proxy
ARG no_proxy
ARG TEST_ENV=false
ARG USE_LOCAL_API=false

ENV http_proxy=$http_proxy \
    https_proxy=$https_proxy \
    no_proxy=$no_proxy \
    HTTP_PROXY=$http_proxy \
    HTTPS_PROXY=$https_proxy \
    NO_PROXY=$no_proxy

# Use local api in test environment
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./nginx.conf.local /etc/nginx/nginx.conf.local
RUN if [ "${TEST_ENV}" = "true" ] || [ "$USE_LOCAL_API" = "true" ]; then \
    cp -rf /etc/nginx/nginx.conf.local /etc/nginx/nginx.conf; \
    fi

COPY --from=0 /app/_site /usr/share/nginx/html
EXPOSE 8080