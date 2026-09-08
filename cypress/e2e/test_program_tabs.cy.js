describe('Program tabs', () => {
  it('full page screenshots', () => {
    cy.viewport('macbook-16');
    cy.visit('test/program_tabs.html');
    cy.get('body').compareSnapshot('overview');
    cy.get('#spending-tab').click();
    cy.get('.grid-container').compareSnapshot('spending');
    cy.get('#results-tab').click();
    cy.get('.grid-container').compareSnapshot('results');
    cy.get('#authorization-tab').click();
    cy.get('.grid-container').compareSnapshot('authorization');
    cy.get('#oversight-tab').click();
    cy.get('.grid-container').compareSnapshot('oversight');
  });

  it('full page screenshots - responsiveness', () => {
    cy.viewport('iphone-8');
    cy.visit('test/program_tabs.html');
    cy.get('body').compareSnapshot('overview_responsiveness');
    cy.get('#spending-tab').click();
    cy.get('.grid-container').compareSnapshot('spending_responsiveness');
    cy.get('#results-tab').click();
    cy.get('.grid-container').compareSnapshot('results_responsiveness');
    cy.get('#authorization-tab').click();
    cy.get('.grid-container').compareSnapshot('authorization_responsiveness');
    cy.get('#oversight-tab').click();
    cy.get('.grid-container').compareSnapshot('oversight_responsiveness');
  });
});