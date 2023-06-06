describe("Login", () => {
    before(() => {
        cy.clearCookies();
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("sessionid", "csrftoken", "astrobin_lang", "astrobin_cookie_consent");
    });

    it("should login", () => {
        cy.login();
    });
});
