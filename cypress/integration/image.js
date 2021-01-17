describe("Image features", () => {
    before(() => {
        cy.clearCookies();
        cy.login();
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("sessionid", "csrftoken", "astrobin_lang", "cookielaw_accepted");
    });

    it("should like and unlike an image", () => {
        cy.likeImage();
    });

    it("should comment on an image", () => {
        cy.comment();
    });

    it("should edit a comment", () => {
        cy.editComment();
    });

    it("should delete a comment", () => {
        cy.deleteComment();
    });
});
