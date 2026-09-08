describe('Test: _list_section component: one item, category', () => {
  const testUrl = 'test/list_one_item.html';

  beforeEach(() => {
    cy.visit(testUrl);
    cy.get('body').should('be.visible');
  });

  it('should have one item', () => {
    cy.get('.program-filter').should('have.length', 1);
  });

  it('category search page applies Housing filter and shows matching programs', () => {
    cy.get('.program-filter').first().click();

    cy.get('.program-title').should('be.visible');
    cy.get('[aria-controls="categories-section"]').first().click();

    cy.get('input[data-filter-type="category"][data-category-title="Housing"]')
      .should('be.checked');
    cy.get(
      'input[data-filter-type="sub-category"][data-subcategory-title="Housing and Homelessness"]'
    ).should('be.checked');

    cy.contains('.program-title', 'Veterans Housing Guaranteed and Insured Loans')
      .should('be.visible');
    cy.contains(
      '.program-title',
      'Very Low to Moderate Income Housing Loans and Loan Guarantees'
    ).should('be.visible');
    cy.contains('.program-title', 'Credit for low-income housing investments')
      .should('be.visible');
  });
});

describe('Test: _list_section component: multiple items, applicant', () => {
  const testUrl = 'test/list_multiple_items.html';

  beforeEach(() => {
    cy.visit(testUrl);
    cy.get('body').should('be.visible');
  });

  it('should have multiple items', () => {
    cy.get('.program-filter').should('have.length', 2);
  });
});

describe('Test: _list_section component: one item, program type', () => {
  const testUrl = 'test/list_program_type.html';

  beforeEach(() => {
    cy.visit(testUrl);
    cy.get('body').should('be.visible');
  });

  it('should have one item', () => {
    cy.get('.program-filter').should('have.length', 1);
  });

  it('category search page applies program filter and shows matching programs', () => {
    cy.get('.program-filter').first().click();

    cy.get('.program-title').should('be.visible');
    cy.get('[aria-controls="program-type-section"]').first().click();
    
    cy.get('input[data-filter-type="assistance"][data-assistance-title="Direct Payments with Unrestricted Use"]')
      .should('be.checked');

    cy.contains('.program-title', 'Indian Job Placement').should('be.visible');
    cy.contains('.program-title', 'State Select').should('be.visible');
    cy.contains('.program-title', '8(g) State Coastal Zone')
      .should('be.visible');
  });
});

describe('Test: _list_section component: no items', () => {
  const testUrl = 'test/list_no_items.html';

  beforeEach(() => {
    cy.visit(testUrl);
    cy.get('body').should('be.visible');
  });

  it('should have no items', () => {
    cy.get('.program-filter').should('not.exist');
  });
});

describe('Test: _list_section component: beneficiaries', () => {
  const testUrl = 'test/list_beneficiaries.html';

  beforeEach(() => {
    cy.visit(testUrl);
    cy.get('body').should('be.visible');
  });

  it('should have no filter items', () => {
    cy.get('.program-filter').should('not.exist');
  });

  it('should have list items', () => {
    cy.contains('li', 'Child').should('exist');
    cy.contains('li', 'Individual/Family').should('exist');
  });
});