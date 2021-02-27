/// <reference types="cypress" />

context("premium", () => {
  describe("when logged out", () => {
    it("should redirect to the login page", () => {
      cy.server();
      cy.setupInitializationRoutes();
      cy.route("GET", "**/common/userprofiles/current", []).as("getCurrentUserProfile");
      cy.visitPage("/subscriptions/premium");
      cy.url().should("contain", "/account/login?redirectUrl=%2Fsubscriptions%2Fpremium");
    });
  });

  describe("when logged in", () => {
    beforeEach(() => {
      cy.server();
      cy.setupInitializationRoutes();

      cy.route("GET", "**/payments/pricing/premium/USD/", {
        discount: 0,
        price: 20,
        fullPrice: 20
      }).as("pricing");
      cy.route("GET", "**/images/image/?user=1", {}).as("userImages");

      cy.login();
    });

    it("should show correct header", () => {
      cy.visitPage("/subscriptions/premium");
      cy.get("h1 > span")
        .contains("Premium")
        .should("exist");
    });

    it("should allow purchase if the user is on Lite", () => {
      cy.route("GET", "**/common/usersubscriptions/?user=*", "fixture:api/common/usersubscriptions_1_lite.json").as(
        "getUserSubscriptions"
      );
      cy.visitPage("/subscriptions/premium");
      cy.get(".already-subscribed.alert").should("not.exist");
      cy.get(".already-subscribed-higher.alert").should("not.exist");
      cy.get(".buy.btn").should("exist");
    });

    it("should allow purchase if the user is on Premium", () => {
      cy.route("GET", "**/common/usersubscriptions/?user=*", "fixture:api/common/usersubscriptions_1_premium.json").as(
        "getUserSubscriptions"
      );
      cy.visitPage("/subscriptions/premium");
      cy.get(".already-subscribed.alert").should("exist");
      cy.get(".already-subscribed-higher.alert").should("not.exist");
      cy.get(".buy.btn").should("exist");
    });

    it("should not allow purchase if the user is on Ultimate", () => {
      cy.route("GET", "**/common/usersubscriptions/?user=*", "fixture:api/common/usersubscriptions_1_ultimate.json").as(
        "getUserSubscriptions"
      );
      cy.visitPage("/subscriptions/premium");
      cy.get(".already-subscribed.alert").should("not.exist");
      cy.get(".already-subscribed-higher.alert").should("exist");
      cy.get(".buy.btn").should("not.exist");
    });

    it("should allow purchase if the user is not already subscribed", () => {
      cy.route("GET", "**/common/usersubscriptions/?user=*", []).as("getUserSubscriptions");
      cy.visitPage("/subscriptions/premium");
      cy.get(".already-subscribed.alert").should("not.exist");
      cy.get(".already-subscribed-higher.alert").should("not.exist");
      cy.get(".price").should("contain", "$20.00");
      cy.get(".buy.btn").should("exist");
    });

    it("should not show warning about 50 images if use has more than 25 images", () => {
      cy.route("GET", "**/common/usersubscriptions/?user=*", []).as("getUserSubscriptions");
      cy.route("GET", "**/images/image/?user=1", { count: 50 }).as("userImages");
      cy.visitPage("/subscriptions/premium");
      cy.get(".lite-limit.alert").should("not.exist");
    });
  });
});
