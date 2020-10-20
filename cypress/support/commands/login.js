Cypress.Commands.add('login', (opts={}) => {
    cy.login({next: "/forum/"});

    cy.visit("/accounts/login/?next=" + opts.next || "/me/");

    cy.acceptCookies();

    cy.get(".login-form input[name='username']").type(opts.username || "astrobin_dev");
    cy.get(".login-form input[name='password']").type(opts.password || "astrobin_dev");
    cy.get(".login-form input[type='submit']").click();

    cy.url().should("contain", opts.next === "/me/" ? "/users/" + (opts.username || "astrobin_dev" + "/") : opts.next);

    cy.get("body").then((body) => {
        if (body.find("#realname-prompt").length > 0) {
            cy.get("#realname-prompt input[type='submit']").click();
        }
    });
});
