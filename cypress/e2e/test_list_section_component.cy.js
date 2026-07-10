describe('Test: _list_section component: one item, category', () => {
  const testUrl = 'test/list_one_item.html';

  beforeEach(() => {
    cy.visit(testUrl);
    cy.get('body').should('be.visible');
  });

  it('should have one item', () => {
    cy.get('.program-filter').should('have.length', 1);
  });

  it('page should match', () => {
    cy.compareSnapshot('list_one_item');
  });

  it('category search page matches', () => {
    cy.get('.program-filter').first().click();

    // wait for search page to load and search results to show
    cy.get('.program-title').should('be.visible');
    cy.get('[aria-controls="categories-section"]').first().click();
    cy.compareSnapshot('list_one_item_clicked');
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

  it('page should match', () => {
    cy.compareSnapshot('list_multiple_items');
  });

  it('assistance search page matches', () => {
    cy.get('.program-filter').first().click();

    // wait for search page to load and search results to show
    cy.get('.program-title').should('be.visible');
    cy.get('[aria-controls="eligible-applicants-section"]').first().click();
    cy.compareSnapshot('list_multiple_items_clicked');
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

  it('page should match', () => {
    cy.compareSnapshot('list_program_type');
  });

  it('program type search page matches', () => {
    cy.get('.program-filter').first().click();

    // wait for search page to load and search results to show
    cy.get('.program-title').should('be.visible');
    cy.get('[aria-controls="program-type-section"]').first().click();
    cy.compareSnapshot('list_program_type_clicked');
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

  it('page should match', () => {
    cy.compareSnapshot('list_no_items');
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

  it('page should match', () => {
    cy.compareSnapshot('list_beneficiaries');
  });
});