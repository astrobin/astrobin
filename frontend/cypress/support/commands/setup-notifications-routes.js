Cypress.Commands.add("setupNotificationRoutes", () => {
  cy.route("GET", "**/notifications/notification/?page=*", "fixture:api/notifications/notification_none.json").as(
    "getNotificationsNone"
  );

  cy.route("PUT", "**/notifications/notification/*", {}).as("putNotification");

  cy.route("GET", "**/notifications/notification/get_unread_count", "0").as("getUnreadNotificationsCount");

  cy.route("POST", "**/notifications/notification/mark_all_as_read", {}).as("markAllNotificationsAsRead");
});
