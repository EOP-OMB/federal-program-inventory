describe('Breadcrumbs without Sub-Agency', () => {
  const testUrl = 'test/breadcrumbs_wo_subagency.html';

  beforeEach(() => {
    cy.visit(testUrl);
    cy.get('.usa-breadcrumb').should('be.visible');
  });

  it('shows agency and program crumbs without a sub-agency', () => {
    cy.get('.usa-breadcrumb__list-item').should('have.length', 2);

    cy.get('.usa-breadcrumb__link[data-filter-type="agency"]')
      .should('be.visible')
      .and('contain.text', 'Test Agency')
      .and('have.attr', 'data-agency-title', 'Test Agency');

    cy.get('.usa-breadcrumb__link[data-filter-type="sub-agency"]').should('not.exist');

    cy.get('.usa-breadcrumb__list-item.usa-current')
      .should('be.visible')
      .and('contain.text', 'Program 00.000');
  });
});
