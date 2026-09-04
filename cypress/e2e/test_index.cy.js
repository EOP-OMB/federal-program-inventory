describe('Test: index', () => {
  const testUrl = 'test/index.html';
  const tooltipBody = '#homepage-spending-tip';
  const tooltipTrigger = '.custom-tooltip__trigger[aria-controls="homepage-spending-tip"]';
  const tooltipClose = `${tooltipBody} .custom-tooltip__close`;

  it('should load the test page', () => {
    cy.visit(testUrl);
    cy.get('body').should('be.visible');
  });

  it('opens and closes the spending tooltip on desktop', () => {
    cy.viewport('macbook-16');
    cy.visit(testUrl);

    cy.get(tooltipBody).should('have.attr', 'hidden');
    cy.get(tooltipTrigger).click();
    cy.get(tooltipBody).should('be.visible');
    cy.get('body').compareSnapshot('homepage_spending_tooltip_open_desktop');

    cy.get(tooltipTrigger).click();
    cy.get(tooltipBody).should('have.attr', 'hidden');
  });

  it('opens and closes the spending tooltip on tablet', () => {
    cy.visit(testUrl);

    cy.get(tooltipBody).should('have.attr', 'hidden');
    cy.get(tooltipTrigger).click();
    cy.get(tooltipBody).should('be.visible');
    cy.get('.info-sections').first().compareSnapshot('homepage_spending_tooltip_open_tablet');

    cy.get(tooltipTrigger).click();
    cy.get(tooltipBody).should('have.attr', 'hidden');
  });

  it('closes the spending tooltip via icon, close button, and outside click', () => {
    cy.visit(testUrl);

    // Close by clicking the icon again
    cy.get(tooltipTrigger).click();
    cy.get(tooltipBody).should('be.visible');
    cy.get(tooltipTrigger).click();
    cy.get(tooltipBody).should('have.attr', 'hidden');

    // Close by clicking the × button
    cy.get(tooltipTrigger).click();
    cy.get(tooltipBody).should('be.visible');
    cy.get(tooltipClose).click();
    cy.get(tooltipBody).should('have.attr', 'hidden');

    // Close by clicking outside the tooltip
    cy.get(tooltipTrigger).click();
    cy.get(tooltipBody).should('be.visible');
    cy.contains('.font-body-md', 'Programs').click();
    cy.get(tooltipBody).should('have.attr', 'hidden');
  });

  it('opens and closes the spending tooltip on iphone-8', () => {
    cy.viewport('iphone-8');
    cy.visit(testUrl);

    cy.get(tooltipBody).should('have.attr', 'hidden');
    cy.get(tooltipTrigger).click();
    cy.get(tooltipBody).should('be.visible');
    cy.get('.info-sections').first().compareSnapshot('homepage_spending_tooltip_open_iphone8');

    cy.get(tooltipTrigger).click();
    cy.get(tooltipBody).should('have.attr', 'hidden');
  });
});
