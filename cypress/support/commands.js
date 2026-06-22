// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

Cypress.Commands.add('waitForPageLoad', () => {
  cy.get('body').should('be.visible')
  cy.get('body').should('not.have.class', 'loading')
})

Cypress.Commands.add('checkA11yPage', (context = undefined, options = undefined) => {
  cy.injectAxe()

  const logViolations = (violations) => {
    if (!violations.length) {
      return
    }

    cy.task('log', `A11y violations found: ${violations.length}`)

    violations.forEach((violation) => {
      cy.task(
        'log',
        `Rule: ${violation.id} | Impact: ${violation.impact || 'unknown'} | Tags: ${violation.tags.join(', ')}`
      )
      cy.task('log', `Help: ${violation.help}`)
      cy.task('log', `More info: ${violation.helpUrl}`)
      cy.task('log', `Affected elements: ${violation.nodes.length}`)

      const nodeDetails = violation.nodes.map((node, index) => ({
        index: index + 1,
        target: node.target.join(' | '),
        failureSummary: (node.failureSummary || '').replace(/\s+/g, ' ').trim(),
      }))

      nodeDetails.forEach((node) => {
        cy.task('log', `Element ${node.index}: ${node.target || '[no selector provided]'}`)
        cy.task('log', `Issue: ${node.failureSummary || '[no failure summary provided]'}`)
      })

      cy.task('table', nodeDetails)
    })
  }

  cy.checkA11y(context, options, logViolations)
})


