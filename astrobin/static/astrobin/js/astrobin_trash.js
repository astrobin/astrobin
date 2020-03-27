(function () {
    $(document).ready(function () {
        var $restoreButton = $("#restore-from-trash");
        var $restoreNumber = $("#restore-from-trash-number");
        var $loadingIndicator = $("#restore-from-trash + .loading");

        $(".trash-thumbnail").click(function (e) {
            e.preventDefault();

            var restore = $(this).attr("data-restore");

            $(this).find(".restore-thumbnail-overlay").css({
                visibility: restore === "true" ? "hidden" : "visible"
            });

            $(this).attr("data-restore", restore === "true" ? "false" : "true");

            var number = $("[data-restore=true]").length;

            $restoreNumber.text(number);
            if (number === 0) {
                $restoreButton.attr("disabled", "disabled");
            } else {
                $restoreButton.removeAttr("disabled");
            }
        });

        $restoreButton.click(function (e) {
            e.preventDefault();

            var pks = $("[data-restore=true]").map(function (index, item) {
                return parseInt($(item).attr("data-pk"), 10);
            }).get();

            $restoreButton.attr("disabled", "disabled");
            $loadingIndicator.show();

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
    });
})();
