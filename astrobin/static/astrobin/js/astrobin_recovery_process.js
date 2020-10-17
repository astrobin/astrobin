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

        $(".recovery-process .astrobin-image-container.corrupted.recovered").click(function () {
            var $self = $(this);
            
            if ($self.hasClass("recovery-process-recover-selected")) {
                $self.removeClass("recovery-process-recover-selected");
                $self.addClass("recovery-process-delete-selected");
            } else if ($self.hasClass("recovery-process-delete-selected")) {
                if ($self.hasClass("revision")) {
                    $self.removeClass("recovery-process-delete-selected");
                    $self.addClass("recovery-process-recover-selected");
                } else {
                    $self.removeClass("recovery-process-delete-selected");
                }
            } else {
                $self.addClass("recovery-process-recover-selected");
            }
            
            if (!$self.hasClass("revision")) {
                var id = $self.find(".astrobin-image").data("id");
                var $revisions = $(".astrobin-image-container.revision.corrupted.recovered .astrobin-image[data-id=" + id + "]");
                $revisions.each(function(index, $revision) {
                    var $container = $($revision.closest(".astrobin-image-container"));
                    if ($self.hasClass("recovery-process-recover-selected")) {
                        $container.removeClass("recovery-process-delete-selected");
                        $container.addClass("recovery-process-recover-selected");
                    } else if ($self.hasClass("recovery-process-delete-selected")) {
                        $container.removeClass("recovery-process-recover-selected");
                        $container.addClass("recovery-process-delete-selected");
                    } else {
                        $container.removeClass("recovery-process-recover-selected");
                        $container.removeClass("recovery-process-delete-selected");
                    }
                });
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

            var imageRecoverPks = $(".recovery-process-recover-selected:not(.revision)").map(function (index, item) {
                return parseInt($(item).find('.astrobin-image').attr("data-id"), 10);
            }).get();

            var revisionRecoverPks = $(".recovery-process-recover-selected.revision").map(function (index, item) {
                return parseInt($(item).find('.astrobin-image').attr("data-revision-id"), 10);
            }).get();

            var imageDeletePks = $(".recovery-process-delete-selected:not(.revision)").map(function (index, item) {
                return parseInt($(item).find('.astrobin-image').attr("data-id"), 10);
            }).get();

            var revisionDeletePks = $(".recovery-process-delete-selected.revision").map(function (index, item) {
                return parseInt($(item).find('.astrobin-image').attr("data-revision-id"), 10);
            }).get();

            $(this).prop("disabled", "disabled").addClass("running");

            $.ajax({
                url: "/json-api/user/confirm-revision-recovery/",
                type: "POST",
                cache: false,
                timeout: 30000,
                data: JSON.stringify({
                    revisions: revisionRecoverPks
                }),
                dataType: "json",
                success: function () {
                    $.ajax({
                        url: "/json-api/user/delete-revisions/",
                        type: "POST",
                        cache: false,
                        timeout: 30000,
                        data: JSON.stringify({
                            revisions: revisionDeletePks
                        }),
                        dataType: "json",
                        success: function () {
                            $.ajax({
                                url: "/json-api/user/confirm-image-recovery/",
                                type: "POST",
                                cache: false,
                                timeout: 30000,
                                data: JSON.stringify({
                                    images: imageRecoverPks
                                }),
                                dataType: "json",
                                success: function () {
                                    $.ajax({
                                        url: "/json-api/user/delete-images/",
                                        type: "POST",
                                        cache: false,
                                        timeout: 30000,
                                        data: JSON.stringify({
                                            images: imageDeletePks
                                        }),
                                        dataType: "json",
                                        success: function () {
                                            window.location.reload();
                                        }
                                    });
                                }
                            });
                        }
                    });
                }
            });
        });
    });
})();
