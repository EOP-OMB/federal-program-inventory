describe('Category page', () => {
  it('full page screenshot', () => {
    cy.visit('test/category.html');
    cy.get('body').compareSnapshot('category_page');
  });

  it('full page screenshot - responsiveness', () => {
    cy.viewport('iphone-8');
    cy.visit('test/category.html');
    cy.get('body').compareSnapshot('category_page_responsiveness');
  });
});