/// <reference types="cypress" />

import { Constants } from "../../src/app/shared/constants";

context("uploader", () => {
  describe("when logged out", () => {
    it("should redirect to the login page", () => {
      cy.server();
      cy.setupInitializationRoutes();
      cy.route("GET", "**/common/userprofiles/current", []).as("getCurrentUserProfile");

      cy.visitPage("/uploader");
      cy.url().should("contain", "/account/login?redirectUrl=%2Fuploader");
    });
  });

  describe("when logged in", () => {
    beforeEach(() => {
      cy.server();
      cy.setupInitializationRoutes();
    });

    describe("when the website is in read-only mode", () => {
      beforeEach(() => {
        cy.login();
        cy.route("GET", "**/json-api/common/app-config/", "fixture:api/json/app-config-read-only.json").as("appConfig");
        cy.visitPage("/uploader");
      });

      it("should show the read-only mode alert", () => {
        cy.get("astrobin-read-only-mode").should("exist");
      });
    });

    describe("when the website is not in read-only mode", () => {
      beforeEach(() => {
        cy.login();
      });

      it("should not show the read-only mode alert", () => {
        cy.visitPage("/uploader");

        cy.get("astrobin-read-only-mode").should("not.exist");
      });

      it("should have all form controls", () => {
        cy.visitPage("/uploader");

        cy.get("#title").should("exist");
        cy.get("#image_file").should("exist");
        cy.get(".accepted-formats").should("contain.text", Constants.ALLOWED_UPLOAD_EXTENSIONS.join(","));
      });

      it("should display error if title is missing and Upload is clicked", () => {
        cy.visitPage("/uploader");

        cy.get("button")
          .contains("Upload")
          .click();

        cy.get(".form-group.has-error label[for='title']").should("exist");
      });

      it("should have all form controls if user is Premium", () => {
        cy.login();

        cy.route(
          "GET",
          "**/common/usersubscriptions/?user=*",
          "fixture:api/common/usersubscriptions_2_premium.json"
        ).as("getUserSubscriptions");

        cy.route("GET", "**/common/users/*", "fixture:api/common/users_2.json").as("getUser");

        cy.visitPage("/uploader");

        cy.get("#title").should("exist");
        cy.get("#image_file").should("exist");
        cy.get(".accepted-formats").should("contain.text", Constants.ALLOWED_UPLOAD_EXTENSIONS.join(","));
      });

      it("should have all form controls if user is Premium (autorenew)", () => {
        cy.login();

        cy.route(
          "GET",
          "**/common/usersubscriptions/?user=*",
          "fixture:api/common/usersubscriptions_2_premium_autorenew.json"
        ).as("getUserSubscriptions");

        cy.route("GET", "**/common/users/*", "fixture:api/common/users_2.json").as("getUser");

        cy.visitPage("/uploader");

        cy.get("#title").should("exist");
        cy.get("#image_file").should("exist");
        cy.get(".accepted-formats").should("contain.text", Constants.ALLOWED_UPLOAD_EXTENSIONS.join(","));
      });

      it("should have all form controls if user is Premium 2020", () => {
        cy.login();

        cy.route(
          "GET",
          "**/common/usersubscriptions/?user=*",
          "fixture:api/common/usersubscriptions_2_premium_2020.json"
        ).as("getUserSubscriptions");

        cy.route("GET", "**/common/users/*", "fixture:api/common/users_2.json").as("getUser");

        cy.visitPage("/uploader");

        cy.get("#title").should("exist");
        cy.get("#image_file").should("exist");
        cy.get(".accepted-formats").should("contain.text", Constants.ALLOWED_UPLOAD_EXTENSIONS.join(","));
      });

      it("should have all form controls if user is Free", () => {
        cy.login();

        cy.route("GET", "**/common/usersubscriptions/?user=*", "fixture:api/common/usersubscriptions_2_free.json").as(
          "getUserSubscriptions"
        );

        cy.route("GET", "**/common/users/*", "fixture:api/common/users_2.json").as("getUser");

        cy.visitPage("/uploader");

        cy.get("#title").should("exist");
        cy.get("#image_file").should("exist");
        cy.get(".accepted-formats").should("contain.text", Constants.ALLOWED_UPLOAD_EXTENSIONS.join(","));
      });
    });
  });
});
