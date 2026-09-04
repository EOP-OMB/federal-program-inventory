describe('FPI Taxonomy snapshots', () => {
  const testUrl = '/about/taxonomy';

  const waitForTaxonomy = () => {
    cy.get('#taxonomy-filter-panels', { timeout: 10000 }).should('be.visible');
    cy.get('#taxonomy-gwo-table', { timeout: 10000 }).should('be.visible');
    cy.get('#taxonomy-gwo-table-body tr', { timeout: 10000 }).should('have.length.greaterThan', 0);
  };

  it('captures a full taxonomy snapshot', () => {
    cy.viewport('macbook-16');
    cy.visit(testUrl);

    waitForTaxonomy();
    cy.get('body').compareSnapshot('taxonomy_page');
  });

  it('captures a full taxonomy mobile snapshot', () => {
    cy.viewport('iphone-8');
    cy.visit(testUrl);

    waitForTaxonomy();
    cy.get('body').compareSnapshot('taxonomy_page_mobile');
  });
});