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

// Wait for D3/SVG charts to finish drawing (or show explicit no-data) before axe runs.
Cypress.Commands.add('waitForChartsReady', () => {
  const chartHosts = [
    '#chart',
    '#spending-chart',
    '#objectiveChart',
    '#outcomeChart',
    '#myChart',
  ]

  cy.get('body').then(($body) => {
    const presentHosts = chartHosts.filter((selector) => $body.find(selector).length > 0)

    presentHosts.forEach((selector) => {
      cy.get(selector, { timeout: 10000 }).should(($el) => {
        const el = $el[0]
        const doc = el.ownerDocument
        const noChart =
          doc.querySelector('#no-chart:not(.hide)') ||
          doc.querySelector('#no-spending-chart:not(.hide)')
        const hasDrawnContent = Boolean(
          el.querySelector('svg, g, rect, path, text') ||
            (el.tagName.toLowerCase() === 'svg' && el.childElementCount > 0)
        )

        expect(
          hasDrawnContent || Boolean(noChart),
          `${selector} should render chart content or show the no-data state`
        ).to.eq(true)
      })

      cy.waitForStableLayout(selector, { stableMs: 400, timeout: 5000 })
    })
  })
})

// ANDI parity: focusables must not sit under aria-hidden=true outside the open mobile nav.
Cypress.Commands.add('assertNoFocusableUnderAriaHidden', () => {
  cy.document().then((doc) => {
    const nav = doc.querySelector('.usa-nav')
    const focusableSel =
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    const offenders = [...doc.querySelectorAll(focusableSel)].filter((el) => {
      if (nav && (nav === el || nav.contains(el))) {
        return false
      }
      let node = el
      while (node) {
        if (node.getAttribute && node.getAttribute('aria-hidden') === 'true') {
          return true
        }
        node = node.parentElement
      }
      return false
    })
    expect(
      offenders,
      offenders
        .slice(0, 5)
        .map(
          (el) =>
            el.tagName + (el.className ? '.' + String(el.className).split(' ')[0] : '')
        )
        .join(', ')
    ).to.have.length(0)
  })
})

Cypress.Commands.add('checkA11yPage', (context = undefined, options = undefined) => {
  cy.waitForChartsReady()
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
