describe('About pages', () => {
  it('full page screenshot - about terms', () => {
    cy.viewport('macbook-16');
    cy.visit('about/terms');
    cy.get('body').compareSnapshot('terms');
  });

  it('nav responsiveness', () => {
    cy.viewport('iphone-8');
    cy.visit('about/terms');
    cy.get('body').compareSnapshot('nav_responsiveness');
  });

  it('full page screenshot - about fpi', () => {
    cy.viewport('macbook-16');
    cy.visit('test/about-fpi.html');
    cy.get('body').compareSnapshot('fpi');
  });
});