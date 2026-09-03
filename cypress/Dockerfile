# cypress/Dockerfile
FROM cypress/factory:8.1.1

WORKDIR /app

# Install browser and OS fonts matching website/sass font stacks:
# - Public Sans: vendored from USWDS (see fonts/public-sans) — $theme-font-type-sans / $site-default-font
# - Inter: fonts-inter — styles.scss
# - Century Schoolbook L: fonts-urw-base35 — $site-header-font-family / $site-subheader-font-family
# - Liberation: Arial / Helvetica-compatible fallbacks in $site-default-font
# - DejaVu: generic sans/serif fallbacks
# to get candidate chromium versions:
#   docker run --rm cypress/factory:<image version from above> bash -lc "apt-get update >/dev/null && apt-cache policy chromium"
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-common \
    fontconfig \
    fonts-inter \
    fonts-urw-base35 \
    fonts-liberation \
    fonts-dejavu-core \
  && rm -rf /var/lib/apt/lists/*

# Install Public Sans (exact USWDS files used by the website)
COPY fonts/public-sans/ /usr/local/share/fonts/public-sans/
RUN fc-cache -f

# Install Node.js dependencies
COPY package.json package-lock.json* ./
#command below is needed when ZScaler is active. Will remove before pushing code to main/release.
RUN npm config set strict-ssl false
RUN npm ci

# Copy Cypress configuration and tests
COPY cypress.config.js ./
COPY cypress-image-diff.config.js ./
COPY e2e/ ./cypress/e2e/
COPY support/ ./cypress/support/
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh
