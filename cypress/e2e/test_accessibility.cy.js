describe('Accessibility checks', () => {
  const a11yOptions = {
    runOnly: {
      type: 'tag',
      values: ['wcag2a', 'wcag2aa', 'section508'],
    },
  }

  const includeFixturePages = Cypress.env('INCLUDE_FIXTURE_A11Y') !== false

  // Define the core pages to scan for accessibility issues. Add new pages here as needed for real site route auditing for 508 compliance.
  const corePagesToScan = [
    '/',
    '/search',
    '/about/fpi',
    '/about/terms',
    '/about/taxonomy',
    '/category',
  ]

  // Define additional test pages (fixture pages) to scan for accessibility issues. Add test pages here as needed for comprehensive component-level accessibility testing.
  const testPagesToScan = [
    '/test/index.html',
    '/test-footer-scroll.html',
    '/test-gwo-pon-count.html',
    '/test-improper-payment-card-NA.html',
    '/test-improper-payment-multiple-rate.html',
    '/test-improper-payment-no-data.html',
    '/test-improper-payment-positive-rate.html',
    '/test-improper-payment-zero-rate.html',
    '/test/improper_payments_section_1a.html',
    '/test-visited-links.html',
    '/test/authorization_tab_both.html',
    '/test/authorization_tab_neither.html',
    '/test/authorization_tab_no_auth.html',
    '/test/authorization_tab_no_rule.html',
    '/test/breadcrumbs_w_subagency.html',
    '/test/breadcrumbs_wo_subagency.html',
    '/test/category.html',
    '/test/subcategory.html',
    '/test/gwo_blank_description.html',
    '/test/gwo_missing_description.html',
    '/test/gwo_tags.html',
    '/test/gwo_treemap.html',
    '/test/insight_many_zero.html',
    '/test/insight_many.html',
    '/test/insight_one.html',
    '/test/insight_zero.html',
    '/test/list_beneficiaries.html',
    '/test/list_multiple_items.html',
    '/test/list_no_items.html',
    '/test/list_one_item.html',
    '/test/list_program_type.html',
    '/test/pon_tags.html',
    '/test/pon_treemap.html',
    '/test/program_overview_chart_base.html',
    '/test/program_overview_chart_coincide.html',
    '/test/program_overview_chart_no_data.html',
    '/test/program_overview_chart_no_obligations.html',
    '/test/program_overview_chart_no_outlays.html',
    '/test/program_overview_chart_one_year_stacked.html',
    '/test/program_overview_chart_one_year.html',
    '/test/program_overview_chart_other_program_spending.html',
    '/test/program_spending_chart_amount_formatting.html',
    '/test/program_spending_chart_base.html',
    '/test/program_spending_chart_data_gaps.html',
    '/test/program_spending_chart_neg_obligation.html',
    '/test/program_spending_chart_neg_outlay.html',
    '/test/program_spending_chart_negative_padding.html',
    '/test/program_spending_chart_no_baseline.html',
    '/test/program_spending_chart_no_data.html',
    '/test/program_spending_chart_other_program_spending.html',
    '/test/program_spending_chart_outlay_label_covered.html',
    '/test/program_spending_chart_unreported_years.html',
    '/test/program_test_4_tags.html',
    '/test/test-gwo-info-card.html',
    '/test/test-pon-info-card.html',
    '/test/taxonomy_filter_scenarios.html',
    '/test/program_page_populated.html',
    '/test/program_page_empty.html',
    '/test/program_page_objectives_only.html',
    '/test/subcategory_pagination.html',
    '/test/shared_ui_scenarios.html',
  ]

  const expandSearchFilter = (sectionId) => {
    cy.get(`button[data-content-id="${sectionId}"]`).click()
    cy.get(`#${sectionId}`).should('be.visible')
  }

  const scanPath = (path) => {
    it(`checks ${path} for 508 issues`, () => {
      cy.visit(path)
      cy.waitForPageLoad()
      cy.checkA11yPage(null, a11yOptions)
    })
  }

  corePagesToScan.forEach(scanPath)

  if (includeFixturePages) {
    testPagesToScan.forEach(scanPath)

    //checking all program tabs for 508 issues when running program_test_4_tags.html
    it('checks /test/program_test_4_tags.html program tabs for 508 issues', () => {
      const tabs = [
        { tab: '#overview-tab', panel: '#overview-panel' },
        { tab: '#spending-tab', panel: '#spending-panel' },
        { tab: '#results-tab', panel: '#results-panel' },
        { tab: '#authorization-tab', panel: '#authorization-panel' },
        { tab: '#oversight-tab', panel: '#oversight-panel' },
      ]

      cy.visit('/test/program_test_4_tags.html')
      cy.waitForPageLoad()

      cy.wrap(tabs).each(({ tab, panel }) => {
        cy.get(tab).should('be.visible').click({ force: true })
        cy.get(panel).should('be.visible')
        // Scan full page so tablist selected/ARIA state is included with the panel.
        cy.checkA11yPage(null, a11yOptions)
      })
    })
  }

  it('checks /search with expanded filter state for 508 issues', () => {
    cy.visit('/search')
    cy.waitForPageLoad()

    expandSearchFilter('agency-section')
    expandSearchFilter('categories-section')
    expandSearchFilter('program-type-section')
    expandSearchFilter('eligible-applicants-section')
    expandSearchFilter('gwo-section')

    cy.checkA11yPage(null, a11yOptions)
  })

  it('checks mobile nav with About submenu expanded for 508 issues', () => {
    cy.viewport('iphone-8')
    cy.visit('/')
    cy.waitForPageLoad()

    cy.get('.usa-menu-btn').should('be.visible').click()
    cy.get('nav.usa-nav').should('be.visible')
    cy.get('body').should('have.class', 'usa-js-mobile-nav--active')
    cy.get('body').should('have.attr', 'data-mobile-nav-a11y', 'fixed')
    cy.get('[data-nav-inert]').should('exist')
    cy.assertNoFocusableUnderAriaHidden()

    // Do not leave bare <a> tags (no href) — ANDI flags those as mouse-only links.
    cy.get('a:not([href])').should('not.exist')

    cy.get('.custom-accordion-button').should('be.visible').click()
    cy.get('.usa-nav__submenu').should('be.visible').and('not.have.attr', 'hidden')
    cy.assertNoFocusableUnderAriaHidden()

    cy.checkA11yPage(null, a11yOptions)
  })

  it('checks /about/taxonomy filters, sort, and pagination for 508 issues', () => {
    cy.visit('/about/taxonomy')
    cy.waitForPageLoad()

    cy.get('#taxonomy-filter-panels', { timeout: 10000 }).should('be.visible')
    cy.get('#taxonomy-gwo-table-body tr', { timeout: 10000 }).should(
      'have.length.greaterThan',
      0
    )

    cy.get('button[data-content-id="taxonomy-categories-section"]').click()
    cy.get('#taxonomy-categories-section').should('be.visible')

    cy.get('button.taxonomy-children-toggle').first().should('be.visible').click()
    cy.get('.taxonomy-filter-children:not([hidden])').should('be.visible')

    cy.get('#taxonomy-gwo-table th[data-column="title"]').click()
    cy.get('#taxonomy-pagination .usa-pagination__next-page').click()
    cy.get('#taxonomy-results-start').should('not.have.text', '1')

    cy.checkA11yPage(null, a11yOptions)
  })

  it('checks subcategory table mode radios for 508 issues', () => {
    const subcategoryPath = includeFixturePages
      ? '/test/subcategory.html'
      : '/category/education/k-12-education'

    cy.visit(subcategoryPath)
    cy.waitForPageLoad()

    cy.get('#view-by-selector').should('be.visible')

    cy.get('label[for="agency"]').click()
    cy.get('#agency').should('be.checked')
    cy.get('#agencies-table').should('be.visible')
    cy.checkA11yPage(null, a11yOptions)

    cy.get('label[for="eligible-applicant"]').click()
    cy.get('#eligible-applicant').should('be.checked')
    cy.get('#applicant-types-table').should('be.visible')
    cy.checkA11yPage(null, a11yOptions)
  })

  it('checks homepage spending tooltip open state for 508 issues', () => {
    const tooltipBody = '#homepage-spending-tip'
    const tooltipTrigger =
      '.custom-tooltip__trigger[aria-controls="homepage-spending-tip"]'

    cy.visit('/')
    cy.waitForPageLoad()

    cy.get(tooltipBody).should('have.attr', 'hidden')
    cy.get(tooltipTrigger).click()
    cy.get(tooltipBody).should('be.visible').and('not.have.attr', 'hidden')

    cy.checkA11yPage(null, a11yOptions)
  })
})
