# Stage 1: Build the static HTML / CSS / JS bundle
#          This stage is responsible for using Jekyll to build the static
#          files that are ultimately served by nginx. This is not the final
#          image.
FROM ruby:3.2.2 AS build-image
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
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y curl git && \
    curl -k -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash && \
    . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION} && \
    . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION} && \
    npm install --legacy-peer-deps chart.js && \
    bundle install

COPY . /app
RUN bundle exec jekyll build && \
    npx gulp updateUswds


# Stage 2: Build the final nginx image
#          This stage is responsible for building the final nginx image that
#          contains the static files generated in Stage 1.
FROM nginxinc/nginx-unprivileged:alpine AS runtime-image
ARG http_proxy
ARG https_proxy
ARG no_proxy

ENV http_proxy=$http_proxy \
    https_proxy=$https_proxy \
    no_proxy=$no_proxy \
    HTTP_PROXY=$http_proxy \
    HTTPS_PROXY=$https_proxy \
    NO_PROXY=$no_proxy

COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=0 /app/_site /usr/share/nginx/html
EXPOSE 8080