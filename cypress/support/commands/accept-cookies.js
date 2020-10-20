Cypress.Commands.add('acceptCookies', () => {
    cy.get(".cookielaw-banner .btn-primary").click();
});
