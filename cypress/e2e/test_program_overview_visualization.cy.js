describe('Program Overview Visualization', () => {
  const svgSelector = '#chart svg';
  const tooltipSelector = '.outlays-chart-tooltip';
  const tooltipOverlaySelector = svgSelector + ' > g > rect';
  const noChartSelector = '#no-chart';

  // coordinates, find in browser by executing this in console:
  // document.addEventListener('mousemove', function(event) {
  //  console.log('Mouse position (viewport): ' + event.clientX + ', ' + event.clientY);
  // });
  const originX = 0;
  const originY = 0;
  const legendItemX = 530;
  const legendItemY1 = 290;
  const legendItemY2 = 310;
  const tooltipX1 = 300;
  const tooltipY1 = 500;
  const tooltipX2 = 400;
  const tooltipY2 = 300;

  // base case + also tests:
  // 1) obligations < outlays
  // 2) outlays null in a year
  it('base case, obligations < outlays, outlays null', () => {
    cy.visit('test/program_overview_chart_base.html');
    cy.get(svgSelector).should('be.visible').compareSnapshot('overview_viz_base');
    cy.get(noChartSelector).should('not.be.visible');
  });

  // 3) missing one data series cases and 10) one series always zero
  // currently, 3 and 10 are the same case, because null is not loaded into the md files
  it('missing data series cases', () => {
    cy.visit('test/program_overview_chart_no_outlays.html');
    cy.get(svgSelector).should('be.visible').compareSnapshot('overview_viz_no_outlays');

    cy.visit('test/program_overview_chart_no_obligations.html');
    cy.get(svgSelector).should('be.visible').compareSnapshot('overview_viz_no_obligations');
  });

  // 4) missing both data series case
  it('missing data series case', () => {
    cy.visit('test/program_overview_chart_no_data.html');
    cy.get(noChartSelector).should('be.visible');
  });

  // 5) one year case, 6) no fill for one year case, and 7) show obligation point when only one point
  it('one year case', () => {
    cy.visit('test/program_overview_chart_one_year.html');
    cy.get(svgSelector).should('be.visible').compareSnapshot('overview_viz_one_year');
  });

  // 9) one year case with coinciding data
  it('one year case - stacked', () => {
    cy.visit('test/program_overview_chart_one_year_stacked.html');
    cy.get(svgSelector).should('be.visible').compareSnapshot('overview_viz_one_year_stacked');
  });

  // outlays json is formatted differently
  it('other program spending', () => {
    cy.visit('test/program_overview_chart_other_program_spending.html');
    cy.get(svgSelector).should('be.visible').compareSnapshot('overview_viz_other_program_spending');
  });

  // legend + 8) coincide case
  it('legend + coincide case', () => {
    const legendItemSelector = svgSelector + ' .legend-item';
    cy.visit('test/program_overview_chart_coincide.html');
    cy.get(svgSelector).should('be.visible').compareSnapshot('overview_viz_coincide');

    // hover over outlays legend item
    cy.get(legendItemSelector).first().trigger('mousemove', { clientX: legendItemX, clientY: legendItemY1, force: true });
    cy.get(legendItemSelector).first().trigger('mouseenter', { clientX: legendItemX, clientY: legendItemY1, force: true });
    cy.get(svgSelector).compareSnapshot('overview_viz_coincide_outlays');

    // hover over obligations legend item
    cy.get(legendItemSelector).last().trigger('mousemove', { clientX: legendItemX, clientY: legendItemY2, force: true });
    cy.get(legendItemSelector).first().trigger('mouseleave', { force: true });
    cy.get(legendItemSelector).last().trigger('mouseenter', { clientX: legendItemX, clientY: legendItemY2, force: true });
    cy.get(svgSelector).compareSnapshot('overview_viz_coincide_obligations');

    // move mouse out of legend
    cy.get('body').trigger('mousemove', { clientX: originX, clientY: originY, force: true });
    cy.get(legendItemSelector).last().trigger('mouseleave', { force: true });
    cy.get(svgSelector).compareSnapshot('overview_viz_coincide');
  });

  // tooltips
  it('tooltip', () => {
    cy.visit('test/program_overview_chart_base.html');
    cy.get(tooltipOverlaySelector).should('be.visible');
    cy.get(tooltipSelector).should('not.be.visible');

    // move near 2021 datapoint
    cy.get(tooltipOverlaySelector).trigger('mousemove', { clientX: tooltipX1, clientY: tooltipY1 });
    cy.get(tooltipSelector).compareSnapshot('overview_viz_tooltip');
    cy.get(tooltipSelector).should('contain.text', 'Year');
    cy.get(tooltipSelector).should('contain.text', '2021');
    cy.get(tooltipSelector).should('contain.text', 'Obligations');
    cy.get(tooltipSelector).should('contain.text', 'Outlays');

    // move near 2023 datapoint (tooltip should be x-driven, so y should not matter)
    cy.get(tooltipOverlaySelector).trigger('mousemove', { clientX: tooltipX2, clientY: tooltipY2, force: true });
    cy.get(tooltipSelector).should('contain.text', '2023');

    // move mouse out of chart
    cy.get('body').trigger('mousemove', { clientX: originX, clientY: originY, force: true });
    cy.get(tooltipOverlaySelector).trigger('mouseout', { force: true });
    cy.get(tooltipSelector).should('not.be.visible');
  });
});