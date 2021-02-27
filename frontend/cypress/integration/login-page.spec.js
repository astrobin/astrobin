/// <reference types="cypress" />

context("account-page", () => {
  beforeEach(() => {
    cy.server();
    cy.setupInitializationRoutes();

    cy.route("GET", "**/common/userprofiles/current", []).as("getCurrentUserProfile");

    cy.visitPage("/account/login?redirectUrl=%2F");
  });

  it("should display the form", () => {
    cy.get("h1")
      .contains("Log in")
      .should("exist");
    cy.get("#handle").should("exist");
    cy.get("#password").should("exist");
    cy.get(".buttons-area .btn")
      .contains("Log in")
      .should("exist")
      .should("be.disabled");
    cy.get(".buttons-area .btn")
      .contains("Register")
      .should("exist");
    cy.get(".buttons-area .btn")
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

    cy.get(".buttons-area .btn-primary").click();

    cy.get(".error")
      .contains("We could not log you in. Please check your credentials and try again.")
      .should("exist");
  });

  it("should redirect to front page in case of success", () => {
    cy.get("#handle").type("handle");
    cy.get("#password").type("password");

    cy.login();
    cy.get(".buttons-area .btn-primary").click();

    cy.url().should("equal", "http://localhost:4400/account/logged-in?redirectUrl=%2F");
    cy.wait(3000);
    cy.url().should("equal", "http://localhost:4400/");

    cy.get("#user-dropdown astrobin-username .username")
      .contains("AstroBin Dev")
      .should("exist");

    cy.get("#user-dropdown .scores .astrobin-index").should("contain.text", "1.23");
    cy.get("#user-dropdown .scores .astrobin-index").should("not.contain.text", "1.234");
    cy.get("#user-dropdown .scores .followers").should("contain.text", "123");
  });

  it("should redirect to front page in case of success (account via enter key)", () => {
    cy.login();

    cy.get("#handle").type("handle");
    cy.get("#password").type("password{enter}");

    cy.url().should("equal", "http://localhost:4400/account/logged-in?redirectUrl=%2F");
    cy.wait(3000);
    cy.url().should("equal", "http://localhost:4400/");
  });
});
