Cypress.Commands.add('acceptCookies', () => {
    cy.get("body").then((body) => {
        if (body.find(".cookielaw-banner").length > 0) {
            cy.get(".cookielaw-banner .btn-primary").click();
        }
    });
});
