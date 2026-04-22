describe('Program Overview Visualization', () => {
  const svgSelector = '#spending-chart svg';
  const tooltipSelector = '.spending-chart-tooltip';
  const tooltipOverlaySelector = svgSelector + ' > g > rect:last';
  const noChartSelector = '#no-spending-chart';
  const toggleSelector = '#projection-toggle input[type="checkbox"]';

  // Set desktop viewport to avoid mobile CSS breakpoints
  beforeEach(() => {
    cy.viewport(1280, 720);
  });

  // coordinates, find in browser by executing this in console:
  // document.addEventListener('mousemove', function(event) {
  //  console.log('Mouse position (viewport): ' + event.clientX + ', ' + event.clientY);
  // });
  const originX = 0;
  const originY = 0;
  const tooltipX1 = 200;
  const tooltipY1 = 600;
  const tooltipX2 = 746;
  const tooltipY2 = 600;
  const tooltipX3 = 803;
  const tooltipY3 = 600;

  // base case + inflation disabled by default + also tests:
  // 1) a bar is too small to display the label
  it('base case, small bar', () => {
    cy.visit('test/program_spending_chart_base.html');
    cy.get(svgSelector).should('be.visible')
      .parent().parent().parent().compareSnapshot('spending_viz_base');
    cy.get(noChartSelector).should('not.be.visible');
    cy.contains('Inflation + Population').should('be.visible');
  });

  it('negative obligation', () => {
    cy.visit('test/program_spending_chart_neg_obligation.html');
    cy.get(svgSelector).should('be.visible')
      .parent().parent().parent().compareSnapshot('spending_viz_neg_obligation');
    cy.get(noChartSelector).should('not.be.visible');
  });

  it('negative outlay', () => {
    cy.visit('test/program_spending_chart_neg_outlay.html');
    cy.get(svgSelector).should('be.visible')
      .parent().parent().parent().compareSnapshot('spending_viz_neg_outlay');
    cy.get(noChartSelector).should('not.be.visible');
  });

  it('no baseline (toggle hidden)', () => {
    cy.visit('test/program_spending_chart_no_baseline.html');
    cy.get(svgSelector).should('be.visible')
      .parent().parent().parent().compareSnapshot('spending_viz_no_baseline');
    cy.get(noChartSelector).should('not.be.visible');
    cy.contains('Inflation + Population').should('not.be.visible');
  });

  it('outlay label covered', () => {
    cy.visit('test/program_spending_chart_outlay_label_covered.html');
    cy.get(svgSelector).should('be.visible')
      .parent().parent().parent().compareSnapshot('spending_viz_outlay_label_covered');
    cy.get(noChartSelector).should('not.be.visible');
  });

  it('unreported years (treat as 0)', () => {
    cy.visit('test/program_spending_chart_unreported_years.html');
    cy.get(svgSelector).should('be.visible')
      .parent().parent().parent().compareSnapshot('spending_viz_unreported_years');
    cy.get(noChartSelector).should('not.be.visible');

    cy.visit('test/program_spending_chart_data_gaps.html');
    cy.get(svgSelector).should('be.visible')
      .parent().parent().parent().compareSnapshot('spending_viz_unreported_years');
    cy.get(noChartSelector).should('not.be.visible');
  });

  it('no data', () => {
    cy.visit('test/program_spending_chart_no_data.html');
    cy.get(noChartSelector).should('be.visible').compareSnapshot('spending_viz_no_data');
  });

  // lowest negative number is small in magnitude compare to max positive number
  it('negative padding', () => {
    cy.visit('test/program_spending_chart_negative_padding.html');
    cy.get(svgSelector).should('be.visible')
      .parent().parent().parent().compareSnapshot('spending_viz_outlay_negative_padding');
    cy.get(noChartSelector).should('not.be.visible');
  });

  // outlays json is formatted differently
  it('other program spending', () => {
    cy.visit('test/program_spending_chart_other_program_spending.html');
    cy.get(svgSelector).should('be.visible')
      .parent().parent().parent().compareSnapshot('spending_viz_other_program_spending');
    cy.get(noChartSelector).should('not.be.visible');
  });

  // tooltips + inflation
  it('tooltip', () => {
    cy.visit('test/program_spending_chart_base.html');
    cy.get(tooltipOverlaySelector).should('be.visible');
    cy.get(tooltipSelector).should('not.be.visible');

    // move near 2015 datapoint (no inflation)
    cy.get(tooltipOverlaySelector).trigger('mousemove', { clientX: tooltipX1, clientY: tooltipY1 });
    cy.get(tooltipSelector).compareSnapshot('spending_viz_tooltip_no_inflation');
    cy.get(tooltipSelector).should('contain.text', 'Year');
    cy.get(tooltipSelector).should('contain.text', '2015');
    cy.get(tooltipSelector).should('contain.text', 'Obligations');
    cy.get(tooltipSelector).should('contain.text', 'Outlays');

    // move mouse out of chart
    cy.get(tooltipOverlaySelector).trigger('mousemove', { clientX: originX, clientY: originY, force: true });
    cy.get('body').trigger('mousemove', { clientX: originX, clientY: originY, force: true });
    cy.get(tooltipOverlaySelector).trigger('mouseout', { force: true });
    cy.get(tooltipSelector).should('not.be.visible');

    // activate inflation projection line
    cy.get(toggleSelector).check({ force: true });
    cy.get(toggleSelector).should('be.checked');
    cy.get(svgSelector).should('be.visible')
      .parent().parent().parent().compareSnapshot('spending_viz_base_inflation');

    // move near 2019 datapoint (has inflation)
    cy.get(tooltipOverlaySelector).trigger('mousemove', { clientX: tooltipX2, clientY: tooltipY2 });
    cy.get(tooltipSelector).compareSnapshot('spending_viz_tooltip_has_inflation');
    cy.get(tooltipSelector).should('contain.text', 'Year');
    cy.get(tooltipSelector).should('contain.text', '2019');
    cy.get(tooltipSelector).should('contain.text', 'Obligations');
    cy.get(tooltipSelector).should('contain.text', 'Outlays');
    cy.get(tooltipSelector).should('contain.text', 'Projected');
  });

  it('dollar amount formatting', () => {
    cy.visit('test/program_spending_chart_amount_formatting.html');
    cy.get(tooltipOverlaySelector).should('be.visible');
    cy.get(tooltipSelector).should('not.be.visible');

    // move near 2020 datapoint (has untested magnitudes)
    cy.get(tooltipOverlaySelector).trigger('mousemove', { clientX: tooltipX3, clientY: tooltipY3 });
    // Wait for tooltip to be populated with content before asserting
    cy.get(tooltipSelector).should('contain.text', 'Year');
    cy.get(tooltipSelector).should('contain.text', '2020');
    cy.get(tooltipSelector).should('contain.text', '$52M');
    cy.get(tooltipSelector).should('contain.text', '$50B');
    cy.get(tooltipSelector).should('contain.text', '$50T');
  });
});