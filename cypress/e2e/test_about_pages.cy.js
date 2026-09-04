describe('About pages', () => {
  it('full page screenshot - about terms', () => {
    cy.viewport('macbook-16');
    cy.visit('about/terms');
    cy.get('body').compareSnapshot('terms');
  });

  it('nav responsiveness', () => {
    cy.viewport('iphone-8');
    cy.visit('about/terms');
    cy.get('body').compareSnapshot('nav_responsiveness');
  });

  it('full page screenshot - about fpi', () => {
    cy.viewport('macbook-16');
    cy.visit('test/about-fpi.html');
    cy.get('body').compareSnapshot('fpi');
  });

  it('downloads all files from the about download table', () => {
    cy.visit('about/terms');

    cy.get('#about-download-table-container a[download]')
      .should('have.length.greaterThan', 0)
      .each(($anchor, index) => {
        const href = $anchor.prop('href');
        const alias = `downloadFile${index}`;

        cy.intercept('GET', href).as(alias);
        cy.wrap($anchor).click();
        cy.wait(`@${alias}`).then((interception) => {
          const { response } = interception;
          const contentType = response?.headers?.['content-type'] || '';
          const locationHeader = response?.headers?.location;

          expect(response?.statusCode).to.be.oneOf([200, 304]);
          expect(response?.statusCode, `unexpected redirect for ${href}`).to.not.be.oneOf([301, 302, 303, 307, 308]);
          expect(locationHeader, `redirect location header should be absent for ${href}`).to.not.exist;
          expect(contentType, `expected file content for ${href}, got HTML fallback`).to.not.include('text/html');
        });
      });
  });
});