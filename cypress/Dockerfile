# cypress/Dockerfile
FROM cypress/factory:8.1.1

WORKDIR /app

# Install browser
# to get candidate versions:
#   docker run --rm cypress/factory:<image version from above> bash -lc "apt-get update >/dev/null && apt-cache policy chromium"
RUN apt update && apt install -y chromium=147.0.7727.137-1~deb13u1 chromium-common=147.0.7727.137-1~deb13u1

# Install Node.js dependencies
COPY package.json package-lock.json* ./
#command below is needed when ZScaler is active. Will remove before pushing code to main/release.
RUN npm config set strict-ssl false
RUN npm ci

# Copy Cypress configuration and tests
COPY cypress.config.js ./
COPY e2e/ ./cypress/e2e/
COPY support/ ./cypress/support/
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh
