const fs = require('fs');
const yaml = require('js-yaml');

describe('Test: index', () => {
  const testUrl = 'test/index.html';

  it('should load the test page', () => {
    cy.visit(testUrl);
    cy.get('body').should('be.visible');
  });
});


