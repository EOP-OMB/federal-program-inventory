describe('PON treemap', () => {
  const testUrl = 'test/pon_treemap.html';

  beforeEach(() => {
    cy.visit(testUrl);
    cy.contains('Program Outcome').should('be.visible');
    cy.get('#outcomeChart svg > g > rect', { timeout: 10000 }).should('have.length', 3);
  });

  it('shows a tile for each nonzero program', () => {
    cy.get('#outcomeChart svg > g > rect').should('have.length', 3);
    cy.get('#related-programs table tbody tr')
      .not('[data-total-row]')
      .should('have.length', 4);
    cy.get('#outcomeChart').compareSnapshot('pon_treemap');
  });

  it('shows program labels and percentages in tiles', () => {
    cy.get('#outcomeChart svg text').contains('Test Program One').should('exist');
    cy.get('#outcomeChart svg text').contains('Test Program Two').should('exist');
    cy.get('#outcomeChart svg text').contains('Test Program Three').should('exist');
    cy.get('#outcomeChart svg text').contains('Test Program Zero').should('not.exist');
    cy.get('#outcomeChart svg text').contains('50.0%').should('exist');
    cy.get('#outcomeChart svg text').contains('33.3%').should('exist');
    cy.get('#outcomeChart svg text').contains('16.7%').should('exist');
    cy.wait(1000);
    cy.get('#outcomeChart').compareSnapshot('pon_treemap_labels');
  });

  it('shows tooltip with name, amount, and percentage', () => {
    cy.get('#outcomeChart svg > g > rect').first().trigger('mouseover');
    cy.get('.chart-tooltip').should('be.visible');
    cy.get('.chart-tooltip').should('contain.text', 'Test Program One');
    cy.get('.chart-tooltip').should('contain.text', 'Amount:');
    cy.get('.chart-tooltip').should('contain.text', 'Percent: 50.0%');
    cy.wait(1000);
    cy.get('#outcomeChart').compareSnapshot('pon_treemap_tooltip');
  });

  it('navigates to a program when a tile is clicked', () => {
    cy.get('#outcomeChart svg > g > rect').first().click({ force: true });
    cy.location('pathname').should('match', /\/program\/test-(1|2|3)$/);
    cy.contains('Test Program').should('be.visible');
  });

  it('jumps to related programs table', () => {
    cy.get('a[href="#related-programs"]').click();
    cy.location('hash').should('eq', '#related-programs');
    cy.get('#related-programs').should('be.visible');

    // Assert table is visible without scrolling
    cy.get('#related-programs').should('be.visible');
  });
});
