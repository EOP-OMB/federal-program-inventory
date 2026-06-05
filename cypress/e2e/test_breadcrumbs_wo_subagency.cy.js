describe('Visual Regression: Breadcrumbs without Sub-Agency', () => {
  const testUrl = 'test/breadcrumbs_wo_subagency.html';

  beforeEach(() => {
    cy.visit(testUrl);
    // Wait for the chart to fully render
    cy.get('.usa-breadcrumb').should('be.visible');
    cy.wait(1000); // Allow time for animations/rendering
  });

  it('page should match', () => {
    cy.compareSnapshot('breadcrumbs_w_subagency');
  });
});