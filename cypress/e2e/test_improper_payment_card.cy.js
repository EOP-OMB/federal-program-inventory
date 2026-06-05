describe('Improper Payment Rate Card', () => {
  // Test pages with controlled improper_payments data
  const testPageZeroRate = '/test-improper-payment-zero-rate.html';
  const testPagePositiveRate = '/test-improper-payment-positive-rate.html';
  const testPageNA = '/test-improper-payment-card-NA.html';

  describe('Program with improper_payments rate = 0%', () => {
    beforeEach(() => {
      cy.visit(testPageZeroRate);
      // Wait for the improper payment container to be rendered with content
      cy.get('#improper-payment-card-container', { timeout: 5000 })
        .should('not.have.css', 'display', 'none');
    });

    it('should display the improper payment section', () => {
      // Wait for the card container to be visible
      cy.get('#improper-payment-card-container')
        .should('be.visible');

      // Check that the improper payment label is visible
      cy.get('.payment-rate-box').contains('Improper Payment').should('be.visible');
    });

    it('should display the improper payment card container', () => {
      // The card container should be visible (not style="display: none;")
      cy.get('#improper-payment-card-container')
        .should('be.visible')
        .should('not.have.css', 'display', 'none');
    });

    it('should display the payment info section with FY expenditure', () => {
      // Check for the FY expenditure section
      cy.get('.payment-info').should('be.visible');
      cy.get('.payment-info').contains('FY').should('be.visible');
      cy.get('.payment-info').contains('Expenditure').should('be.visible');
    });

    it('should display the improper payment rate box', () => {
      // Check for the payment-rate-box
      cy.get('.payment-rate-box').should('be.visible');
      cy.get('.payment-rate-box').contains('Improper Payment').should('be.visible');
    });

    it('should show the percentage and improper payment amount in the badge', () => {
      // Check for the usa-tag with percentage and amount
      cy.get('.usa-tag').should('be.visible');
      cy.get('.usa-tag').should('contain', '%');
      cy.get('.usa-tag').should('contain', '$');
    });

    it('should display correct alignment of left and right sections', () => {
      // Both sections should be visible side by side
      cy.get('.improper-payment-card-container').within(() => {
        cy.get('.payment-info').should('be.visible');
        cy.get('.payment-rate-box').should('be.visible');
      });
    });

    it('visual regression: improper payment card is displayed when page.improper_payments is NOT null (0% rate)', () => {
      // Wait for any animations to complete
      cy.wait(500);
      // Capture the entire grid container to show the card is displayed
      cy.get('.grid-container').compareSnapshot('improper_payment_card_zero_rate');
    });

    it('should display a valid percentage in the card', () => {
      // Extract and validate the percentage is a valid number
      cy.get('.usa-tag').then(($tag) => {
        const text = $tag.text();
        const percentageMatch = text.match(/(\d+\.?\d*)%/);
        expect(percentageMatch).to.exist;
        const percentage = parseFloat(percentageMatch[1]);
        expect(percentage).to.be.at.least(0);
        expect(percentage).to.be.at.most(100);
      });
    });

    it('should display properly formatted currency amounts', () => {
      cy.get('.payment-info .font-heading-xl').should('be.visible');
      cy.get('.payment-info .font-heading-xl').should('contain', '$');
      cy.get('.usa-tag').should('contain', '$');
    });

    it('should have a valid fiscal year label', () => {
      cy.get('.payment-info').contains('FY').should('be.visible');
      cy.get('.payment-info').should('contain', 'Expenditure');
    });
  });

  describe('Program with improper_payments rate > 0%', () => {
    beforeEach(() => {
      cy.visit(testPagePositiveRate);
      // Wait for the improper payment container to be rendered with content
      cy.get('#improper-payment-card-container', { timeout: 5000 })
        .should('not.have.css', 'display', 'none');
    });

    it('should display the improper payment section', () => {
      // Wait for the card container to be visible (JS must create the h2)
      cy.get('#improper-payment-card-container')
        .should('be.visible');

      // Check that the improper payment label is visible
      cy.get('.payment-rate-box').contains('Improper Payment').should('be.visible');
    });

    it('should display the improper payment card container', () => {
      // The card container should be visible (not style="display: none;")
      cy.get('#improper-payment-card-container')
        .should('be.visible')
        .should('not.have.css', 'display', 'none');
    });

    it('should display the payment info section with FY expenditure', () => {
      // Check for the FY expenditure section
      cy.get('.payment-info').should('be.visible');
      cy.get('.payment-info').contains('FY').should('be.visible');
      cy.get('.payment-info').contains('Expenditure').should('be.visible');
    });

    it('should display the improper payment rate box', () => {
      // Check for the payment-rate-box
      cy.get('.payment-rate-box').should('be.visible');
      cy.get('.payment-rate-box').contains('Improper Payment').should('be.visible');
    });

    it('should show the percentage and improper payment amount in the badge', () => {
      // Check for the usa-tag with percentage and amount
      cy.get('.usa-tag').should('be.visible');
      cy.get('.usa-tag').should('contain', '%');
      cy.get('.usa-tag').should('contain', '$');
    });

    it('should display correct alignment of left and right sections', () => {
      // Both sections should be visible side by side
      cy.get('.improper-payment-card-container').within(() => {
        cy.get('.payment-info').should('be.visible');
        cy.get('.payment-rate-box').should('be.visible');
      });
    });

    it('visual regression: improper payment card is displayed when page.improper_payments is NOT null (positive rate)', () => {
      // Wait for any animations to complete
      cy.wait(500);
      // Capture the entire grid container to show the card is displayed
      cy.get('.grid-container').compareSnapshot('improper_payment_card_positive_rate');
    });

    it('should display a valid percentage in the card', () => {
      // Extract and validate the percentage is a valid number
      cy.get('.usa-tag').then(($tag) => {
        const text = $tag.text();
        const percentageMatch = text.match(/(\d+\.?\d*)%/);
        expect(percentageMatch).to.exist;
        const percentage = parseFloat(percentageMatch[1]);
        expect(percentage).to.be.at.least(0);
        expect(percentage).to.be.at.most(100);
      });
    });

    it('should display properly formatted currency amounts', () => {
      cy.get('.payment-info .font-heading-xl').should('be.visible');
      cy.get('.payment-info .font-heading-xl').should('contain', '$');
      cy.get('.usa-tag').should('contain', '$');
    });

    it('should have a valid fiscal year label', () => {
      cy.get('.payment-info').contains('FY').should('be.visible');
      cy.get('.payment-info').should('contain', 'Expenditure');
    });
  });

  describe('Program with improper_payments data not available (N/A)', () => {
    beforeEach(() => {
      cy.visit(testPageNA);
      // Wait for the improper payment container to be rendered with content
      cy.get('#improper-payment-card-container', { timeout: 5000 })
        .should('not.have.css', 'display', 'none');
    });

    it('should display improper payment card in grayed out state when improper_payments is null', () => {
      // When improper_payments is null, the card should display with N/A values
      cy.get('#improper-payment-card-container')
        .should('be.visible');
      cy.get('.improper-payment-card')
        .should('be.visible');
    });

    it('should display N/A values', () => {
      // Check for N/A rate value
      cy.get('#improper-payments-percent').should('contain', 'N/A');
      
      // Check for N/A amount value
      cy.get('#improper-payments-total').should('contain', 'N/A');
    });

    it('should display the payment info section with FY expenditure', () => {
      // Check for the FY expenditure section even when improper payment data is unavailable
      cy.get('.payment-info').should('be.visible');
      cy.get('.payment-info').contains('FY').should('be.visible');
      cy.get('.payment-info').contains('Expenditure').should('be.visible');
    });

    it('should display the improper payment rate box', () => {
      // Check for the payment-rate-box which should be visible
      cy.get('.payment-rate-box').should('be.visible');
    });

    it('should display correct alignment of left and right sections', () => {
      // Both sections should be visible side by side
      cy.get('.improper-payment-card-container').within(() => {
        cy.get('.payment-info').should('be.visible');
        cy.get('.payment-rate-box').should('be.visible');
      });
    });

    it('visual regression: improper payment card is displayed with N/A values when improper_payments is null', () => {
      // Wait for any animations to complete
      cy.wait(500);
      // Capture the entire grid container to show the N/A card is displayed
      cy.get('.grid-container').compareSnapshot('improper_payment_card_NA');
    });
  });

  describe('Program with improper_payments_is_multiple = true', () => {
    beforeEach(() => {
      cy.visit('/test-improper-payment-multiple-rate.html');
      // Wait for the improper payment container to be rendered with content
      cy.get('#improper-payment-card-container', { timeout: 5000 })
        .should('not.have.css', 'display', 'none');
    });

    it('should display the improper payment section', () => {
      // Wait for the card container to be visible
      cy.get('#improper-payment-card-container')
        .should('be.visible');

      // Check that the improper payment label is visible
      cy.get('.payment-rate-box').contains('Improper Payment').should('be.visible');
    });

    it('should display "Multiple" instead of percentage when improper_payments_is_multiple is true', () => {
      // Should show "Rate: Multiple" not a percentage
      cy.get('#improper-payments-percent').should('contain', 'Multiple');
      cy.get('#improper-payments-percent').should('not.contain', '%');
    });

    it('should display "Multiple" instead of dollar amount when improper_payments_is_multiple is true', () => {
      // Should show "Amount: Multiple" not a dollar amount
      cy.get('#improper-payments-total').should('contain', 'Multiple');
      cy.get('#improper-payments-total').should('not.contain', '$');
    });

    it('should display the payment info section with FY expenditure', () => {
      // Check for the FY expenditure section
      cy.get('.payment-info').should('be.visible');
      cy.get('.payment-info').contains('FY').should('be.visible');
      cy.get('.payment-info').contains('Expenditure').should('be.visible');
    });

    it('should display correct alignment of left and right sections', () => {
      // Both sections should be visible side by side
      cy.get('.improper-payment-card-container').within(() => {
        cy.get('.payment-info').should('be.visible');
        cy.get('.payment-rate-box').should('be.visible');
      });
    });

    it('should display the improper payment rate box with proper styling', () => {
      // Check for the payment-rate-box
      cy.get('.payment-rate-box').should('be.visible');
      cy.get('.payment-rate-box').contains('Improper Payment').should('be.visible');
    });

    it('visual regression: improper payment card displays "Multiple" when improper_payments_is_multiple is true', () => {
      // Wait for any animations to complete
      cy.wait(500);
      // Capture the entire grid container to show the multiple rate card is displayed
      cy.get('.grid-container').compareSnapshot('improper_payment_card_multiple_rate');
    });

    it('should have both Rate: Multiple and Amount: Varies in the same badge', () => {
      // Extract and validate both texts appear in the usa-tag
      cy.get('.usa-tag').then(($tag) => {
        const text = $tag.text();
        expect(text).to.contain('Multiple');
        expect(text).to.contain('|'); // Verify the separator is present
      });
    });

    it('should have a valid fiscal year label', () => {
      cy.get('.payment-info').contains('FY').should('be.visible');
      cy.get('.payment-info').should('contain', 'Expenditure');
    });
  });
});