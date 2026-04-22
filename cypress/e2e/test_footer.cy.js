describe('Footer and Footer Banner Components', () => {
  const testUrl = '/test/index.html';

  it('should display the footer', () => {
    cy.visit(testUrl);
    cy.get('footer.width-full').should('be.visible');
  });

  it('should display the footer banner', () => {
    cy.visit(testUrl);
    cy.get('[role="footer-banner"]').should('be.visible');
  });

  it('should display footer links', () => {
    cy.visit(testUrl);
    cy.contains('a', 'Accessibility').should('be.visible');
    cy.contains('a', 'Privacy Policy').should('be.visible');
    cy.contains('a', 'Freedom of Information Act').should('be.visible');
    cy.contains('a', 'No FEAR Act').should('be.visible');
    cy.contains('a', 'Inspector General').should('be.visible');
    cy.contains('a', '© 2026 Federal Program Inventory').should('be.visible');
  });

  it('visual regression: footer banner snapshot', () => {
    cy.viewport(1024, 768);
    cy.visit(testUrl);

    // Wait for footer banner to load
    cy.get('[role="footer-banner"]', { timeout: 10000 }).should('exist');
    
    // Scroll to ensure footer banner is in view
    cy.scrollTo('bottom');
    cy.wait(500);
    
    // Take a snapshot of the footer banner
    cy.get('[role="footer-banner"]').compareSnapshot('footer_banner');
  });

  it('visual regression: footer snapshot', () => {
    cy.viewport(1024, 768);
    cy.visit(testUrl);

    // Wait for footer to load
    cy.get('footer.padding-0', { timeout: 10000 }).should('exist');
    
    // Scroll to ensure footer is in view
    cy.scrollTo('bottom');
    cy.wait(500);
    
    // Take a snapshot of the footer
    cy.get('footer.padding-0').compareSnapshot('footer');
  });

  it('should display return to top link when scrolled to bottom', () => {
    cy.visit(testUrl);
    
    // Return to top link should be hidden initially
    cy.get('#return-to-top').should('not.be.visible');
    
    // Scroll to bottom
    cy.scrollTo('bottom');
    
    // Return to top link should now be visible
    cy.get('#return-to-top').should('be.visible');
    cy.contains('a', 'Return to top').should('be.visible');
  });

  it('visual regression: footer snapshot with return to top link visible', () => {
    // See cypress/md/footer_scroll.md for expected behavior
    cy.viewport(1024, 768);
    cy.visit('/test-footer-scroll.html');

    // Scroll to bottom to make "Return to top" link visible
    cy.scrollTo('bottom');
    cy.wait(500);
    
    // Verify the return to top link is visible
    cy.get('#return-to-top').should('be.visible');
    
    // Take a snapshot of the entire page to show footer with return to top link visible
    cy.get('body').compareSnapshot('footer_with_return_to_top');
  });
});
