describe('Improper Payments Section', () => {
  const section = '#improper-payment';
  const ipDefinition =
    'Improper payments are payments that were not made in the correct amount';
  const notAtRisk =
    'This program is not at risk of significant improper payments.';
  const multipleIpPrograms =
    'There are multiple Improper Payment Programs associated with this FPI Program.';
  const multipleFpiPrograms =
    'There are multiple FPI Programs associated with the Improper Payment Program.';
  const multipleIpAndFpiPrograms =
    'There are multiple Improper Payment Programs associated with this FPI Program and additional FPI Programs associated with the Improper Payment Programs.';

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

  it('scenario 1a: one FPI program, one IP program with values', () => {
    cy.visit('test/improper_payments_section_1a.html');
    cy.get(section).within(() => {
      cy.contains(ipDefinition).should('be.visible');
      cy.contains(notAtRisk).should('not.exist');
      cy.contains(multipleIpPrograms).should('not.exist');
      cy.contains(multipleFpiPrograms).should('not.exist');
      cy.contains(
        'The table below shows the Improper Payment Program associated with this FPI Program.'
      ).should('be.visible');
      cy.get('table.usa-table tbody tr').should('have.length', 1);
      cy.contains('a', 'Old-Age and Survivors Insurance (OASI)')
        .should('be.visible')
        .and(
          'have.attr',
          'href',
          'https://paymentaccuracy.gov/program/ssa-old-age-and-survivors-insurance-oasi'
        );
      cy.contains('0.1%').should('be.visible');
      cy.contains('10-2023 to 09-2024').should('be.visible');
      cy.contains('a', 'PaymentAccuracy.gov').should(
        'have.attr',
        'href',
        'https://paymentaccuracy.gov'
      );
    });
  });

  it('scenario 1b: multiple FPI programs, one IP program with values', () => {
    cy.visit('test/improper_payments_section_1b.html');
    cy.get(section).within(() => {
      cy.contains(ipDefinition).should('be.visible');
      cy.contains(multipleFpiPrograms).should('be.visible');
      cy.contains(multipleIpPrograms).should('not.exist');
      cy.contains(
        'The table below shows the Improper Payment Program associated with this FPI Program.'
      ).should('be.visible');
      cy.get('table.usa-table tbody tr').should('have.length', 1);
      cy.contains('a', 'Old-Age and Survivors Insurance (OASI)').should(
        'be.visible'
      );
      cy.contains(
        'The FPI Programs listed below are also associated with the Improper Payment Program.'
      ).should('be.visible');
      cy.contains('a', 'Social Security Survivors Insurance')
        .should('be.visible')
        .and('have.attr', 'href', '/program/96.004');
    });
  });

  it('scenario 2a: one FPI program, one IP program without values', () => {
    cy.visit('test/improper_payments_section_2a.html');
    cy.get(section).within(() => {
      cy.contains(notAtRisk).should('be.visible');
      cy.contains(ipDefinition).should('be.visible');
      cy.contains(multipleIpPrograms).should('not.exist');
      cy.contains(multipleFpiPrograms).should('not.exist');
      cy.contains(
        'The Improper Payment Program listed below is associated with this FPI Program.'
      ).should('be.visible');
      cy.get('table.usa-table').should('not.exist');
      cy.get('ul li').should('have.length', 1);
      cy.contains('a', 'Departmental Offices - Emergency Rental Assistance')
        .should('be.visible')
        .and(
          'have.attr',
          'href',
          'https://paymentaccuracy.gov/program/treasury-departmental-offices-emergency-rental-assistance'
        );
    });
  });

  it('scenario 2b: multiple FPI programs, one IP program without values', () => {
    cy.visit('test/improper_payments_section_2b.html');
    cy.get(section).within(() => {
      cy.contains(notAtRisk).should('be.visible');
      cy.contains(ipDefinition).should('be.visible');
      cy.contains(multipleFpiPrograms).should('be.visible');
      cy.contains(
        'The Improper Payment Program listed below is associated with this FPI Program.'
      ).should('be.visible');
      cy.get('table.usa-table').should('not.exist');
      cy.contains('a', 'Salaries & Expenses')
        .should('be.visible')
        .and('have.attr', 'href', 'https://paymentaccuracy.gov/agency/USDA');
      cy.contains(
        'The FPI Programs listed below are also associated with the Improper Payment Program.'
      ).should('be.visible');
      cy.contains('a', 'Consumer Data and Nutrition Research').should(
        'have.attr',
        'href',
        '/program/10.253'
      );
      cy.contains(
        'a',
        'Research Innovation and Development Grants in Economic (RIDGE)'
      ).should('have.attr', 'href', '/program/10.255');
      cy.contains('a', 'Census of Agriculture').should(
        'have.attr',
        'href',
        '/program/10.951'
      );
    });
  });

  it('scenario 3a: one FPI program, multiple IP programs with values', () => {
    cy.visit('test/improper_payments_section_3a.html');
    cy.get(section).within(() => {
      cy.contains(ipDefinition).should('be.visible');
      cy.contains(notAtRisk).should('not.exist');
      cy.contains(multipleIpPrograms).should('be.visible');
      cy.contains(multipleFpiPrograms).should('not.exist');
      cy.contains(
        'The table below shows all Improper Payment Programs associated with this FPI Program.'
      ).should('be.visible');
      cy.get('table.usa-table tbody tr').should('have.length', 3);
      cy.contains('a', 'Paycheck Protection Program (PPP) Loan Approvals')
        .should('be.visible')
        .and(
          'have.attr',
          'href',
          'https://paymentaccuracy.gov/program/sba-paycheck-protection-program-ppp-loan-approvals'
        );
      cy.contains('a', 'Paycheck Protection Program (PPP) Loan Forgiveness')
        .should('be.visible');
      cy.contains('19.0%').should('be.visible');
      cy.contains('04-2024 to 03-2025').should('be.visible');
      cy.contains(
        'a',
        'Paycheck Protection Program (PPP) Loan Guaranty Purchases'
      ).should('be.visible');
      cy.contains('5.2%').should('be.visible');
    });
  });

  it('scenario 3b: multiple FPI programs, multiple IP programs with values', () => {
    cy.visit('test/improper_payments_section_3b.html');
    cy.get(section).within(() => {
      cy.contains(ipDefinition).should('be.visible');
      cy.contains(notAtRisk).should('not.exist');
      cy.contains(multipleIpAndFpiPrograms).should('be.visible');
      cy.contains(
        'The table below shows all Improper Payment Programs associated with this FPI Program.'
      ).should('be.visible');
      cy.get('table.usa-table tbody tr').should('have.length', 12);
      cy.contains('a', 'Centers for Medicare & Medicaid Services (CMS) - Medicare Advantage (Part C)')
        .should('be.visible');
      cy.contains('6.1%').should('be.visible');
      cy.contains(
        'a',
        'Centers for Medicare & Medicaid Services (CMS) - Medicare Fee-for-Service (FFS)'
      ).should('be.visible');
      cy.contains('6.6%').should('be.visible');
      cy.contains(
        'The FPI Programs listed below are also associated with the Improper Payment Programs.'
      ).should('be.visible');
      cy.contains('a', 'Social Insurance for Railroad Workers').should(
        'have.attr',
        'href',
        '/program/57.006'
      );
      cy.contains('a', 'Medicare Hospital Insurance').should(
        'have.attr',
        'href',
        '/program/93.773'
      );
    });
  });

  it('scenario 4a: one FPI program, multiple IP programs without values', () => {
    cy.visit('test/improper_payments_section_4a.html');
    cy.get(section).within(() => {
      cy.contains(notAtRisk).should('be.visible');
      cy.contains(ipDefinition).should('be.visible');
      cy.contains(multipleIpPrograms).should('be.visible');
      cy.contains(multipleFpiPrograms).should('not.exist');
      cy.contains(
        'The Improper Payment Programs listed below are associated with this FPI Program.'
      ).should('be.visible');
      cy.get('table.usa-table').should('not.exist');
      cy.get('ul li').should('have.length', 3);
      cy.contains('a', 'Paycheck Protection Program (PPP) Loan Approvals')
        .should('be.visible');
      cy.contains('a', 'Paycheck Protection Program (PPP) Loan Forgiveness')
        .should('be.visible');
      cy.contains(
        'a',
        'Paycheck Protection Program (PPP) Loan Guaranty Purchases'
      ).should('be.visible');
    });
  });

  it('scenario 4b: multiple FPI programs, multiple IP programs without values', () => {
    cy.visit('test/improper_payments_section_4b.html');
    cy.get(section).within(() => {
      cy.contains(notAtRisk).should('be.visible');
      cy.contains(ipDefinition).should('be.visible');
      cy.contains(multipleIpAndFpiPrograms).should('be.visible');
      cy.contains(
        'The Improper Payment Programs listed below are associated with this FPI Program.'
      ).should('be.visible');
      cy.get('table.usa-table').should('not.exist');
      cy.contains('a', 'Paycheck Protection Program (PPP) Loan Approvals')
        .should('be.visible');
      cy.contains('a', 'Paycheck Protection Program (PPP) Loan Forgiveness')
        .should('be.visible');
      cy.contains(
        'a',
        'Paycheck Protection Program (PPP) Loan Guaranty Purchases'
      ).should('be.visible');
      cy.contains(
        'The FPI Programs listed below are also associated with the Improper Payment Programs.'
      ).should('be.visible');
      cy.contains('a', 'Social Insurance for Railroad Workers').should(
        'have.attr',
        'href',
        '/program/57.006'
      );
      cy.contains('a', 'Medicare Hospital Insurance').should(
        'have.attr',
        'href',
        '/program/93.773'
      );
    });
  });

  it('scenario 5: no improper payment mappings', () => {
    cy.visit('test/improper_payments_section_5.html');
    cy.get(section).within(() => {
      cy.contains(ipDefinition).should('not.exist');
      cy.contains(notAtRisk).should('not.exist');
      cy.contains(
        'This is a new program or an existing program being listed for the first time.'
      ).should('be.visible');
      cy.get('table.usa-table').should('not.exist');
      cy.contains('a', 'PaymentAccuracy.gov').should(
        'have.attr',
        'href',
        'https://paymentaccuracy.gov'
      );
    });
  });
});
