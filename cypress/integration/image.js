describe("Image features", () => {
    before(() => {
        cy.clearCookies();
        cy.login({
            username: "astrobin_dev2",
            password: "astrobin_dev2"
        });
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("sessionid", "csrftoken", "astrobin_lang", "cookielaw_accepted");
        cy.visitImage();
    });

    it("should like an image", () => {
        cy.likeImage();
    });

    it("should unlike an image", () => {
        cy.unlikeImage();
    });

    it("should comment on an image", () => {
        cy.comment();
    });
});
