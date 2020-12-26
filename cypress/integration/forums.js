describe("Forums", () => {
    before(() => {
        cy.login({next: "/forum/"});
    });

    beforeEach(() => {
        Cypress.Cookies.preserveOnce("sessionid", "csrftoken", "astrobin_lang", "cookielaw_accepted");
    });

    it("should have default forum", () => {
        cy.get(".forum-name").contains("AstroBin Meta Forums").should("exist");
        cy.get(".forum-name a").contains("Announcements").should("exist");
    });

    it("should post", () => {
        cy.visit("/forum/c/astrobin/announcements/");
        cy.get("a").contains("New topic").click();
        cy.url().should("contain", "/topic/add/");

        cy.get('#forum-usage-modal .btn-primary').click();

        // Give the editor 10 seconds to appear
        cy.get(".post-form input[name='name']", {timeout: 10000}).should('be.visible');

        cy.get(".post-form input[name='name']").type("Test topic");
        cy.get("#cke_id_body .cke_wysiwyg_div").type("Hello, this is a test topic.");
        cy.get(".post-form button[type='submit']").click();

        cy.url().should("contain", "/forum/c/astrobin/announcements/test-topic");
        cy.get(".topic h1").contains("Test topic").should("exist");
        cy.get(".post-content").contains("Hello, this is a test topic.").should("exist");
    });

    it("should edit", () => {
        cy.get(".post-related a").contains("Edit").click();
        cy.url().should("match", /\/forum\/post\/\d+\/edit\//);

        // Give the editor 10 seconds to appear
        cy.get(".post-form input[name='name']", {timeout: 10000}).should('be.visible');

        cy.get(".post-form input[name='name']").clear().type("Edited test topic");
        cy.get("#cke_id_body .cke_wysiwyg_div")
            .clear()
            .type("Hello, this is an edited test topic.");
        cy.get(".post-form button[type='submit']").click();

        cy.url().should("contain", "/forum/c/astrobin/announcements/test-topic");
        cy.get(".topic h1").contains("Edited test topic").should("exist");
        cy.get(".post-content").contains("Hello, this is an edited test topic.").should("exist");
    });

    it("should reply", () => {
        cy.get("#cke_id_body .cke_wysiwyg_div").type("This is a reply.");
        cy.get(".post-form button[type='submit']").click();

        cy.url().should("contain", "/forum/c/astrobin/announcements/test-topic");
        cy.get(".post-content").contains("This is a reply.").should("exist");
    });

    it("should quote", () => {
        cy.get(".post-related").last().contains("quote").click();
        cy.wait(1000);
        cy.get(".cke_button__sourcedialog").click();
        cy.get("textarea.cke_source")
            .should("contain.value", "[quote=\"astrobin_dev\"]This is a reply.[/quote]");
    });

    it("should like", () => {
        cy.login({
            next: "/forum/c/astrobin/announcements/test-topic",
            username: "astrobin_dev2",
            password: "astrobin_dev2"
        });

        let btn = cy.get(".post-related").first().find("button");

        btn.contains("Like").click();
        btn.contains("Unlike").should("be.visible");
    });

    it("should unlike", () => {
        let btn = cy.get(".post-related").first().find("button");

        btn.contains("Unlike").click();
        btn.contains("Like").should("be.visible");
    });

    it("should insert smiley", () => {
        cy.get("#cke_37").click();
        cy.get(".cke_dark_background a").first().click();
        cy.get("#cke_1_contents").find(".smiley").should("be.visible");
    });

    it("should insert bold", () => { 
        cy.get("#cke_22").click();
        cy.get("#cke_id_body .cke_wysiwyg_div strong");
    });


});
