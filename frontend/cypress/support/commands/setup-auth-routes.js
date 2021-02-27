Cypress.Commands.add("setupAuthRoutes", () => {
  cy.route("POST", "**/api-auth-token", { token: "1234567890" }).as("getApiToken");

  cy.route("GET", "**/common/userprofiles/current", "fixture:api/common/userprofile_current_1.json").as(
    "getCurrentUserProfile"
  );

  cy.route("GET", "**/common/users/*", "fixture:api/common/users_1.json").as("getUser");
});
