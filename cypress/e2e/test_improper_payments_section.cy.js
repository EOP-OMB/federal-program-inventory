describe('Improper Payments Section', () => {
  const screenshotSelector = '#improper-payment';

  /*
   * 1:  has non-zero IP, lacks related programs, and one timeframe
   * 2a: has non-zero IP, has related programs, and one timeframe
   * 2b: has non-zero IP, has related programs, and multiple timeframes
   * 3:  lacks non-zero IP (has mappings), lacks related programs
   * 4:  lacks non-zero IP (has mappings), has related programs
   * 5:  lacks mappings
   */
  const scenarios = ['1', '2a', '2b', '3', '4', '5'];

  for(let i = 0; i < scenarios.length; ++i) {
    const scenarioId = 'improper_payments_section_' + scenarios[i];
    it('scenario ' + scenarios[i], () => {
        cy.visit('test/' + scenarioId + '.html');
        cy.get(screenshotSelector).should('be.visible').compareSnapshot(scenarioId);
    });
  }
});