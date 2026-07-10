describe('Visited Program Links with #6E5841 Color', () => {
  it('should display visited links on test page', () => {
    // Visit the test page with visited link styling
    cy.visit('/test-visited-links.html');
    
    // Wait for page content to load
    cy.get('h1', { timeout: 10000 }).should('be.visible');
    
    // Verify visited links exist with test-visited class
    cy.get('a.test-visited', { timeout: 5000 }).should('have.length', 2);
    
    // Verify links render with correct text
    cy.get('a.test-visited').first().should('contain.text', 'Largest Program');
    cy.get('a.test-visited').last().should('contain.text', 'Smallest Program');
    
    // Capture full page visual snapshot for regression testing
    // Screenshot will alert us if color or styling changes
    cy.get('body').compareSnapshot('visited_links_page');
  });
});
