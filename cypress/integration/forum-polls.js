describe("Forums", () => {
    before(() => {
        cy.login({next: "/forum/"});
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("sessionid", "csrftoken", "astrobin_lang", "cookielaw_accepted");
    });


    it("should post", () => {
        cy.visit("/forum/c/astrobin/announcements/");
        cy.get("a").contains("New topic").click();
        cy.url().should("contain", "/topic/add/");

        cy.get('#i-have-read').click();
        cy.get('#forum-usage-modal .btn-primary').click();

        // Give the editor 10 seconds to appear
        cy.get(".post-form input[name='name']", {timeout: 10000}).should('be.visible');

        cy.get(".post-form input[name='name']").type("Test topic");
        cy.get("#cke_id_body .cke_wysiwyg_div").type("Hello, this is a test topic.");

        cy.get(".poll-edit-container .select2").click();
        cy.get(".select2-results__option").contains("Single answer").click();
        cy.get("#id_poll_question").type("This is a poll question");
        cy.get("[name='poll_answers-0-text']").type("First answer");
        cy.get("[name='poll_answers-1-text']").type("Second answer");
        cy.get(".add-row").click();
        cy.get("[name='poll_answers-2-text']").type("Third answer");


        cy.get(".post-form button[type='submit']").click();

        cy.url().should("contain", "/forum/c/astrobin/announcements/test-topic");
        cy.get(".topic h1").contains("Test topic").should("exist");
        cy.get(".post-content").contains("Hello, this is a test topic.").should("exist");
        cy.get(".poll-question > th").contains("This is a poll question").should("exist");
        cy.get("[for='id_answers_0']").contains("First answer").should("exist");
        cy.get("[for='id_answers_1']").contains("Second answer").should("exist");
        cy.get("[for='id_answers_2']").contains("Third answer").should("exist");
    });

    it("should vote", () => {
        cy.get("[for='id_answers_0']").contains("First answer").click();
        cy.get(".poll-form .btn").contains("Submit").click();

        cy.url().should("contain", "/forum/c/astrobin/announcements/test-topic");

        cy.get(".poll-answer td").contains("First answer").should("exist");
        cy.get(".poll-answer td").contains("1 (100.00 %)").should("exist");
        cy.get(".poll-answer td").contains("Second answer").should("exist");
        cy.get(".poll-answer td").contains("Third answer").should("exist");
    });

    it("should cancel vote", () => {
        cy.get(".btn").contains("Cancel my poll vote").click();

        cy.url().should("contain", "/forum/c/astrobin/announcements/test-topic");

        cy.get("[for='id_answers_0']").contains("First answer").should("exist");
        cy.get("[for='id_answers_1']").contains("Second answer").should("exist");
        cy.get("[for='id_answers_2']").contains("Third answer").should("exist");
    });
});
