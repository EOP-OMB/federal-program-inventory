describe('Taxonomy filter scenarios', () => {
  const testUrl = 'test/taxonomy_filter_scenarios.html';
  const tableRows = '#taxonomy-gwo-table-body tr';

  const waitForTable = () => {
    cy.get('#taxonomy-filter-panels').should('be.visible');
    cy.get(tableRows).should('have.length.greaterThan', 0);
  };

  const expandCategoryFilters = () => {
    cy.get('button[data-content-id="taxonomy-categories-section"]').click();
    cy.get('#taxonomy-categories-section').should('be.visible');
  };

  it('scenario: default load shows the first page in ascending order', () => {
    cy.visit(testUrl);
    waitForTable();

    cy.get('#taxonomy-results-start').should('have.text', '1');
    cy.get('#taxonomy-results-end').should('have.text', '10');
    cy.get('#taxonomy-results-total').should('have.text', '12');
    cy.get(tableRows).should('have.length', 10);
    cy.get(`${tableRows} td`).first().should('contain.text', 'Alpha Objective');
    cy.contains('a.usa-link', 'Alpha Objective').should(
      'have.attr',
      'href',
      '/gwo/GWO_ALPHA'
    );
    cy.contains('#taxonomy-gwo-table-body td', 'Delta Unmapped Objective')
      .should('be.visible')
      .find('a')
      .should('not.exist');
    cy.get('#taxonomy-gwo-table th[data-column="title"]').should(
      'have.attr',
      'aria-sort',
      'ascending'
    );
  });

  it('scenario: sorting toggles descending order without changing the result count', () => {
    cy.visit(testUrl);
    waitForTable();

    cy.get('#taxonomy-gwo-table th[data-column="title"]').click();
    cy.get('#taxonomy-gwo-table th[data-column="title"]').should(
      'have.attr',
      'aria-sort',
      'descending'
    );
    cy.get(`${tableRows} td`).first().should('contain.text', 'Lima Objective');
    cy.get('#taxonomy-results-total').should('have.text', '12');
  });

  it('scenario: pagination advances to the remaining rows', () => {
    cy.visit(testUrl);
    waitForTable();

    cy.get('#taxonomy-pagination .usa-pagination__next-page').click();
    cy.get('#taxonomy-results-start').should('have.text', '11');
    cy.get('#taxonomy-results-end').should('have.text', '12');
    cy.get(tableRows).should('have.length', 2);
    cy.contains('Kilo Objective').should('be.visible');
    cy.contains('Lima Objective').should('be.visible');
    cy.contains('Alpha Objective').should('not.exist');
  });

  it('scenario: category filter keeps only mapped objectives', () => {
    cy.visit(testUrl);
    waitForTable();
    expandCategoryFilters();

    cy.get(
      'input[data-filter-type="category"][data-category-title="Education"]'
    ).check({ force: true });
    cy.get(
      'input[data-filter-type="sub-category"][data-subcategory-title="K-12 Education"]'
    ).should('be.checked');
    cy.get('#taxonomy-filter-count').should('contain.text', '(2)');
    cy.get(tableRows).should('have.length', 2);
    cy.contains('Alpha Objective').should('be.visible');
    cy.contains('Bravo Objective').should('be.visible');
    cy.contains('Charlie Objective').should('not.exist');
    cy.get('#taxonomy-results-total').should('have.text', '2');
  });

  it('scenario: unmapped category shows the empty-filter state', () => {
    cy.visit(testUrl);
    waitForTable();
    expandCategoryFilters();

    cy.get(
      'input[data-filter-type="category"][data-category-title="Unmapped Category"]'
    ).check({ force: true });
    cy.contains('No items match the selected filters.').should('be.visible');
    cy.get('#taxonomy-results-total').should('have.text', '0');
    cy.get('.usa-pagination__list').should('not.be.visible');
  });

  it('scenario: clear filters restores the full sorted table', () => {
    cy.visit(testUrl);
    waitForTable();
    expandCategoryFilters();

    cy.get(
      'input[data-filter-type="category"][data-category-title="Health"]'
    ).check({ force: true });
    cy.get(tableRows).should('have.length', 1);
    cy.contains('Charlie Objective').should('be.visible');

    cy.get('#taxonomy-clear-button').click();
    cy.get(
      'input[data-filter-type="category"][data-category-title="Health"]'
    ).should('not.be.checked');
    cy.get('#taxonomy-filter-count').should('not.contain.text', '(');
    cy.get('#taxonomy-results-total').should('have.text', '12');
    cy.get(`${tableRows} td`).first().should('contain.text', 'Alpha Objective');
  });

  it('scenario: keyword search hides non-matching category options', () => {
    cy.visit(testUrl);
    waitForTable();
    expandCategoryFilters();

    cy.get('#taxonomy-filter-search').type('unmapped');
    cy.contains('label', 'Unmapped Category', { timeout: 4000 }).should(
      'be.visible'
    );
    cy.contains('label', 'Education', { timeout: 4000 })
      .closest('.taxonomy-filter-option-row')
      .should('have.class', 'hide');
    cy.contains('label', 'Health')
      .closest('.taxonomy-filter-option-row')
      .should('have.class', 'hide');
  });
});
