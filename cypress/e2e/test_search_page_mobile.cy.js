describe('Search Page Mobile View Snapshot', () => {
  const testUrl = '/test/search.html';

  it('visual regression: search page full snapshot in mobile view', () => {
    // Set mobile viewport (iPhone 8)
    cy.viewport('iphone-8');
    cy.visit(testUrl);

    // Wait for page shell and search results to render
    cy.get('body', { timeout: 10000 }).should('be.visible');
    cy.get('#program-list .program-search-container', { timeout: 10000 })
      .should('have.length.greaterThan', 0);

    // Take full page snapshot
    cy.get('body').compareSnapshot('search_page_mobile_view');
  });
});
