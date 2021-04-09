Cypress.Commands.add("visitImage", (options = {}) => {
    cy.visit("/users/astrobin_dev/");
    cy.get(".astrobin-image-container a").first().click();
    cy.get(".main-image").should("be.visible");
});

Cypress.Commands.add("likeImage", (options = {}) => {
    let btn = cy.get(".property-like").first();

    btn.click();
    btn.should("contain", "Unlike");
});

Cypress.Commands.add("unlikeImage", (options = {}) => {
    let btn = cy.get(".property-like").first();

    btn.click();
    btn.should("contain", "Like");
});

Cypress.Commands.add("comment", (options = {}) => {
    cy.get(".comment .uncollapse").click();
    cy.get(".cke_contents .cke_wysiwyg_div").first().type("hello world");
    cy.get(".ember-view button").click();
    cy.get(".comment .comment-container").should("be.visible");
});
