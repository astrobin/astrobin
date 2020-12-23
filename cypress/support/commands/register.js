Cypress.Commands.add('register', (opts={}) => {
    cy.visit("/accounts/register/");

    cy.acceptCookies();

    cy.get(".form-horizontal input[name='username']").type(opts.username || "astrobin_dev1");
    cy.get(".form-horizontal input[name='email']").type(opts.email || "dev1@astrobin.com");
    cy.get(".form-horizontal input[name='password1']").type(opts.password || "astrobin_dev1");
    cy.get(".form-horizontal input[name='password2']").type(opts.password || "astrobin_dev1");
    cy.get("#uniform-id_tos").click();

    cy.bypassReCAPTCHA();
    cy.wait(1500);
    
    cy.get(".form-horizontal button").click();

    cy.url().should("contain", "/accounts/register/complete/");
});
