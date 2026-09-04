describe('Tag functionality and visual regression', () => {
  let tag_test = function(url, subcategory) {
    let tag_selector = '.radius-pill.program-filter';
    cy.visit('test/program_test_4_tags.html');

    // visual regression
    cy.get(tag_selector)
      .first()
      .parent()
      .compareSnapshot('tag_appearance');

    // category and subcategory should both appear
    cy.get(tag_selector).should('have.length', 2);
    if (subcategory) {
      cy.get(tag_selector).eq(1).click();
    } else {
      cy.get(tag_selector).first().click();
    }

    cy.get('[aria-controls="categories-section"]')
      .should('be.visible')
      .first()
      .click();

    cy.get('.program-title').should('be.visible');
    if (subcategory) {
      cy.get('[aria-controls="categories-section"]').first().click();
      
      cy.get('input[data-filter-type="sub-category"][data-subcategory-title="Personal Financial Health"]')
        .should('be.checked');

      cy.contains('.program-title', 'Exclusion of employer contributions').should('be.visible');
      cy.contains('.program-title', 'Veterans Compensation').should('be.visible');
      cy.contains('.program-title', 'Exclusion of net imputed rental income')
        .should('be.visible');
    } else {
      cy.get('[aria-controls="categories-section"]').first().click();
      
      cy.get('input[data-filter-type="category"][data-category-title="Income Security and Social Services"]')
        .should('be.checked');
      cy.get('input[data-filter-type="sub-category"][data-subcategory-title="Personal Financial Health"]')
        .should('be.checked');
      cy.get('input[data-filter-type="sub-category"][data-subcategory-title="Burial Benefits"]')
        .should('be.checked');

      cy.contains('.program-title', 'Exclusion of employer contributions').should('be.visible');
      cy.contains('.program-title', 'Veterans Compensation').should('be.visible');
      cy.contains('.program-title', 'Exclusion of net imputed rental income')
        .should('be.visible');
    }
  };

  it('Tags search category on program page', () => {
    tag_test('test/program_test_4_tags.html', false);
  });

  it('Tags search subcategory on program page', () => {
    tag_test('test/program_test_4_tags.html', true);
  });

  it('Tags search category on gwo page', () => {
    tag_test('test/gwo_tags.html', false);
  });

  it('Tags search subcategory on gwo page', () => {
    tag_test('test/gwo_tags.html', true);
  });

  it('Tags search category on pon page', () => {
    tag_test('test/pon_tags.html', false);
  });

  it('Tags search subcategory on pon page', () => {
    tag_test('test/pon_tags.html', true);
  });
});