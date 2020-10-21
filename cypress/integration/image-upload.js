describe("Image upload", () => {
    before(() => {
        cy.clearCookies();
        cy.login();
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("sessionid", "csrftoken", "astrobin_lang", "cookielaw_accepted");
    });

    it("should upload an image using the classic uploader", () => {
        cy.imageUpload("test.jpg");
    });
});
