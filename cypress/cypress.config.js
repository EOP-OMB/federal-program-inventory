const { defineConfig } = require('cypress')
const getCompareSnapshotsPlugin = require('cypress-image-diff-js/plugin')

module.exports = defineConfig({
  retries: 2,
  e2e: {
    baseUrl: process.env.CYPRESS_baseUrl || 'http://website:8080',
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.js',
    video: false,
    screenshotOnRunFailure: true,
    screenshotsFolder: 'cypress/reports/screenshots',
    videosFolder: 'cypress/reports/videos',
    testIsolation: true,
    chromeWebSecurity: false,
    setupNodeEvents(on, config) {
      // Register the cypress-image-diff-js plugin
      getCompareSnapshotsPlugin(on, config)

      on('before:browser:launch', (browser, launchOptions) => {
        // Ensure screenshots capture everything on "macbook-16" viewport
        launchOptions.args.push('--window-size=1536,960')

        return launchOptions
      });

      // implement node event listeners here
      on('task', {
        log(message) {
          console.log(message)
          return null
        },
        table(message) {
          console.table(message)
          return null
        }
      });

      on('before:run', (details) => {
        console.log(
          `Version Information:  Cypress ${details.cypressVersion} | ` +
          `${details.browser.displayName} ${details.browser.version}`
        )
      })

      return config;
    },
  },
})

