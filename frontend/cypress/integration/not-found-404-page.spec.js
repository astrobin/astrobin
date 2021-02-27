/// <reference types="cypress" />

context("not-found-404", () => {
  it("should navigate to the 404 page", () => {
    cy.server();
    cy.setupInitializationRoutes();

    cy.visitPage("/this-does-not-exist");

    cy.get("h1")
      .contains("404")
      .should("exist");
  });
});
