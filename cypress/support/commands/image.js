Cypress.Commands.add("visitImage", (options = {}) => {
    cy.visit("/users/astrobin_dev/");
    cy.get(".astrobin-image-container a").first().click();
    cy.get(".main-image").should("be.visible");
});

Cypress.Commands.add("likeImage", (options = {}) => {
    cy.url().then(url => {
        cy.login({
            next: url,
            username: "astrobin_dev2",
            password: "astrobin_dev2"
        });
    
        let btn = cy.get(".property-like");
    
        btn.click();
        btn.should("contain", "Unlike");
    
        btn.click();
        btn.should("contain", "Like");
    });
});

Cypress.Commands.add("comment", (options = {}) => {
    cy.get(".uncollapse").click();
    cy.get(".cke_wysiwyg_div").first().type("hello world");
    cy.get(".ember-view button").click();
    cy.get(".comment-container").should("be.visible");
});
