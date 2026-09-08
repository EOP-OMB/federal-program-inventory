describe('Category page', () => {
  it('category index full page screenshot', () => {
    cy.visit('test/category_index.html');
    cy.get('body').compareSnapshot('category_index_page');
  });

  it('category index full page screenshot - responsiveness', () => {
    cy.viewport('iphone-8');
    cy.visit('test/category_index.html');
    cy.get('body').compareSnapshot('category_index_page_responsiveness');
  });

  it('category full page screenshot', () => {
    cy.visit('test/category.html');
    cy.get('body').compareSnapshot('category_page');
  });

  it('category full page screenshot - responsiveness', () => {
    cy.viewport('iphone-8');
    cy.visit('test/category.html');
    cy.get('body').compareSnapshot('category_page_responsiveness');
    cy.get('label[for="agency"]').click();
    cy.get('#myChart').parent().compareSnapshot('category_page_agency_responsiveness');
    cy.get('label[for="eligible-applicant"]').click();
    cy.get('#myChart').parent().compareSnapshot('category_page_eligible_applicant_responsiveness');
  });

  it('subcategory full page screenshot', () => {
    cy.visit('test/subcategory.html');
    cy.get('body').compareSnapshot('subcategory_page');
  });

  it('subcategory full page screenshot - responsiveness', () => {
    cy.viewport('iphone-8');
    cy.visit('test/subcategory.html');
    cy.get('body').compareSnapshot('subcategory_page_responsiveness');
    cy.get('label[for="agency"]').click();
    cy.get('#myChart').parent().compareSnapshot('subcategory_page_agency_responsiveness');
    cy.get('label[for="eligible-applicant"]').click();
    cy.get('#myChart').parent().compareSnapshot('subcategory_page_eligible_applicant_responsiveness');
  });

  it('subcategory empty programs full page screenshot', () => {
    cy.visit('test/subcategory_empty.html');
    cy.contains('No programs reported for this subcategory at the moment.');
    cy.get('#myChart').should('not.exist');
  });
});