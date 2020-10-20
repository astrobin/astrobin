describe("Login", () => {
    it("should upload an image using the classic uploader", () => {
        cy.login("astrobin_dev", "astrobin_dev");
        cy.imageUpload("test.jpg");
    });
});
