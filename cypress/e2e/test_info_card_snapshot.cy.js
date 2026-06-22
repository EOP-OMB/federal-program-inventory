describe('Info Card Snapshot and Text Verification', () => {
  const gwoTestPage = 'test/test-gwo-info-card.html';
  const ponTestPage = 'test/test-pon-info-card.html';

  describe('GWO Info Card', () => {
    beforeEach(() => {
      cy.visit(gwoTestPage);
      // Wait for the page to fully load
      cy.get('.info-card-bg', { timeout: 5000 }).should('be.visible');
    });

    it('should display the info card with Programs, FY title, and Agencies', () => {
      // Verify the info cards are present
      cy.get('.info-card-bg').should('have.length.gte', 3);
      
      // Verify Programs card is visible
      cy.get('.info-card-title').contains('Programs').should('be.visible');
      
      // Verify at least one info-card title has an FY year label.
      cy.get('.info-card-title').then(($titles) => {
        const hasFyTitle = [...$titles].some((el) => {
          const normalized = el.textContent.replace(/\s+/g, ' ').trim();
          return /^FY\s\d{4}(\b|\s|$)/.test(normalized);
        });
        expect(hasFyTitle).to.equal(true);
      });
      
      // Verify Agencies card is visible
      cy.get('.info-card-title').contains('Agencies').should('be.visible');
    });

    it('should NOT contain "Expended so far this year" text', () => {
      // Verify the text is not present anywhere on the page
      cy.contains('Expended so far this year').should('not.exist');
      
      // Also check that info cards don't contain this text
      cy.get('.info-card-bg').each(($card) => {
        cy.wrap($card).should('not.contain', 'Expended so far this year');
      });
    });

    it('should take a snapshot of the GWO info card section', () => {
      // Get the info card container and take a snapshot
      cy.get('.info-card-bg').first().parent().then(($parent) => {
        cy.wrap($parent).compareSnapshot('gwo-info-card');
      });
    });

    it('should verify info card structure and styling', () => {
      cy.get('.info-card-bg').first().within(() => {
        // Verify header with title
        cy.get('.info-card-header').should('be.visible');
        cy.get('.info-card-title').should('be.visible');
        
        // Verify display number (the value)
        cy.get('.text-bold').should('be.visible');
      });
    });
  });

  describe('PON Info Card', () => {
    beforeEach(() => {
      cy.visit(ponTestPage);
      // Wait for the page to fully load
      cy.get('.info-card-bg', { timeout: 5000 }).should('be.visible');
    });

    it('should display the info card with Programs, FY title, and Agencies', () => {
      // Verify the info cards are present
      cy.get('.info-card-bg').should('have.length.gte', 3);
      
      // Verify Programs card is visible
      cy.get('.info-card-title').contains('Programs').should('be.visible');
      
      // Verify at least one info-card title has an FY year label.
      cy.get('.info-card-title').then(($titles) => {
        const hasFyTitle = [...$titles].some((el) => {
          const normalized = el.textContent.replace(/\s+/g, ' ').trim();
          return /^FY\s\d{4}(\b|\s|$)/.test(normalized);
        });
        expect(hasFyTitle).to.equal(true);
      });
      
      // Verify Agencies card is visible
      cy.get('.info-card-title').contains('Agencies').should('be.visible');
    });

    it('should NOT contain "Expended so far this year" text', () => {
      // Verify the text is not present anywhere on the page
      cy.contains('Expended so far this year').should('not.exist');
      
      // Also check that info cards don't contain this text
      cy.get('.info-card-bg').each(($card) => {
        cy.wrap($card).should('not.contain', 'Expended so far this year');
      });
    });

    it('should take a snapshot of the PON info card section', () => {
      // Get the info card container and take a snapshot
      cy.get('.info-card-bg').first().parent().then(($parent) => {
        cy.wrap($parent).compareSnapshot('pon-info-card');
      });
    });

    it('should verify info card structure and styling', () => {
      cy.get('.info-card-bg').first().within(() => {
        // Verify header with title
        cy.get('.info-card-header').should('be.visible');
        cy.get('.info-card-title').should('be.visible');
        
        // Verify display number (the value)
        cy.get('.text-bold').should('be.visible');
      });
    });
  });

  describe('Cross-Page Text Verification', () => {
    it('should verify no page contains "Expended so far this year" text', () => {
      // Test GWO page
      cy.visit(gwoTestPage);
      cy.contains('Expended so far this year').should('not.exist');
      
      // Test PON page
      cy.visit(ponTestPage);
      cy.contains('Expended so far this year').should('not.exist');
    });
  });
});
