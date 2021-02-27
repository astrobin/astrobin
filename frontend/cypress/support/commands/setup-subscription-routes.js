Cypress.Commands.add("setupSubscriptionRoutes", () => {
  cy.route("GET", "**/common/subscriptions", "fixture:api/common/subscriptions.json").as("getSubscriptions");
  cy.route("GET", "**/common/usersubscriptions/?user=*", "fixture:api/common/usersubscriptions_1.json").as(
    "getUserSubscriptions"
  );
});
