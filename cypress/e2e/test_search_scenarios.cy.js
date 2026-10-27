describe('Search page scenarios', () => {
  const searchUrl = 'test/search.html';

  const emptyResponse = {
    count: 0,
    total_obligations: 0,
    global_program_count: 100,
    global_total_obligations: 1,
    programs: [],
  };

  const programOnPage = (page, index) => ({
    title: `Scenario Program P${page}-${index}`,
    permalink: `/program/scenario-${page}-${index}`,
    popularName: '',
    agency: { title: 'Scenario Agency' },
    obligations: 1000 * page + index,
    objectives: 'Scenario search program',
    programType: 'assistance_listing',
    cfda: `99.00${page}${index}`,
  });

  const parseRequestBody = (req) =>
    typeof req.body === 'string' ? JSON.parse(req.body) : req.body;

  const decodeFiltersFromUrl = (urlString) => {
    const encodedFilters = new URL(urlString).searchParams.get('f');
    expect(encodedFilters, 'encoded filters in URL').to.not.be.null;
    return JSON.parse(decodeURIComponent(atob(encodedFilters)));
  };

  it('scenario: empty results hide the program list and pagination', () => {
    cy.viewport('macbook-16');
    cy.intercept('POST', '/api/search/programsTable', {
      statusCode: 200,
      body: emptyResponse,
    }).as('programsTable');

    cy.visit(searchUrl);
    cy.wait('@programsTable');

    cy.get('.program-title').should('not.exist');
    cy.get('#filtered-count').should('have.text', '0');
    cy.get('#results-start').should('have.text', '0');
    cy.get('#results-end').should('have.text', '0');
    cy.get('#results-total').should('have.text', '0');
    cy.get('.usa-pagination__list').should('not.be.visible');
  });

  it('scenario: API error shows the retry message', () => {
    cy.viewport('macbook-16');
    cy.intercept('POST', '/api/search/programsTable', {
      statusCode: 500,
      body: { error: 'server error' },
    }).as('programsTable');

    cy.visit(searchUrl);
    cy.wait('@programsTable');

    cy.get('#program-list').should(
      'contain.text',
      'Unable to load results. Please try again.'
    );
    cy.get('.program-title').should('not.exist');
  });

  it('scenario: pagination requests the next page and renders its programs', () => {
    cy.viewport('macbook-16');
    cy.intercept('POST', '/api/search/programsTable', (req) => {
      const body = parseRequestBody(req);
      const page = body.page || 1;
      req.reply({
        statusCode: 200,
        body: {
          count: 25,
          total_obligations: 25000,
          global_program_count: 25,
          global_total_obligations: 25000,
          programs: [1, 2, 3].map((index) => programOnPage(page, index)),
        },
      });
    }).as('programsTable');

    cy.visit(searchUrl);
    cy.wait('@programsTable').then((interception) => {
      expect(parseRequestBody(interception.request).page).to.eq(1);
    });
    cy.contains('.program-title', 'Scenario Program P1-1').should('be.visible');
    cy.get('#results-start').should('have.text', '1');
    cy.get('#results-end').should('have.text', '10');
    cy.get('#results-total').should('have.text', '25');

    cy.get('#next-page-button').click();
    cy.wait('@programsTable').then((interception) => {
      expect(parseRequestBody(interception.request).page).to.eq(2);
    });
    cy.contains('.program-title', 'Scenario Program P2-1').should('be.visible');
    cy.contains('.program-title', 'Scenario Program P1-1').should('not.exist');
    cy.get('#results-start').should('have.text', '11');
  });

  it('scenario: agency select-all checks sub-agencies and encodes them in the URL', () => {
    cy.viewport('macbook-16');
    cy.intercept('POST', '/api/search/programsTable', {
      statusCode: 200,
      body: emptyResponse,
    }).as('programsTable');

    cy.visit(searchUrl);
    cy.wait('@programsTable');

    cy.get('[data-content-id="agency-section"]').click();
    cy.get('#agency-section').should('be.visible');
    cy.get(
      'input[data-filter-type="agency"][data-agency-title="Department of Agriculture"]'
    )
      .check({ force: true })
      .should('be.checked')
      .invoke('attr', 'data-children-id')
      .then((childrenId) => {
        cy.get(`#${childrenId} input[data-filter-type="sub-agency"]`)
          .should('have.length.greaterThan', 1)
          .each(($input) => {
            cy.wrap($input).should('be.checked');
          });
      });

    cy.url().then((urlString) => {
      const decodedFilters = decodeFiltersFromUrl(urlString);
      const parentAgency = decodedFilters.a.find((code) =>
        String(code).startsWith('p')
      );
      expect(parentAgency, 'parent agency select-all marker').to.match(/\*$/);
      expect(decodedFilters.a.filter((code) => String(code).startsWith('s')))
        .to.have.length.greaterThan(0);
    });

    cy.wait('@programsTable')
      .its('request.body.agencySubAgency')
      .should('include', 'Department of Agriculture - Agricultural Marketing Service');
  });

  it('scenario: category and assistance filters serialize and restore from the URL', () => {
    cy.viewport('macbook-16');
    cy.intercept('POST', '/api/search/programsTable', {
      statusCode: 200,
      body: emptyResponse,
    }).as('programsTable');

    cy.visit(searchUrl);
    cy.wait('@programsTable');

    cy.get('[data-content-id="categories-section"]').click();
    cy.get(
      'input[data-filter-type="category"][data-category-title="Education"]'
    ).check({ force: true });
    cy.wait('@programsTable');

    cy.get('[data-content-id="program-type-section"]').click();
    cy.get(
      'input[data-filter-type="assistance"][data-assistance-title="Financial"]'
    ).check({ force: true });
    cy.wait('@programsTable');

    cy.get(
      'input[data-filter-type="sub-category"][data-subcategory-title="K\u201312 Education"]'
    ).should('be.checked');

    cy.url().then((urlString) => {
      const decodedFilters = decodeFiltersFromUrl(urlString);
      expect(decodedFilters.c, 'category filters').to.have.length.greaterThan(0);
      expect(decodedFilters.t, 'assistance filters').to.have.length.greaterThan(0);
    });

    cy.reload();
    cy.wait('@programsTable');

    cy.get(
      'input[data-filter-type="category"][data-category-title="Education"]'
    ).should('be.checked');
    cy.get(
      'input[data-filter-type="assistance"][data-assistance-title="Financial"]'
    ).should('be.checked');
    cy.get(
      'input[data-filter-type="sub-category"][data-subcategory-title="K\u201312 Education"]'
    ).should('be.checked');
  });

  it('scenario: an exact CFDA match redirects to the program permalink', () => {
    cy.viewport('macbook-16');
    cy.intercept('POST', '/api/search/programsTable', (req) => {
      const body = parseRequestBody(req);
      if ((body.query || '').toLowerCase() === '99.001') {
        req.reply({
          statusCode: 200,
          body: {
            count: 1,
            total_obligations: 1,
            global_program_count: 1,
            global_total_obligations: 1,
            programs: [
              {
                title: 'Exact Match Program',
                permalink: '/test/index.html',
                cfda: '99.001',
                agency: { title: 'Scenario Agency' },
                obligations: 1,
                objectives: 'Redirects on exact CFDA match',
              },
            ],
          },
        });
        return;
      }

      req.reply({ statusCode: 200, body: emptyResponse });
    }).as('programsTable');

    cy.visit(searchUrl);
    cy.wait('@programsTable');

    cy.get('#search-field-en-small').type('99.001');
    cy.get('.usa-search').submit();
    cy.wait('@programsTable');
    cy.location('pathname').should('eq', '/test/index.html');
  });
});
