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
    '/category',
  ]

  // Define additional test pages (fixture pages) to scan for accessibility issues. Add test pages here as needed for comprehensive component-level accessibility testing.
  const testPagesToScan = [
    '/test/index.html',
    '/test-footer-scroll.html',
    '/test-gwo-pon-count.html',
    '/test-improper-payment-card-NA.html',
    '/test-improper-payment-multiple-rate.html',
    '/test-improper-payment-positive-rate.html',
    '/test-improper-payment-zero-rate.html',
    '/test-visited-links.html',
    '/test/authorization_tab_both.html',
    '/test/authorization_tab_neither.html',
    '/test/authorization_tab_no_auth.html',
    '/test/authorization_tab_no_rule.html',
    '/test/breadcrumbs_w_subagency.html',
    '/test/breadcrumbs_wo_subagency.html',
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
  ]

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
  }

  it('checks /search with expanded filter state for 508 issues', () => {
    cy.visit('/search')
    cy.waitForPageLoad()

    cy.get('button[data-content-id="agency-section"]').click()
    cy.get('#agency-section').should('be.visible')

    cy.get('button[data-content-id="categories-section"]').click()
    cy.get('#categories-section').should('be.visible')

    cy.checkA11yPage(null, a11yOptions)
  })

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
      cy.checkA11yPage(panel, a11yOptions)
    })
  })
})