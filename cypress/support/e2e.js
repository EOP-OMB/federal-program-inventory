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
  (originalFn, subject, options) => {
    const skipComparison =
      Cypress.env('SKIP_SCREENSHOT_COMPARISON') === true ||
      Cypress.env('SKIP_SCREENSHOT_COMPARISON') === 'true'

    if (skipComparison) {
      cy.log('SKIP_SCREENSHOT_COMPARISON is set; skipping screenshot comparison')
      return cy.wrap(null, { log: false })
    }

    let cacheBust = true
    let snapshotOptions = options

    if (typeof options === 'object' && options !== null) {
      ;({ cacheBust = true, ...snapshotOptions } = options)
    }

    // cache busting is used to remove :visited formatting from links
    // (other methods are inconsistent)
    const applyCacheBust = () => {
      if (!cacheBust) {
        return
      }
      const bust = Date.now()
      cy.get('body').then(($body) => {
        $body.find('a[href]').each((_, el) => {
          const href = el.getAttribute('href')
          if (
            !href ||
            href.startsWith('javascript:') ||
            href.startsWith('mailto:') ||
            href.startsWith('tel:')
          ) {
            return
          }

          el.setAttribute('data-cb-original-href', href)

          // Intrapage anchors: keep the fragment and bust via a query param
          // so :visited history does not match (e.g. "#foo" -> "?_cb=…#foo").
          if (href.startsWith('#')) {
            el.setAttribute('href', `?_cb=${bust}${href}`)
            return
          }

          const hashIndex = href.indexOf('#')
          const hash = hashIndex >= 0 ? href.slice(hashIndex) : ''
          const withoutHash = hashIndex >= 0 ? href.slice(0, hashIndex) : href
          const sep = withoutHash.includes('?') ? '&' : '?'
          el.setAttribute('href', `${withoutHash}${sep}_cb=${bust}${hash}`)
        })
      })
    }

    const restoreCacheBust = () => {
      if (!cacheBust) {
        return
      }
      cy.get('body').then(($body) => {
        $body.find('a[data-cb-original-href]').each((_, el) => {
          el.setAttribute('href', el.getAttribute('data-cb-original-href'))
          el.removeAttribute('data-cb-original-href')
        })
      })
    }

    const applyFontSmoothing = () => {
      cy.document().then((doc) => {
        if (doc.getElementById('cy-font-smoothing')) {
          return
        }
        const style = doc.createElement('style')
        style.id = 'cy-font-smoothing'
        style.textContent = `
          * {
            -webkit-font-smoothing: antialiased !important;
            -moz-osx-font-smoothing: grayscale !important;
            text-rendering: geometricPrecision !important;
          }
        `
        doc.head.appendChild(style)
      })
    }

    return cy
      .document()
      .then((doc) => doc.fonts.ready)
      .then(() => applyFontSmoothing())
      .then(() => applyCacheBust())
      .then(() =>
        cy.waitForStableLayout('body', { stableMs: 1000, timeout: 5000 })
      )
      .then(() => originalFn(subject, snapshotOptions))
      .then(() => restoreCacheBust())
  }
)

beforeEach(() => {
  // clear visited links and other state before each spec file
  cy.clearCookies()
  cy.clearLocalStorage()
})