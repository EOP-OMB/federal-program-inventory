describe('Improper Payments Section', () => {
  const screenshotSelector = '#improper-payment';

  /* #   FPI:IP   Has Values
   * 1a  1:1      Y
   * 1b  M:1      Y
   * 2a  1:1      N
   * 2b  M:1      N
   * 3a  1:M      Y
   * 3b  M:M      Y
   * 4a  1:M      N
   * 4b  M:M      N
   * 5   0:0      N
   */
  const scenarios = ['1a', '1b', '2a', '2b', '3a', '3b', '4a', '4b', '5'];

  for(let i = 0; i < scenarios.length; ++i) {
    const scenarioId = 'improper_payments_section_' + scenarios[i];
    it('scenario ' + scenarios[i], () => {
        cy.visit('test/' + scenarioId + '.html');
        cy.get(screenshotSelector).should('be.visible').compareSnapshot(scenarioId);
    });
  }
});