/// <reference types="cypress" />

context("logged-out-page", () => {
  beforeEach(() => {
    cy.server();
    cy.setupInitializationRoutes();
    cy.login();
    cy.visitPage("/notifications");
  });

  it("should redirect to the logged out page", () => {
    cy.get("#user-dropdown").click();
    cy.get(".navbar .dropdown-item")
      .contains("Logout")
      .click();
    cy.url().should("equal", "http://localhost:4400/account/logged-out");
  });
});
