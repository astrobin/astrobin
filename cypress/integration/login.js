describe("Login", () => {
    it("should display the page", () => {
        cy.visit("/accounts/login/");
        cy.get("input[name='username']").should("exist");
        cy.get("input[name='password']").should("exist");
    });
});
