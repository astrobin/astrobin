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

        cy.get('#i-have-read').click();
        cy.get('#forum-usage-modal .btn-primary').click();

        cy.get(".post-form input[name='name']").should('be.visible');

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

        cy.get(".post-form input[name='name']").should('be.visible');

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
        cy.get("#cke_id_body .cke_wysiwyg_div").should("be.visible");
        cy.get(".post-related").last().contains("quote").click();
        cy.wait(1000);
        cy.get(".cke_button__sourcedialog").click();
        cy.get("textarea.cke_source")
            .should("contain.value", "[quote=\"astrobin_dev\"]This is a reply.[/quote]");
        cy.get(".cke_dialog_ui_button_cancel").click();
        cy.get(".post-form button[type='submit']").click();
        cy.get(".post blockquote a[href='/users/astrobin_dev/']").should("exist");
    });

    // Skip temporarily because too flaky.
    it.skip("should quote with non-ASCII characters", () => {
        cy.get(".post-related").last().contains("quote").click();
        cy.wait(1000);
        cy.get("#cke_id_body .cke_wysiwyg_div").type("你好");
        cy.get(".post-form button[type='submit']").click();
        cy.get(".post").contains("你好").should("exist");
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
        cy.get(".cke_button__smiley").click();
        cy.get(".cke_dark_background a").first().click();
        cy.get("#cke_id_body .cke_wysiwyg_div").find(".smiley").should("be.visible");
    });

    it("should insert bold", () => {
        cy.get(".cke_button__bold").click();
        cy.get("#cke_id_body .cke_wysiwyg_div strong");
    });

    it("should insert italic", () => {
        cy.get(".cke_button__italic").click();
        cy.get("#cke_id_body .cke_wysiwyg_div em");
    });

    it("should insert link", () => {
        cy.get(".cke_button__simplelink").click();
        cy.get(".cke_dialog_ui_input_text input").first().type("https://astrobin.com");
        cy.get(".cke_dialog_ui_input_text input").last().type("Astrobin");
        cy.get(".cke_dialog_ui_button_ok").click();
        cy.get("#cke_id_body .cke_wysiwyg_div a").should("contain", "Astrobin");
    });

    it("should not show 'new posts below' break and notification for the first post", () => {
        cy.clearCookies();
        cy.login({username: "astrobin_dev2", password: "astrobin_dev2", next: "/forum/c/astrobin/announcements/"});

        cy.get("a").contains("New topic").click();
        cy.url().should("contain", "/topic/add/");

        cy.get('#i-have-read').click();
        cy.get('#forum-usage-modal .btn-primary').click();

        cy.get(".post-form input[name='name']").should('be.visible');

        cy.get(".post-form input[name='name']").type("Test topic");
        cy.get("#cke_id_body .cke_wysiwyg_div").type("Hello, this is a test topic.");
        cy.get(".post-form button[type='submit']").click();

        cy.clearCookies();
        cy.login({username: "astrobin_dev", password: "astrobin_dev", next: "/forum/c/astrobin/announcements/"});
        cy.get(".topic-list tr:first-child .topic-name a").first().click();

        cy.get(".unread-marker").should("not.exist");
        cy.get(".jq-toast").should("not.exist");
    });

    it("should show 'new posts below' break and notification", () => {
        cy.clearCookies();
        cy.login({username: "astrobin_dev2", password: "astrobin_dev2", next: "/forum/c/astrobin/announcements/"});

        cy.get(".topic-list tr:first-child .topic-name a").first().click();
        cy.get("#cke_id_body .cke_wysiwyg_div").type("This is a reply.");
        cy.get(".post-form button[type='submit']").click();

        cy.clearCookies();
        cy.login({username: "astrobin_dev", password: "astrobin_dev", next: "/forum/c/astrobin/announcements/"});
        cy.get(".topic-list tr:first-child .topic-name a").first().click();

        cy.get(".unread-marker").should("exist");
        cy.get(".jq-toast-heading").contains("You have unread posts in this topic.").should("exist");
    });

    it("should not show 'new posts below' break and notification when visiting again", () => {
        cy.visit("/forum/c/astrobin/announcements/");

        cy.get(".topic-list tr:first-child .topic-name a").first().click();

        cy.get(".unread-marker").should("not.exist");
        cy.get(".jq-toast").should("not.exist");
    });

    it("should not show the notification but only the marker if clicking on the 'first-unread' link", () => {
        cy.clearCookies();
        cy.login({username: "astrobin_dev2", password: "astrobin_dev2", next: "/forum/c/astrobin/announcements/"});

        cy.get(".topic-list tr:first-child .topic-name a").first().click();
        cy.get("#cke_id_body .cke_wysiwyg_div").type("This is a reply.");
        cy.get(".post-form button[type='submit']").click();

        cy.clearCookies();
        cy.login({username: "astrobin_dev", password: "astrobin_dev", next: "/forum/c/astrobin/announcements/"});
        cy.get(".topic-list tr:first-child .topic-name .first-unread-post-link").click();

        cy.get(".unread-marker").should("exist");
        cy.get(".jq-toast").should("not.exist");
    });

    it("the page should display fine for anonymous users", () => {
        cy.clearCookies();

        cy.visit("/forum/c/astrobin/announcements/");
        cy.get(".topic-list tr:first-child .topic-name a").first().click();
        cy.get("h1").contains("Test topic").should("exist");
        cy.get(".unread-marker").should("not.exist");
        cy.get(".jq-toast").should("not.exist");
    });
});
