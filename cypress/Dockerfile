# cypress/Dockerfile
FROM cypress/factory

WORKDIR /app

# Install browser
RUN apt update && apt install -y chromium

# Install Node.js dependencies
COPY package.json package-lock.json* ./
#command below is needed when ZScaler is active. Will remove before pushing code to main/release.
RUN npm config set strict-ssl false
RUN npm install

# Copy Cypress configuration and tests
COPY cypress.config.js ./
COPY e2e/ ./cypress/e2e/
COPY support/ ./cypress/support/
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh
