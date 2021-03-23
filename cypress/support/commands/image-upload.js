Cypress.Commands.add("imageEditThumbnails", (options = {}) => {
    cy.url().should("contain", "edit/thumbnails");
    cy.get(".form-actions [type='submit']").click();
});

Cypress.Commands.add("imageEditWatermark", (options = {}) => {
    cy.url().should("contain", "edit/watermark");
    cy.get(".form-actions [type='submit']").click();
});

Cypress.Commands.add("imageEditBasic", (options = {}) => {
    const title = options.title || "Test image upload";
    const dataSource = options.dataSource || "Backyard";
    const subjectType = options.subjectType || "Other";

    cy.url().should("contain", "edit/basic");
    cy.get("input[name='title']").type(title);
    cy.select2("select[name='data_source']", dataSource);
    cy.select2("select[name='subject_type']", subjectType);
    cy.get(".form-actions [type='submit'][name='submit_save']").click();

    cy.get("h3.image-title").contains(title).should("exist");
});

Cypress.Commands.add("imageUpload", (fixture, options = {}) => {
    cy.visit("/upload/?forceClassicUploader");

    cy.get(".final-form-box input[type='file']")
        .then(function ($input) {
            cy.fixture(fixture, 'base64')
                .then(Cypress.Blob.base64StringToBlob)
                .then(blob => {
                    const el = $input[0];
                    const testFile = new File([blob], fixture, {
                        type: "image/jpeg",
                    });
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(testFile);
                    el.files = dataTransfer.files;
                });
        });

    cy.get(".final-form-box input[type='submit']").click();

    cy.imageEditThumbnails(options);
    cy.imageEditWatermark(options);
    cy.imageEditBasic(options);
});

Cypress.Commands.add("ngPrepareImageUpload", (fixture, options = {}) => {
    cy.get("#title").type(options.title || "Test title");
    cy.get("input#image_file")
        .then(function ($input) {
            cy.fixture(fixture, 'base64')
                .then(Cypress.Blob.base64StringToBlob)
                .then(blob => {
                    const el = $input[0];
                    const testFile = new File([blob], fixture, {
                        type: "image/jpeg",
                    });
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(testFile);
                    el.files = dataTransfer.files;

                    const event = document.createEvent("UIEvents");
                    event.initUIEvent("change", true, true);
                    el.dispatchEvent(event);
                });
        });
});
