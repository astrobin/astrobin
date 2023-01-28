Cypress.Commands.add('fillInLogin', (opts = {}) => {
    cy.get(".login-form input[name='auth-username']").type(opts.username || "astrobin_dev");
    cy.get(".login-form input[name='auth-password']").type(opts.password || "astrobin_dev");
    cy.get(".login-form button[type='submit']").click();
});

Cypress.Commands.add('login', (opts={}) => {
    cy.visit("/account/login/?next=" + (opts.next || "/me/"));

    cy.acceptCookies();
    cy.fillInLogin(opts);

    cy.wait(2000);

    cy.url().should(
        "contain",
        (!opts.next || opts.next === "/me/") ? "/users/" + (opts.username || "astrobin_dev" + "/") : opts.next
    );

    cy.get("body").then((body) => {
        if (body.find("#realname-prompt").length > 0) {
            cy.get("#realname-prompt .btn[type='submit']").click();
        }
    });
});
