describe('Search page', () => {
  it('wider viewport + applicant wrapping screenshot', () => {
    cy.viewport('macbook-16');
    cy.visit('test/search.html');

    cy.get('.usa-sidenav').eq(5).click();
    cy.get('#check-applicant-3')
      .parent()
      .compareSnapshot('search_page_applicant_wrapped');
    cy.get('#check-applicant-4')
      .parent()
      .compareSnapshot('search_page_applicant_not_wrapped');
  });

  it('search within pon', () => {
    cy.viewport('macbook-16');
    cy.visit('test/search.html');

    cy.get('.usa-sidenav').eq(3).click();
    cy.get('#pon-filter-search').type('advance');
    cy.contains('Construct New Community Infrastructure').should('not.be.visible');
    cy.get('#search-filters').compareSnapshot('search_page_pon_filter');
  });

  it('sorting', () => {
    cy.viewport('macbook-16');
    cy.visit('test/search.html');

    cy.intercept('POST', '/api/search/programsTable').as('programsTable')
    cy.get('#programNameSort').click();
    cy.wait('@programsTable').its('response.statusCode').should('eq', 200);
    cy.get('.program-title')
      .eq(0)
      .should('contain.text', '100,000 Strong');
  });

  it('serializes and restores agency, gwo, and pon filters from URL', () => {
    cy.viewport('macbook-16');
    cy.intercept('POST', '/api/search/programsTable').as('programsTable');
    cy.visit('test/search.html');
    cy.wait('@programsTable').its('response.statusCode').should('eq', 200);

    cy.get('[data-content-id="agency-section"]').click();
    cy.get('input[data-filter-type="agency"][data-agency-title="Department of Agriculture"]')
      .check({ force: true });
    cy.wait('@programsTable');

    cy.get('[data-content-id="gwo-section"]').click();
    cy.get('div:not(.facet-hidden):not(.hide) > div.usa-checkbox > input[data-filter-type="gwo"]')
      .first().check({ force: true }).invoke('attr', 'data-gwo-title')
      .as('selectedGwoTitle');
    cy.wait('@programsTable');

    cy.get('[data-content-id="pons-section"]').click();
    cy.get('div:not(.facet-hidden):not(.hide) > div.usa-checkbox > input[data-filter-type="pon"]')
      .first().check({ force: true }).invoke('attr', 'data-pon-title')
      .as('selectedPonTitle');
    cy.wait('@programsTable');

    cy.url().then((urlString) => {
      const url = new URL(urlString);
      const encodedFilters = url.searchParams.get('f');
      expect(encodedFilters, 'encoded filters in URL').to.not.be.null;

      const decodedFilters = JSON.parse(decodeURIComponent(atob(encodedFilters)));
      expect(decodedFilters.a, 'agency filters').to.have.length.greaterThan(0);
      expect(decodedFilters.gwo, 'gwo filters').to.have.length.greaterThan(0);
      expect(decodedFilters.pon, 'pon filters').to.have.length.greaterThan(0);
    });

    cy.reload();
    cy.wait('@programsTable').its('response.statusCode').should('eq', 200);

    cy.get('input[data-filter-type="agency"][data-agency-title="Department of Agriculture"]')
      .should('be.checked');
    cy.get('@selectedGwoTitle').then((selectedGwoTitle) => {
      cy.get(`input[data-filter-type="gwo"][data-gwo-title="${selectedGwoTitle}"]`)
        .should('be.checked');
    });
    cy.get('@selectedPonTitle').then((selectedPonTitle) => {
      cy.get(`input[data-filter-type="pon"][data-pon-title="${selectedPonTitle}"]`)
        .should('be.checked');
    });
  });

  it('restores search text and result count after refresh', () => {
    cy.viewport('macbook-16');
    cy.intercept('POST', '/api/search/programsTable').as('programsTable');
    cy.visit('test/search.html');
    cy.wait('@programsTable').its('response.statusCode').should('eq', 200);

    cy.get('#filtered-count')
      .should('not.have.prop', 'innerText', '')
      .invoke('text')
      .as('originalCount', { type: 'static' });

    cy.get('#search-field-en-small').type('test{enter}');
    cy.wait('@programsTable').its('response.statusCode').should('eq', 200);

    cy.get('@originalCount').then((originalCount) => {
      cy.get('#filtered-count').should('not.have.text', originalCount);
    });

    cy.get('#filtered-count')
      .invoke('text')
      .then((resultCountText) => {
        const capturedResultCount = resultCountText.trim();

        cy.reload();
        cy.wait('@programsTable').its('response.statusCode').should('eq', 200);

        cy.get('#search-field-en-small').should('have.value', 'test');
        cy.get('#filtered-count').should(($resultCount) => {
          expect($resultCount.text().trim()).to.eq(capturedResultCount);
        });
      });
  });

  it('clears search, applicant filters, and restores global filtered count', () => {
    cy.viewport('macbook-16');
    cy.intercept('POST', '/api/search/programsTable').as('programsTable');
    cy.visit('test/search.html');
    cy.wait('@programsTable').its('response.statusCode').should('eq', 200);

    cy.get('#global-count')
      .should('not.have.prop', 'innerText', '')
      .invoke('text')
      .as('globalCount', { type: 'static' });

    cy.get('#search-field-en-small').type('state{enter}');
    cy.wait('@programsTable').its('response.statusCode').should('eq', 200);

    cy.get('[data-content-id="eligible-applicants-section"]').click();
    cy.get('input[data-filter-type="applicant"]')
      .first()
      .check({ force: true });
    cy.wait('@programsTable').its('response.statusCode').should('eq', 200);

    cy.contains('button', 'Clear Filters')
      .should('have.attr', 'aria-disabled', 'false')
      .click();
    cy.wait('@programsTable').its('response.statusCode').should('eq', 200);

    cy.get('@globalCount').then((globalCount) => {
      cy.get('#filtered-count').should('have.text', globalCount);
    });

    cy.get('#search-field-en-small').should('have.value', '');
    cy.get('input[data-filter-type="applicant"]:checked').should('have.length', 0);
    cy.get('#filtered-count').then(($filteredCount) => {
      const filteredCountText = $filteredCount.text().trim();
      cy.get('#global-count').should(($globalCount) => {
        expect(filteredCountText).to.eq($globalCount.text().trim());
      });
    });
  });

  // full page screenshot and filtering is tested by some tag tests
});