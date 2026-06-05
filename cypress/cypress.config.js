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

      // implement node event listeners here
      on('task', {
        log(message) {
          console.log(message)
          return null
        }
      });

      return config;
    },
  },
})

