/// <reference types="cypress" />

// This test checks that the GWO target_count value is correct and visible in the clickable card.
// It visits the test page at /test-gwo-pon-count.html which displays a test card with a known target count.

describe('Target Count Card Validation', () => {
  const testUrl = '/test-gwo-pon-count.html';

  beforeEach(() => {
    // Set a large viewport for accurate card rendering
    cy.viewport(1400, 1000);
  });

  it('shows correct GWO target_count in card', () => {
    cy.visit(testUrl);
    
    // The GWO card should show "Targeted by 5 programs"
    cy.get('[data-testid="gwo-clickable-tile"]').should('exist');
    cy.get('[data-testid="gwo-clickable-tile"]').within(() => {
      cy.get('.text-base').should('contain.text', 'Targeted by 5 programs');
    });
    
    // Take a snapshot of the GWO card for visual regression
    cy.get('[data-testid="gwo-clickable-tile"]').compareSnapshot('gwo-target-count-card');
  });
});
