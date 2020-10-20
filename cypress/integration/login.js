describe("Login", () => {
    it("should login", () => {
        cy.login("astrobin_dev", "astrobin_dev");
    });
});
