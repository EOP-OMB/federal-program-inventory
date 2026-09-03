describe('GWO treemap', () => {
  const testUrl = 'test/gwo_treemap.html';

  beforeEach(() => {
    cy.visit(testUrl);
    cy.contains('Government-wide Objective').should('be.visible');
    cy.get('#objectiveChart svg > g > rect', { timeout: 10000 }).should('have.length', 3);
  });

  it('shows a tile for each nonzero program', () => {
    cy.get('#objectiveChart svg > g > rect').should('have.length', 3);
    cy.get('#related-programs table tbody tr')
      .not('[data-total-row]')
      .should('have.length', 5);
  });

  it('shows program labels, percentages in tiles, and wrapping', () => {
    cy.get('#objectiveChart svg text').contains('Test Program One').should('exist');
    cy.get('#objectiveChart svg text').contains('Test Program Two').should('exist');
    cy.get('#objectiveChart svg text').contains('Test Program Three').should('exist');
    cy.get('#objectiveChart svg text').contains('Test Program Zero').should('not.exist');
    cy.get('#objectiveChart svg text').contains('50.0%').should('exist');
    cy.get('#objectiveChart svg text').contains('33.3%').should('exist');
    cy.get('#objectiveChart svg text').contains('16.7%').should('exist');
    cy.get('#objectiveChart').compareSnapshot('gwo_treemap_labels');
  });

  it('shows tooltip with name, amount, and percentage', () => {
    cy.get('#objectiveChart svg > g > rect').first().trigger('mouseover');
    cy.get('.chart-tooltip').should('be.visible');
    cy.get('.chart-tooltip').should('contain.text', 'Test Program One');
    cy.get('.chart-tooltip').should('contain.text', 'Amount:');
    cy.get('.chart-tooltip').should('contain.text', 'Percent: 50.0%');
    cy.get('.chart-tooltip').should('contain.text', 'Data source: USAspending.gov');
  });

  it('navigates to a program when a tile is clicked', () => {
    cy.get('#objectiveChart svg > g > rect').first().click({ force: true });
    cy.location('pathname').should('match', /\/program\/test-(1|2|3)$/);
    cy.contains('Test Program').should('be.visible');
  });

  it('jumps to related programs table', () => {
    cy.get('a[href="#related-programs"]').click();
    cy.location('hash').should('eq', '#related-programs');

    // Assert table is visible without scrolling
    cy.get('#related-programs').should('be.visible');
  });
});
