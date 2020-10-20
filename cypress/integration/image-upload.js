describe("Image upload", () => {
    it("should upload an image using the classic uploader", () => {
        cy.imageUpload("test.jpg");
    });
});
