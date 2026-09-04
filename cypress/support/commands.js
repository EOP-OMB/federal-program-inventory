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

// rect + scroll is usually enough
Cypress.Commands.add(
  'waitForStableLayout',
  (selector = 'body', { stableMs = 1000, timeout = 5000 } = {}) => {
    cy.get(selector, { timeout }).then(($el) => {
      const start = Date.now()
      let last = null
      let stableSince = null
      const snapshot = () => {
        const r = $el[0].getBoundingClientRect()
        return {
          x: Math.round(r.x),
          y: Math.round(r.y),
          w: Math.round(r.width),
          h: Math.round(r.height),
          scrollX: window.scrollX,
          scrollY: window.scrollY,
        }
      }
      const equal = (a, b) =>
        a &&
        b &&
        a.x === b.x &&
        a.y === b.y &&
        a.w === b.w &&
        a.h === b.h &&
        a.scrollX === b.scrollX &&
        a.scrollY === b.scrollY
      return new Cypress.Promise((resolve, reject) => {
        const tick = () => {
          const now = Date.now()
          if (now - start > timeout) {
            reject(new Error(`Layout did not stabilize within ${timeout}ms`))
            return
          }
          const curr = snapshot()
          if (equal(last, curr)) {
            if (stableSince == null) stableSince = now
            if (now - stableSince >= stableMs) {
              resolve()
              return
            }
          } else {
            last = curr
            stableSince = null
          }
          setTimeout(tick, 50) // poll ~every 50ms
        }
        last = snapshot()
        setTimeout(tick, 50)
      })
    })
  }
)