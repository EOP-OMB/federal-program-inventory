describe('Data source labels', () => {
  it('search page obligations tooltip shows data source label', () => {
    let hoverX;
    let hoverY;

    const singleProgramResponse = {
      count: 1,
      total_obligations: 760419098000,
      global_program_count: 1,
      global_total_obligations: 760419098000,
      programs: [
        {
          title: 'Test Medicaid Program',
          permalink: '/program/test-medicaid',
          popularName: '',
          agency: {
            title: 'Department of Health and Human Services'
          },
          obligations: 760419098000,
          objectives: 'Test program for stable tooltip snapshot testing.',
          data_source: 'USAspending.gov',
          programType: 'assistance_listing'
        }
      ]
    };

    cy.viewport('macbook-16');
    cy.intercept('POST', '/api/search/programsTable', {
      statusCode: 200,
      body: singleProgramResponse
    });

    cy.visit('test/search');

    cy.contains('.program-title', 'Test Medicaid Program')
      .should('be.visible');

    cy.get('.program-obligations-tooltip').trigger('mouseenter', 'center');

    cy.get('.program-obligations-hover-tooltip')
      .should('exist')
      .should('contain.text', 'Data source:')
      .should('contain.text', 'USAspending.gov');

    cy.get('.program-results').compareSnapshot('search_data_source_tooltip');
  });

  it('overview chart tooltip shows data source label', () => {
    cy.visit('test/program_overview_chart_base.html');

    cy.window().then((win) => {
      const chartElement = win.document.getElementById('chart');
      const rawData = JSON.parse(chartElement.getAttribute('data-outlays') || '[]');
      const has2026Point = rawData.some((point) => String(point.x) === '2026');
      const seededData = has2026Point
        ? rawData
        : [...rawData, { x: '2026', outlay: 53, obligation: 65 }];

      const formattedData = win.standardizeDataForD3(seededData, true);
      win.createOutlaysVsSpendChart('#chart', formattedData, 'assistance_listing');
    });

    cy.get('#chart svg > g > rect').should('be.visible').then(($overlay) => {
      const rect = $overlay[0].getBoundingClientRect();
      const hoverX = Math.floor(rect.right - 2);
      const hoverY = Math.floor(rect.top + (rect.height / 2));

      cy.wrap($overlay)
        .trigger('mousemove', { clientX: hoverX, clientY: hoverY, force: true });
    });

    cy.get('.outlays-chart-tooltip')
      .should('be.visible')
      .should('contain.text', 'Year: 2026')
      .should('contain.text', 'Outlays')
      .should('contain.text', 'Obligations')
      .should('contain.text', 'SAM.gov est.')
      .should('contain.text', 'USAspending.gov');

    cy.get('#chart').compareSnapshot('overview_chart_data_source_tooltip');
  });

  it('spending chart tooltip shows data source label', () => {
    cy.visit('test/program_spending_chart_base.html');

    cy.get('#spending-chart svg > g > rect:last').should('be.visible')
      .trigger('mousemove', { clientX: 200, clientY: 600, force: true });

    cy.get('.spending-chart-tooltip')
      .should('be.visible')
      .should('contain.text', 'Data source:');
  });

  it('gwo treemap and related table tooltips show data source labels', () => {
    cy.visit('test/gwo_treemap.html');
    let relatedTooltipX;
    let relatedTooltipY;

    cy.get('#objectiveChart').scrollIntoView();
    cy.get('#objectiveChart svg > g > rect').first().should('be.visible')
      .trigger('mouseover');

    cy.get('.chart-tooltip')
      .should('be.visible')
      .should('contain.text', 'Data source:')
      .should('contain.text', 'USAspending.gov')
      .should('contain.text', 'Test Program One');

    cy.get('body').trigger('mousemove', { clientX: 0, clientY: 0, force: true });
    cy.get('a[href="#related-programs"]').click();
    cy.location('hash').should('eq', '#related-programs');
    cy.get('#related-programs').scrollIntoView().should('be.visible');

    cy.get('#related-programs th')
      .filter((_, el) => (el.innerText || '').includes('FY'))
      .first()
      .invoke('index')
      .then((fyColumnIndex) => {
      const column = fyColumnIndex + 1;
      cy.get(`#related-programs tbody tr:not([data-total-row]) td:nth-child(${column})`)
        .first()
        .should('be.visible')
        .then(($cell) => {
          const cellRect = $cell[0].getBoundingClientRect();
          relatedTooltipX = Math.floor(cellRect.left + (cellRect.width / 2));
          relatedTooltipY = Math.floor(cellRect.top + (cellRect.height / 2));

          cy.wrap($cell)
            .trigger('mouseenter', { force: true })
            .trigger('mousemove', {
              clientX: relatedTooltipX,
              clientY: relatedTooltipY,
              force: true
            });
        });
      });

    cy.get('.program-obligations-hover-tooltip')
      .should('have.length', 1)
      .should('exist')
      .should('contain.text', 'Data source:');
  });

  it('pon treemap and related table tooltips show data source labels', () => {
    cy.visit('test/pon_treemap.html');
    let relatedTooltipX;
    let relatedTooltipY;

    cy.get('#outcomeChart').scrollIntoView();
    cy.get('#outcomeChart svg > g > rect').first().should('be.visible')
      .trigger('mouseover');

    cy.get('.chart-tooltip')
      .should('be.visible')
      .should('contain.text', 'Data source: USAspending.gov')
      .should('contain.text', 'Test Program One');

    cy.get('body').trigger('mousemove', { clientX: 0, clientY: 0, force: true });
    cy.get('a[href="#related-programs"]').click();
    cy.location('hash').should('eq', '#related-programs');
    cy.get('#related-programs').scrollIntoView().should('be.visible');

    cy.get('#related-programs th')
      .filter((_, el) => (el.innerText || '').includes('FY'))
      .first()
      .invoke('index')
      .then((fyColumnIndex) => {
      const column = fyColumnIndex + 1;
      cy.get(`#related-programs tbody tr:not([data-total-row]) td:nth-child(${column})`)
        .first()
        .should('be.visible')
        .then(($cell) => {
          const cellRect = $cell[0].getBoundingClientRect();
          relatedTooltipX = Math.floor(cellRect.left + (cellRect.width / 2));
          relatedTooltipY = Math.floor(cellRect.top + (cellRect.height / 2));

          cy.wrap($cell)
            .trigger('mouseenter', { force: true })
            .trigger('mousemove', {
              clientX: relatedTooltipX,
              clientY: relatedTooltipY,
              force: true
            });
        });
      });

    cy.get('.program-obligations-hover-tooltip')
      .should('have.length', 1)
      .should('exist')
      .should('contain.text', 'Data source: USAspending.gov');
  });
});
