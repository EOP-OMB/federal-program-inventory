describe('PON page', () => {
  const testUrl = 'test/pon_treemap.html';

  it('full page screenshot', () => {
    cy.viewport('macbook-16');
    cy.visit(testUrl);
    cy.get('body').compareSnapshot('full_page');
  });

  it('full page screenshot - phone', () => {
    cy.viewport('iphone-8');
    cy.visit(testUrl);
    cy.get('body').compareSnapshot('full_page_responsiveness');
  });
});