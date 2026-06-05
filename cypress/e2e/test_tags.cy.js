describe('Tag functionality and visual regression', () => {
  let tag_test = function(url, subcategory) {
    let tag_selector = '.radius-pill.program-filter';
    cy.visit('test/program_test_4_tags.html');
    cy.waitForPageLoad();

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

    // search results / functionality
    cy.waitForPageLoad();
    cy.get('[aria-controls="categories-section"]')
      .should('be.visible')
      .first()
      .click();

    cy.get('.program-title').should('be.visible');
    if (subcategory) {
      cy.compareSnapshot('tag_click_subcategory');
    } else {
      cy.compareSnapshot('tag_click_category');
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