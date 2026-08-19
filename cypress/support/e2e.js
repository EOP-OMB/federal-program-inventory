// ***********************************************************
// This example support/e2e.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands'
import 'cypress-axe'

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Register cypress-image-diff-js command for visual regression testing
import compareSnapshotCommand from 'cypress-image-diff-js/command'
compareSnapshotCommand()

Cypress.Commands.overwrite(
  'compareSnapshot',
  (originalFn, subject, ...args) => {
    return cy
      .waitForStableLayout('body', { stableMs: 1000, timeout: 5000 })
      .then(() => originalFn(subject, ...args))
  }
)

beforeEach(() => {
  // clear visited links and other state before each spec file
  cy.clearCookies()
  cy.clearLocalStorage()
})