/// <reference types="cypress" />

// This test checks that the GWO and PON target_count values are correct and visible in the clickable cards.
// It visits the test page at /test-gwo-pon-count.html which displays test cards with known target counts.

describe('Target Count Card Validation', () => {
  const testUrl = '/test-gwo-pon-count.html';

  beforeEach(() => {
    // Set a large viewport for accurate card rendering
    cy.viewport(1400, 1000);
  });

  it('shows correct GWO target_count in card', () => {
    cy.visit(testUrl);
    
    // The GWO card should show "Targeted by 5 other programs"
    cy.get('[data-testid="gwo-clickable-tile"]').should('exist');
    cy.get('[data-testid="gwo-clickable-tile"]').within(() => {
      cy.get('.text-base').should('contain.text', 'Targeted by 5 other programs');
    });
    
    // Take a snapshot of the GWO card for visual regression
    cy.get('[data-testid="gwo-clickable-tile"]').compareSnapshot('gwo-target-count-card');
  });

  it('shows correct PON target_count in card', () => {
    cy.visit(testUrl);
    
    // The PON card should show "Targeted by 3 other programs"
    cy.get('[data-testid="pon-clickable-tile"]').should('exist');
    cy.get('[data-testid="pon-clickable-tile"]').within(() => {
      cy.get('.text-base').should('contain.text', 'Targeted by 3 other programs');
    });
    
    // Take a snapshot of the PON card for visual regression
    cy.get('[data-testid="pon-clickable-tile"]').compareSnapshot('pon-target-count-card');
  });
});
