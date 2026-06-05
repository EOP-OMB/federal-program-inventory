describe('Visual Regression: Insight Section', () => {
  const testCases = [
    { name: 'insight_zero', url: 'test/insight_zero.html' },
    { name: 'insight_one', url: 'test/insight_one.html' },
    { name: 'insight_many', url: 'test/insight_many.html' },
    { name: 'insight_many_zero', url: 'test/insight_many_zero.html' }
  ];

  testCases.forEach(({ name, url }) => {
    it(`page should match for ${name}`, () => {
      cy.visit(url);
      cy.waitForPageLoad();
      cy.get('h3').contains('Insight').should('be.visible');
      cy.wait(1000); // Allow time for fonts and layout to settle
      cy.compareSnapshot(name);
    });
  });
});
