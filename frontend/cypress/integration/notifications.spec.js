/// <reference types="cypress" />

context("notifications", () => {
  describe("when logged out", () => {
    it("should redirect to the login page", () => {
      cy.server();
      cy.setupInitializationRoutes();
      cy.route("GET", "**/common/userprofiles/current", []).as("getCurrentUserProfile");

      cy.visitPage("/notifications");
      cy.url().should("contain", "/account/login?redirectUrl=%2Fnotifications");
    });
  });

  describe("when logged in", () => {
    beforeEach(() => {
      cy.server();
      cy.setupInitializationRoutes();
    });

    describe("when there are no notifications", () => {
      beforeEach(() => {
        cy.login();
        cy.visitPage("/notifications");
        cy.wait("@getUnreadNotificationsCount");
      });

      it("should have the correct setup", () => {
        cy.get(".page > h1").should("contain", "Notifications");
        cy.get("astrobin-empty-list").should("be.visible");
        cy.get("#mark-all-as-read").should("be.disabled");
      });
    });

    describe("when there is a notification", () => {
      beforeEach(() => {
        cy.route("GET", "**/notifications/notification/?page=*", "fixture:api/notifications/notification_one.json").as(
          "getNotificationOne"
        );

        cy.route("GET", "**/notifications/notification/get_unread_count", "1").as("getUnreadNotificationsCount");

        cy.login();
        cy.visitPage("/notifications");
        cy.wait("@getUnreadNotificationsCount");
      });

      it("should have the correct setup", () => {
        cy.get("astrobin-empty-list").should("not.be.visible");
        cy.get("#mark-all-as-read").should("not.be.disabled");
        cy.get("ngb-pagination")
          .its("length")
          .should("equal", 2);
        cy.get("#unread-notifications-count").should("contain.text", 1);
        cy.get(".navbar .notifications-list-item .badge").should("contain.text", 1);
      });

      it("should fetch count again when marking a notification as read", () => {
        cy.route("GET", "**/notifications/notification/get_unread_count", "0");

        cy.get("#notification-1 .read-icon").click();
        cy.get("#unread-notifications-count").should("not.exist");
        cy.get(".navbar .notifications-list-item .badge").should("not.exist");
        cy.get("#mark-all-as-read").should("be.disabled");
      });

      it("should fetch count again when marking all as read", () => {
        cy.route("GET", "**/notifications/notification/get_unread_count", "0");

        cy.get("#mark-all-as-read").click();

        cy.get("#unread-notifications-count").should("not.exist");
        cy.get(".navbar .notifications-list-item .badge").should("not.exist");
        cy.get("#mark-all-as-read").should("be.disabled");
      });

      it("should show the loading stripes when marking as read is slow", () => {
        cy.route("GET", "**/notifications/notification/get_unread_count", "0");

        cy.route({
          method: "POST",
          url: "**/notifications/notification/mark_all_as_read",
          response: {},
          delay: 1000
        }).as("markAllNotificationsAsReadSlow");

        cy.get("#mark-all-as-read").click();

        cy.get(".global-loading-indicator.loading").should("exist");

        cy.wait(1000);

        cy.get(".global-loading-indicator.loading").should("not.exist");
      });
    });
  });
});
