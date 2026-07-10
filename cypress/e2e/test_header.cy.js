describe('Header Component', () => {
  const testUrl = '/test/index.html';

  it('should display the header', () => {
    cy.visit(testUrl);
    cy.get('header.usa-header').should('be.visible');
  });

  it('visual regression: header with navigation', () => {
    // Set viewport to desktop size to show full navigation
    cy.viewport(1024, 768);
    
    cy.visit(testUrl);
    // Wait for page to fully load
    cy.get('header.usa-header', { timeout: 10000 }).should('exist');
    
    // Verify navigation links are displayed
    cy.get('.custom-accordion-button').should('be.visible');
    cy.contains('.usa-nav__primary-item', 'Program search').should('be.visible');
    cy.contains('.usa-nav__primary-item', /Explore FY \d{4} spending/).should('be.visible');
    cy.contains('.usa-nav__primary-item', 'About the FPI').should('be.visible');
    
    // Take a snapshot of the full header with navigation
    cy.get('header.usa-header').compareSnapshot('header_with_navigation');
  });

  it('visual regression: header with narrow viewport and expanded navigation', () => {
    // Set viewport to show navigation links horizontally but without full desktop size
    cy.viewport(980, 400);
    
    cy.visit(testUrl);
    // Wait for page to fully load
    cy.get('header.usa-header', { timeout: 10000 }).should('exist');
    
    // Check if menu button exists and is visible, if so click it
    cy.get('body').then(($body) => {
      if ($body.find('.usa-menu-btn:visible').length > 0) {
        cy.get('.usa-menu-btn').click();
        cy.get('nav.usa-nav').should('be.visible');
      }
    });
    
    // Click to expand the About the FPI accordion
    cy.get('.custom-accordion-button').click();
    
    // Wait for the accordion content to expand and be visible
    cy.get('.usa-nav__submenu').should('be.visible');
    
    // Take a snapshot of just the navigation area (excluding the logo/header)
    cy.get('nav.usa-nav').compareSnapshot('header_narrow_expanded');
  });
});

