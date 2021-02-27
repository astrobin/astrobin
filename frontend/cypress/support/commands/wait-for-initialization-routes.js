Cypress.Commands.add("waitForInitializationRoutes", () => {
  cy.wait("@appConfig");
  cy.wait("@i18n");
  cy.wait("@getSubscriptions");
});
