describe('Authorization tab', () => {
  const bothUrl = 'test/authorization_tab_both.html';
  const noRule = 'test/authorization_tab_no_rule.html';
  const noAuth = 'test/authorization_tab_no_auth.html';
  const neither = 'test/authorization_tab_neither.html';

  it('rules and authorizations show', () => {
    cy.visit(bothUrl);
    cy.get('.grid-container').should('be.visible');
    cy.contains('Test rule').should('be.visible');
    cy.contains('Social Security Act of 1935').should('be.visible');
    cy.contains('a', 'Test auth with link').should('be.visible');
  });

  it('rules only shows', () => {
    cy.visit(noAuth);
    cy.get('.grid-container').should('be.visible');
    cy.contains('Test rule').should('be.visible');
    cy.contains('Social Security Act of 1935').should('not.exist');
    cy.contains('a', 'Test auth with link').should('not.exist');
  });

  it('auth only shows', () => {
    cy.visit(noRule);
    cy.get('.grid-container').should('be.visible');
    cy.contains('Test rule').should('not.exist');
    cy.contains('Social Security Act of 1935').should('be.visible');
    cy.contains('a', 'Test auth with link').should('be.visible');
  });

  it('neither shows', () => {
    cy.visit(neither);
    cy.get('.grid-container').should('be.visible');
    cy.contains('Test rule').should('not.exist');
    cy.contains('Social Security Act of 1935').should('not.exist');
    cy.contains('a', 'Test auth with link').should('not.exist');
    cy.contains('Not available').should('be.visible');
  });

  it('page should match', () => {
    cy.visit(bothUrl);
    cy.get('.grid-container').should('be.visible');
    cy.get('.grid-container').compareSnapshot('authorization_tab_both');
  });
});