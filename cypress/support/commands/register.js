Cypress.Commands.add('register', (opts={}) => {
    cy.visit("/accounts/register/");

    cy.acceptCookies();

    let rand_id = Math.random().toString(36).substring(7);
    let password = "*t8vV2PboXfP";

    cy.get(".form-horizontal input[name='username']").type(opts.username || `astrobin_dev_${rand_id}`);
    cy.get(".form-horizontal input[name='email']").type(opts.email || `dev_${rand_id}@astrobin.com`);
    cy.get(".form-horizontal input[name='password1']").type(opts.password || password);
    cy.get(".form-horizontal input[name='password2']").type(opts.password || password);
    cy.get(".form-horizontal select[name='skill_level']+.select2 .select2-selection__arrow").click();
    cy.get(".select2-results__option:nth-child(2)").click();
    cy.get("#uniform-id_tos").click();

    cy.bypassCaptcha();
    cy.wait(1500);

    cy.get(".form-horizontal .btn[type='submit']").click();

    cy.url().should("contain", "/accounts/register/complete/");
});
