describe('USAID special cases', () => {
  it('should show alert on program page', () => {
    cy.visit('test/usaid_program.html');
    cy.get('.usa-alert')
      .should('contain.text', 'Important USAID Information')
      .compareSnapshot('alert');
  });

  // USAID is hidden from the search page filters, but that is done
  //  via the data pipeline
});
