(function () {
    $(document).ready(function () {
        var $submitSelectedButton = $("#recovery-process-submit-button");
        var $selectedNumber = $("#recovery-process-selected-number");

        function updateSelectedNumber() {
            var n = $(".recovery-process-recover-selected").length + $(".recovery-process-delete-selected").length;

            $selectedNumber.text(n);
            if (n === 0) {
                $submitSelectedButton.attr("disabled", "disabled");
            } else {
                $submitSelectedButton.removeAttr("disabled");
            }
        }

        $(".astrobin-image-container.corrupted.recovered").click(function () {
            if ($(this).hasClass("recovery-process-recover-selected")) {
                $(this).removeClass("recovery-process-recover-selected");
                $(this).addClass("recovery-process-delete-selected");
            } else if ($(this).hasClass("recovery-process-delete-selected")) {
                $(this).removeClass("recovery-process-delete-selected");
            } else {
                $(this).addClass("recovery-process-recover-selected");
            }

            updateSelectedNumber();
        });

        $("#recovery-process-recover-all").click(function (e) {
            e.preventDefault();

            $(".astrobin-image-container.corrupted.recovered")
                .removeClass("recovery-process-delete-selected")
                .addClass("recovery-process-recover-selected");

            updateSelectedNumber();
        });

        $("#recovery-process-delete-all").click(function (e) {
            e.preventDefault();

            $(".astrobin-image-container.corrupted.recovered")
                .removeClass("recovery-process-recover-selected")
                .addClass("recovery-process-delete-selected");

            updateSelectedNumber();
        });

        $("#recovery-process-reset").click(function (e) {
            e.preventDefault();

            $(".astrobin-image-container.corrupted.recovered")
                .removeClass("recovery-process-recover-selected")
                .removeClass("recovery-process-delete-selected");

            updateSelectedNumber();
        });

        $submitSelectedButton.click(function (e) {
            e.preventDefault();

            var recoverPks = $(".recovery-process-recover-selected").map(function (index, item) {
                return parseInt($(item).find('.astrobin-image').attr("data-id"), 10);
            }).get();

            var deletePks = $(".recovery-process-delete-selected").map(function (index, item) {
                return parseInt($(item).find('.astrobin-image').attr("data-id"), 10);
            }).get();

            $(this).prop("disabled", "disabled").addClass("running");

            $.ajax({
                url: "/json-api/user/confirm-image-recovery/",
                type: "POST",
                cache: false,
                timeout: 30000,
                data: JSON.stringify({
                    images: recoverPks
                }),
                dataType: "json",
                success: function() {
                    $.ajax({
                        url: "/json-api/user/delete-images/",
                        type: "POST",
                        cache: false,
                        timeout: 30000,
                        data: JSON.stringify({
                            images: deletePks
                        }),
                        dataType: "json",
                        success: function () {
                            window.location.reload();
                        }
                    });
                }
            });
        });
    });
})();
