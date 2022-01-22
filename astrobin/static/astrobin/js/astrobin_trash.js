(function () {
    $(document).ready(function () {
        const $restoreButton = $("#restore-from-trash");
        const $emptyButton = $("#empty-trash");
        const $restoreNumber = $("#restore-from-trash-number");

        $(".trash-thumbnail").click(function (e) {
            e.preventDefault();

            const restore = $(this).attr("data-restore");

            $(this).find(".restore-thumbnail-overlay").css({
                visibility: restore === "true" ? "hidden" : "visible"
            });

            $(this).attr("data-restore", restore === "true" ? "false" : "true");

            const number = $("[data-restore=true]").length;

            $restoreNumber.text(number);
            if (number === 0) {
                $restoreButton.attr("disabled", "disabled");
            } else {
                $restoreButton.removeAttr("disabled");
            }
        });

        $restoreButton.click(function (e) {
            e.preventDefault();

            const pks = $("[data-restore=true]").map(function (index, item) {
                return parseInt($(item).attr("data-pk"), 10);
            }).get();

            $restoreButton.attr("disabled", "disabled");
            $restoreButton.addClass("running");

            $.ajax({
                url: "/json-api/user/restore-deleted-images/",
                type: "POST",
                cache: false,
                timeout: 30000,
                data: JSON.stringify({
                    images: pks
                }),
                dataType: "json",
                success: function() {
                    window.location.reload();
                }
            });
        });

        $emptyButton.click(function (e) {
            e.preventDefault();

            const $confirmationModal = $("#this-operation-cannot-be-undone-modal");
            $confirmationModal.modal("show");

            const $continueButton = $confirmationModal.find(".btn-continue");

            $continueButton.click(function (e2) {
                e2.preventDefault();

                $continueButton.attr("disabled", "disabled");
                $continueButton.addClass("running");

                $.ajax({
                    url: "/json-api/user/empty-trash/",
                    type: "POST",
                    cache: false,
                    timeout: 30000,
                    success: function () {
                        window.location.reload();
                    }
                });
            });
        })
    });
})();
