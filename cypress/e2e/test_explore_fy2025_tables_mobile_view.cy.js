describe('Explore FY 2025 spending table snapshots', () => {
  const testUrl = '/test/test_explore_fy2025_tables_mobile_view.html';

  const waitForTable = (tableSelector) => {
    cy.get(tableSelector, { timeout: 10000 }).should('be.visible');
    cy.get(`${tableSelector} tbody tr`, { timeout: 10000 }).should('have.length.greaterThan', 0);
  };

  it('captures mobile_view snapshots for sub-categories, programs, agencies, and applicant type tables', () => {
    cy.viewport('iphone-8');
    cy.visit(testUrl);

    waitForTable('#sub-categories-table');
    cy.get('#sub-categories-table').compareSnapshot('explore_fy2025_sub_categories_table_mobile_view');

    waitForTable('#programs-table');
    cy.get('#programs-table').compareSnapshot('explore_fy2025_programs_table_mobile_view');

    waitForTable('#agencies-table');
    cy.get('#agencies-table').compareSnapshot('explore_fy2025_agencies_table_mobile_view');

    waitForTable('#applicant-types-table');
    cy.get('#applicant-types-table').compareSnapshot('explore_fy2025_applicant_types_table_mobile_view');
  });
});
