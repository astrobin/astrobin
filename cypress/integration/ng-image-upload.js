describe("Login", () => {
    before(() => {
        cy.clearCookies();
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("sessionid", "csrftoken", "astrobin_lang", "cookielaw_accepted",
            "classic-auth-token");
    });

    it("should upload an image", () => {
        cy.ngLogin();
        cy.visit("http://localhost:4400/uploader");

        cy.ngPrepareImageUpload("test.jpg");
        cy.get("label.upload-btn .file").should("contain.text", "test.jpg (28.4 KB)");
        cy.get("[type='submit']").click();

        cy.url().should("contain", "login/?next=/edit/thumbnails");

        cy.fillInLogin();

        cy.url().should("contain", "/edit/thumbnails");

        cy.imageEditThumbnails();
        cy.imageEditWatermark();
        cy.imageEditBasic();
    });
});

