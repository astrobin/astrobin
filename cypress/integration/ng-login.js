describe("Login", () => {
    before(() => {
        cy.clearCookies();
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("sessionid", "csrftoken", "astrobin_lang", "cookielaw_accepted",
            "classic-auth-token");
    });

    it("should login", () => {
        cy.ngLogin();
    });
});
