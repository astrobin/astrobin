Cypress.Commands.add('login', (username, password) => {
    cy.visit("/accounts/login/?next=/me/");

    cy.acceptCookies();

    cy.get(".login-form input[name='username']").type(username);
    cy.get(".login-form input[name='password']").type(password);
    cy.get(".login-form input[type='submit']").click();

    cy.url().should("contain", "/users/" + username + "/");

    cy.get("body").then((body) => {
        if (body.find("#realname-prompt").length > 0) {
            cy.get("#realname-prompt input[type='submit']").click();
        }
    });
});
