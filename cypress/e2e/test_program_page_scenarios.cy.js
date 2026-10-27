describe('Program page scenarios', () => {
  const populatedUrl = 'test/program_page_populated.html';
  const emptyUrl = 'test/program_page_empty.html';
  const objectivesOnlyUrl = 'test/program_page_objectives_only.html';

  const openTab = (tabId, panelId) => {
    cy.get(tabId).click();
    cy.get(tabId).should('have.attr', 'aria-selected', 'true');
    cy.get(panelId).should('be.visible').and('not.have.class', 'display-none');
  };

  it('scenario: populated overview, results, authorization, and oversight', () => {
    cy.viewport('macbook-16');
    cy.visit(populatedUrl);

    cy.contains('h1', 'Scenario Populated Program').should('be.visible');
    cy.contains('Known as Scenario Program').should('be.visible');
    cy.contains(
      'Scenario objective used to confirm the overview description renders.'
    ).should('be.visible');
    cy.get('#purpose-pane').should('be.visible');
    cy.contains('a', 'Provide Scenario Healthcare').should(
      'have.attr',
      'href',
      '/test/gwo_treemap.html'
    );
    cy.contains('a', 'Increase Scenario Health Coverage').should(
      'have.attr',
      'href',
      '/test/pon_treemap.html'
    );
    cy.get('#usaid-alert, .usa-alert--usaid').should('not.exist');

    cy.contains('a', 'View results').click();
    cy.get('#results-tab').should('have.attr', 'aria-selected', 'true');
    cy.get('#results-panel').should('be.visible');
    cy.get('#program-pon-gwo').should('be.visible');
    cy.contains('Objectives:').should('be.visible');
    cy.contains('Outcomes:').should('be.visible');
    cy.get('#program-results').within(() => {
      cy.contains('2024').should('be.visible');
      cy.contains('Scenario result for 2024.').should('be.visible');
      cy.contains('2023').should('be.visible');
    });

    openTab('#authorization-tab', '#authorization-panel');
    cy.contains('a', 'Scenario authorizing statute with link')
      .should('have.attr', 'href', 'https://www.govinfo.gov/link/statute/88/1305')
      .and('have.attr', 'target', '_blank')
      .and('have.attr', 'rel', 'noopener noreferrer');
    cy.contains('Scenario authorizing statute without a link').should(
      'be.visible'
    );
    cy.contains('Scenario oversight rules and regulations').should('be.visible');

    openTab('#oversight-tab', '#oversight-panel');
    cy.get('#program-single-audit .usa-icon.text-success').should('exist');
    cy.get('#program-single-audit .usa-icon.text-error').should('not.exist');
    cy.contains('a', 'Compliance Supplement')
      .should(
        'have.attr',
        'href',
        'https://www.whitehouse.gov/omb/information-resources/guidance/compliance-supplement/'
      )
      .and('contain.text', '(opens in a new tab)');
    cy.get('#program-rules-regs').should(
      'contain.text',
      'Scenario oversight rules and regulations.'
    );
  });

  it('scenario: empty program hides purpose, results, and authorization content', () => {
    cy.viewport('macbook-16');
    cy.visit(emptyUrl);

    cy.contains('h1', 'Scenario Empty Program').should('be.visible');
    cy.contains('Description not yet available.').should('be.visible');
    cy.contains('Known as').should('not.exist');
    cy.get('#purpose-pane').should('not.exist');
    cy.get('#usaid-alert, .usa-alert--usaid').should('not.exist');

    openTab('#results-tab', '#results-panel');
    cy.contains('Information is not yet available.').should('be.visible');
    cy.get('#program-pon-gwo').should('not.exist');
    cy.get('#program-results').should('not.exist');

    openTab('#authorization-tab', '#authorization-panel');
    cy.contains('Not available').should('be.visible');
    cy.contains('Authorizing Statutes').should('not.exist');
    cy.contains('Rules & Regulations').should('not.exist');

    openTab('#oversight-tab', '#oversight-panel');
    cy.get('#program-single-audit .usa-icon.text-error').should('exist');
    cy.get('#program-single-audit .usa-icon.text-success').should('not.exist');
    cy.get('#program-rules-regs').should('not.exist');
  });

  it('scenario: objective without outcomes or results shows fallback copy', () => {
    cy.viewport('macbook-16');
    cy.visit(objectivesOnlyUrl);

    cy.get('#purpose-pane').should('be.visible');
    cy.contains('a', 'Provide Scenario Healthcare').should('be.visible');
    cy.contains('Increase Scenario Health Coverage').should('not.exist');

    openTab('#results-tab', '#results-panel');
    cy.contains('Objectives:').should('be.visible');
    cy.contains('Outcomes not yet available.').should('be.visible');
    cy.get('#program-results').should('not.exist');
    cy.contains('Information is not yet available.').should('not.exist');
  });

  it('scenario: arrow keys move between program tabs', () => {
    cy.viewport('macbook-16');
    cy.visit(populatedUrl);

    cy.get('#overview-tab').should('have.attr', 'aria-selected', 'true').focus();
    cy.get('#overview-tab').type('{rightarrow}');
    cy.get('#spending-tab').should('have.attr', 'aria-selected', 'true');
    cy.get('#spending-panel').should('be.visible');
    cy.get('#overview-panel').should('have.class', 'display-none');

    cy.get('#spending-tab').type('{leftarrow}');
    cy.get('#overview-tab').should('have.attr', 'aria-selected', 'true');
    cy.get('#overview-panel').should('be.visible');
  });
});
