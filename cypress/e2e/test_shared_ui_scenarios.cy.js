describe('Shared UI scenarios', () => {
  const testUrl = 'test/shared_ui_scenarios.html';
  const tooltipBody = '#shared-ui-tip';
  const tooltipTrigger = '.custom-tooltip__trigger[aria-controls="shared-ui-tip"]';
  const dataRows = '#sortable-table-section tbody tr:not([data-total-row])';

  it('scenario: tooltip opens, contains a link, and closes on Escape', () => {
    cy.visit(testUrl);

    cy.get(tooltipBody).should('have.attr', 'hidden');
    cy.get(tooltipTrigger).should('have.attr', 'aria-expanded', 'false').click();
    cy.get(tooltipBody).should('be.visible').and('not.have.attr', 'hidden');
    cy.get(tooltipTrigger).should('have.attr', 'aria-expanded', 'true');
    cy.get(`${tooltipBody} a`)
      .should('have.attr', 'href', 'https://www.usaspending.gov')
      .and('contain.text', 'USAspending.gov');

    cy.get(tooltipTrigger).type('{esc}');
    cy.get(tooltipBody).should('have.attr', 'hidden');
    cy.get(tooltipTrigger)
      .should('have.attr', 'aria-expanded', 'false')
      .and('have.focus');
  });

  it('scenario: external link uses the accessible new-tab pattern', () => {
    cy.visit(testUrl);

    cy.get('#external-link-section a.usa-link')
      .should('have.attr', 'href', 'https://www.usaspending.gov')
      .and('have.attr', 'target', '_blank')
      .and('have.attr', 'rel', 'noopener noreferrer')
      .and('contain.text', 'USAspending.gov')
      .and('contain.text', '(opens in a new tab)');
    cy.get('#external-link-section a .usa-sr-only').should(
      'contain.text',
      '(opens in a new tab)'
    );
    cy.get('#external-link-section a svg.usa-icon').should(
      'have.attr',
      'aria-hidden',
      'true'
    );
  });

  it('scenario: sortable table defaults to amount descending and keeps the total last', () => {
    cy.visit(testUrl);

    cy.get(dataRows).should('have.length', 3);
    cy.get(`${dataRows} td`).eq(0).should('contain.text', 'Alpha Program');
    cy.get(dataRows).eq(1).should('contain.text', 'Mid Program');
    cy.get(dataRows).eq(2).should('contain.text', 'Zebra Program');
    cy.get('#sortable-table-section tbody tr[data-total-row]')
      .should('contain.text', 'Total')
      .find('[data-dollar-amount="600"]')
      .should('exist');

    cy.get('#sortable-table-section th[data-sortable]').first().click();
    cy.get(`${dataRows} td`).eq(0).should('contain.text', 'Zebra Program');
    cy.get('#sortable-table-section tbody tr').last().should(
      'have.attr',
      'data-total-row'
    );

    cy.get('#sortable-table-section th[data-sortable]').first().click();
    cy.get(`${dataRows} td`).eq(0).should('contain.text', 'Alpha Program');
  });
});
