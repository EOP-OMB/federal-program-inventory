describe('Program Overview Mobile View Snapshot', () => {
  const testUrl = '/test-program-overview-mobile';

  it('visual regression: program overview page full snapshot in mobile view', () => {
    // Set mobile viewport (iPhone X)
    cy.viewport('iphone-x');
    cy.visit(testUrl);

    // Wait for all assets to load
    cy.get('body', { timeout: 10000 }).should('be.visible');
    cy.get('.grid-container', { timeout: 5000 }).should('be.visible');

    // Take full page snapshot
    cy.get('body').compareSnapshot('program_overview_mobile_view');
  });
});

