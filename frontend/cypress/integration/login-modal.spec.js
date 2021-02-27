/// <reference types="cypress" />

context("account-modal", () => {
  beforeEach(() => {
    cy.server();
    cy.setupInitializationRoutes();

    cy.route("GET", "**/common/userprofiles/current", []).as("getCurrentUserProfile");

    cy.visitPage("/");

    cy.get(".navbar #login-button").click();
  });

  it("should display the form", () => {
    cy.get(".modal-title")
      .contains("Log in")
      .should("exist");
    cy.get("#handle").should("exist");
    cy.get("#password").should("exist");
    cy.get(".modal-footer .btn")
      .contains("Log in")
      .should("exist")
      .should("be.disabled");
    cy.get(".modal-footer .btn")
      .contains("Register")
      .should("exist");
    cy.get(".modal-footer .btn")
      .contains("Reset password")
      .should("exist");
  });

  it("should display error in case of wrong credentials", () => {
    cy.get("#handle").type("wrong");
    cy.get("#password").type("wrong");

    cy.route({
      method: "POST",
      url: "**/api-auth-token",
      status: 400,
      response: ""
    }).as("getApiToken");

    cy.get(".modal-footer .btn-primary").click();

    cy.get(".error")
      .contains("We could not log you in. Please check your credentials and try again.")
      .should("exist");
  });

  it("should redirect to front page in case of success", () => {
    cy.get("#handle").type("handle");
    cy.get("#password").type("password");

    cy.login();
    cy.get(".modal-footer .btn-primary").click();

    cy.url().should("equal", "http://localhost:4400/");

    cy.get("#user-dropdown").should("exist");
  });

  it("should redirect to front page in case of success (account via enter key)", () => {
    cy.login();

    cy.get("#handle").type("handle");
    cy.get("#password").type("password{enter}");

    cy.url().should("equal", "http://localhost:4400/");

    cy.get("#user-dropdown").should("exist");
  });
});
