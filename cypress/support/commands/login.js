Cypress.Commands.add('login', (opts={}) => {
    cy.visit("/accounts/login/?next=" + (opts.next || "/me/"));

    cy.acceptCookies();

    cy.get(".login-form input[name='username']").type(opts.username || "astrobin_dev");
    cy.get(".login-form input[name='password']").type(opts.password || "astrobin_dev");
    cy.get(".login-form input[type='submit']").click();

    cy.url().should(
        "contain",
        (!opts.next || opts.next === "/me/") ? "/users/" + (opts.username || "astrobin_dev" + "/") : opts.next
    );

    cy.get("body").then((body) => {
        if (body.find("#realname-prompt").length > 0) {
            cy.get("#realname-prompt input[type='submit']").click();
        }
    });
});

Cypress.Commands.add('ngLogin', (opts={}) => {
    cy.visit("http://localhost:4400/account/login/?redirectUrl=%2Fuploader");

    cy.acceptCookies();

    cy.get("#login-form #handle").type(opts.username || "astrobin_dev");
    cy.get("#login-form #password").type(opts.password || "astrobin_dev");
    cy.get(".buttons-area .btn").contains("Log in").click();

    cy.url().should("contain", "logged-in");
});
