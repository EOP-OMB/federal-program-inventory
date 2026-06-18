describe('Visual Regression: Breadcrumbs with Sub-Agency', () => {
  const testUrl = 'test/breadcrumbs_w_subagency.html';

  beforeEach(() => {
    cy.visit(testUrl);
    // Wait for the chart to fully render
    cy.get('.usa-breadcrumb').should('be.visible');
  });

  it('page should match', () => {
    cy.compareSnapshot('breadcrumbs_w_subagency');
  });
});