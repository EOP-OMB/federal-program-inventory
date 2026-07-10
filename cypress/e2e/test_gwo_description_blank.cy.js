describe('GWO: description fallback', () => {
  const blankDescriptionUrl = 'test/gwo_blank_description.html';
  const missingDescriptionUrl = 'test/gwo_missing_description.html';

  it('shows default text when description is blank', () => {
    cy.visit(blankDescriptionUrl);
    cy.contains('Government-wide Objective').should('be.visible');
    cy.contains('Description not yet available').should('be.visible');
  });

  it('shows default text when description is missing', () => {
    cy.visit(missingDescriptionUrl);
    cy.contains('Government-wide Objective').should('be.visible');
    cy.contains('Description not yet available').should('be.visible');
  });
});
