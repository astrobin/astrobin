Cypress.Commands.add("select2", (selector, option) => {
    cy.get(selector).attribute("data-select2-id").then(id => {
        cy.get(selector).siblings(".select2").click();
        cy.get("#select2-" + id + "-results .select2-results__option").contains(option).click();
    });
});
