describe('Category and subcategory scenarios', () => {
  const k12Title = 'K\u201312 Education';

  it('scenario: empty subcategory shows the empty-state copy and hides tables', () => {
    cy.visit('test/subcategory_empty.html');

    cy.contains(
      'No programs reported for this subcategory at the moment.'
    ).should('be.visible');
    cy.get('#view-by-selector').should('not.exist');
    cy.get('#programs-table').should('not.exist');
    cy.get('#agencies-table').should('not.exist');
    cy.get('#applicant-types-table').should('not.exist');
    cy.get('#myChart').should('not.exist');
  });

  it('scenario: subcategory view-by radios show the matching table', () => {
    cy.visit('test/subcategory.html');

    cy.get('#view-by-selector').should('be.visible');
    cy.get('#program').should('be.checked');
    cy.get('#programs-table')
      .should('be.visible')
      .find('tbody tr')
      .should('have.length', 6);
    cy.get('#agencies-table').should('not.be.visible');
    cy.get('#applicant-types-table').should('not.be.visible');
    cy.contains('#programs-table a', 'Burial Expenses Allowance for Veterans')
      .should('have.attr', 'href', '/program/64.101');

    cy.get('label[for="agency"]').click();
    cy.get('#agency').should('be.checked');
    cy.get('#agencies-table').should('be.visible');
    cy.get('#programs-table').should('not.be.visible');
    cy.contains('#agencies-table a', 'Department of Veterans Affairs').should(
      'be.visible'
    );

    cy.get('label[for="eligible-applicant"]').click();
    cy.get('#eligible-applicant').should('be.checked');
    cy.get('#applicant-types-table').should('be.visible');
    cy.get('#agencies-table').should('not.be.visible');
    cy.contains('#applicant-types-table a', 'Veteran (including dependents)').should(
      'be.visible'
    );
  });

  it('scenario: subcategory pagination and title sort stay on the fixture page', () => {
    cy.visit('test/subcategory_pagination.html');

    cy.get('#programs-table tbody tr').should('have.length', 10);
    cy.get('#results-start').should('have.text', '1');
    cy.get('#results-end').should('have.text', '10');
    cy.get('#results-total').should('have.text', '12');
    cy.contains('#programs-table a', 'Alpha Burial Program').should('be.visible');
    cy.contains('#programs-table a', 'Lima Burial Program').should('not.exist');

    cy.get('#next-page-button').click();
    cy.get('#results-start').should('have.text', '11');
    cy.get('#programs-table tbody tr').should('have.length', 2);
    cy.contains('#programs-table a', 'Kilo Burial Program').should('be.visible');
    cy.contains('#programs-table a', 'Lima Burial Program').should('be.visible');
    cy.contains('#programs-table a', 'Alpha Burial Program').should('not.exist');

    cy.get('#prev-page-button').click();
    cy.get('#programs-table th[data-column="title"]').click();
    cy.get('#programs-table tbody tr')
      .first()
      .should('contain.text', 'Lima Burial Program');
  });

  it('scenario: category view-by radios show the matching table', () => {
    cy.visit('test/category.html');

    cy.get('#view-by-selector').should('be.visible');
    cy.get('#subCategory').should('be.checked');
    cy.get('#sub-categories-table')
      .should('be.visible')
      .find('tbody tr')
      .should('have.length', 2);
    cy.contains('#sub-categories-table a', 'Burial Benefits').should(
      'have.attr',
      'href',
      '/category/income-security-and-social-services/burial-benefits'
    );
    cy.get('#agencies-table').should('not.be.visible');

    cy.get('label[for="agency"]').click();
    cy.get('#agency').should('be.checked');
    cy.get('#agencies-table').should('be.visible');
    cy.get('#sub-categories-table').should('not.be.visible');
    cy.get('#agencies-table tbody tr').should('have.length.greaterThan', 0);

    cy.get('label[for="eligible-applicant"]').click();
    cy.get('#eligible-applicant').should('be.checked');
    cy.get('#applicant-types-table').should('be.visible');
    cy.get('#agencies-table').should('not.be.visible');
  });

  it('scenario: category dropdown enables subcategories without leaving the fixture', () => {
    cy.visit('test/category.html');

    cy.get('#category option[value="/category/education"]').should('exist');
    cy.get('#subcategory').should('be.disabled');
    cy.get('#category').select('/category/education', { force: true });
    cy.get('#subcategory').should('not.be.disabled');
    cy.get('#subcategory option').should('contain.text', k12Title);
    cy.get('#category-button').should('be.visible');
    cy.location('pathname').should('include', '/test/category');
  });
});
