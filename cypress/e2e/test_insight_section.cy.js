describe('Insight Section', () => {
  it('shows copy for 0 programs', () => {
    cy.visit('test/insight_zero.html');
    cy.get('h3').contains('Insight').should('be.visible');
    cy.contains(
      'No programs are currently working toward this objective as of FY 2024.'
    ).should('be.visible');
    cy.contains('a', 'Large Program').should('not.exist');
    cy.contains('a', 'Small Program').should('not.exist');
  });

  it('shows copy for 1 program', () => {
    cy.visit('test/insight_one.html');
    cy.get('h3').contains('Insight').should('be.visible');
    cy.contains(
      '1 program is working toward this objective, spending $123 in total as of FY 2024.'
    ).should('be.visible');
    cy.contains('a', 'Large Program').should('not.exist');
    cy.contains('a', 'Small Program').should('not.exist');
  });

  it('shows copy for many programs', () => {
    cy.visit('test/insight_many.html');
    cy.get('h3').contains('Insight').should('be.visible');
    cy.contains('3 programs are working toward this objective').should('be.visible');
    cy.contains('spending $456 in total as of FY 2024').should('be.visible');
    cy.contains('a.usa-link', 'Large Program')
      .should('be.visible')
      .and('have.attr', 'href', '/test/large');
    cy.contains('($300)').should('be.visible');
    cy.contains('a.usa-link', 'Small Program')
      .should('be.visible')
      .and('have.attr', 'href', '/test/small');
    cy.contains('($10)').should('be.visible');
  });

  it('shows copy for many programs totaling 0', () => {
    cy.visit('test/insight_many_zero.html');
    cy.get('h3').contains('Insight').should('be.visible');
    cy.contains('3 programs are working toward this objective').should('be.visible');
    cy.contains('spending $0 in total as of FY 2024').should('be.visible');
    cy.contains('a', 'Large Program').should('not.exist');
    cy.contains('a', 'Small Program').should('not.exist');
  });
});
