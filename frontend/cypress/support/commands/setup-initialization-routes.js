Cypress.Commands.add("setupInitializationRoutes", () => {
  // These routes are necessary to every page, since they are used by the app loading service or common components such
  // as the header or footer.
  cy.setupAppRoutes();
  cy.setupAuthRoutes();
  cy.setupSubscriptionRoutes();
  cy.setupNotificationRoutes();
});
