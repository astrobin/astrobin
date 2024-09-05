(function (win) {
    const Status = {
        MISSING: 0,
        PENDING: 1,
        FAILED: 2,
        SUCCESS: 3,
        ADVANCED_PENDING: 4,
        ADVANCED_FAILED: 5,
        ADVANCED_SUCCESS: 6
    };

    function Platesolving(config) {
        this.apiURL = "/api/v2/platesolving/solutions/";
        this.i18n = config.i18n;
        this.errorAlreadyShown = false;
        this.previouslyPending = false;
        this.showErrors = config.showErrors || false;

        $.extend(this, config);

        astrobin_common.init_ajax_csrf_token();
    }

    Platesolving.prototype = {
        getStatus: function () {
            const self = this;
            let attempts = 0;
            self._setInfoModalLoading(true);


            $.ajax({
                url: self.apiURL + `?object_id=${self.object_id}&content_type=${self.content_type_id}`,
                cache: false,
                timeout: 5000
            })
            .done(function (response, textStatus, jqXHR) {
                if (!response || response.length === 0) {
                    self.onStatusPending();
                    return;
                }

                const solution = response[0];

                if (solution.error && solution.attempts >= 3) {
                    self.onError(solution.error);
                    return;
                }

                self._setInfoModalLoading(false);
                self._updateInfoModal("status", self._humanizeStatus(solution.status));

                if (solution.created) {
                    self._updateInfoModal(
                        "started",
                        `<abbr 
                            class="timestamp"
                            data-epoch="${Math.floor(new Date(solution.created.split(".")[0] + "Z").getTime())}"
                        >...</abbr>`
                    );
                    astrobin_common.init_timestamps();
                }

                self._updateInfoModal(
                    "astrometry-job",
                    `<a href="http://nova.astrometry.net/status/${solution.submission_id}" target="_blank">${solution.submission_id}</a>`
                );

                self._updateInfoModal("pixinsight-job", solution.pixinsight_serial_number);
                self._updateInfoModal("pixinsight-stage", self._humanizePixInsightStage(solution.pixinsight_stage));

                switch (solution.status) {
                    case Status.MISSING:
                        self.onStatusMissing(solution.attempts);
                        break;
                    case Status.PENDING:
                        self.onStatusPending();
                        break;
                    case Status.FAILED:
                        self.onStatusFailed(solution.attempts);
                        break;
                    case Status.SUCCESS:
                        self.onStatusSuccess();
                        break;
                    case Status.ADVANCED_PENDING:
                        self.onStatusAdvancedPending(solution.pixinsight_queue_size, solution.pixinsight_stage);
                        break;
                    case Status.ADVANCED_FAILED:
                        self.onStatusAdvancedFailed(solution.attempts);
                        break;
                    case Status.ADVANCED_SUCCESS:
                        self.onStatusAdvancedSuccess();
                        break;
                }
            })
            .fail(function (jqXHR, textStatus, errorThrown) {
                if (attempts < 3) {
                    setTimeout(function () {
                        self.getStatus();
                    }, 1000);
                    attempts++;
                }
            });
        },

        onStatusMissing(attempts) {
            setTimeout(() => {
                this.getStatus();
            }, 2000);
        },

        onStatusPending() {
            const self = this;

            self.previouslyPending = true;
            self._setProgressText(self.basicSolvingMsg);
            self._showStatus();

            setTimeout(function () {
                self.getStatus();
            }, 10000);
        },

        onStatusAdvancedPending(queueSize, stage) {
            const self = this;

            self.previouslyPending = true;
            self._setProgressText(self.advancedSolvingMsg);
            self._showStatus();

            if (queueSize !== null && typeof queueSize !== "undefined") {
                self._updateInfoModal("pixinsight-queue-size", queueSize);
            }

            if (stage !== null && typeof stage !== "undefined") {
                self._updateInfoModal("pixinsight-stage", self._humanizePixInsightStage(stage));
            }

            setTimeout(function () {
                self.getStatus();
            }, 10000);
        },

        onStatusFailed(attempts) {
            const self = this;

            if (attempts < 3) {
                setTimeout(() => {
                    this.getStatus();
                }, 10000);
                return;
            }

            if (self.previouslyPending) {
                self._hideLoading();
                self._setProgressText(self.solveFailedMsg);
            }
        },

        onStatusAdvancedFailed(attempts) {
            const self = this;

            if (attempts < 3) {
                setTimeout(() => {
                    this.getStatus();
                }, 10000);
            }

            if (self.previouslyPending) {
                self._hideLoading();
                self._setProgressText(self.solveAdvancedFailedMsg);
            }
        },

        onStatusSuccess() {
            const self = this;

            if (self.perform_advanced) {
                self.onStatusAdvancedPending();
                return;
            }

            if (self.previouslyPending) {
                self._hideLoading();
                self._setProgressText(self.solveSuccessMsg);
            }
        },

        onStatusAdvancedSuccess() {
            const self = this;

            if (self.previouslyPending) {
                self._hideLoading();
                self._setProgressText(self.solveAdvancedSuccessMsg);
                self._updateInfoModal("pixinsight-stage", self._humanizePixInsightStage("END_TASK"));
            }
        },

        onError(error) {
            const self = this;
            let message;

            if (error.indexOf("Connection refused") > -1 || error.indexOf("timed out") > -1) {
                message = self.i18n.connectionRefused;
            } else if (error.indexOf("500") > -1) {
                message = self.i18n.internalError;
            } else if (error.indexOf("Failure to plate solve image") > -1) {
                message = null;
            } else {
                message = self.i18n.unexpectedError;
            }

            if (self.previouslyPending && !!self.showErrors && !self.errorAlreadyShown && !!message) {
                $.toast({
                    heading: self.i18n.error,
                    text: message,
                    showHideTransition: "slide",
                    allowToastClose: true,
                    position: "top-right",
                    loader: false,
                    hideAfter: false,
                    icon: "error"
                });
                self.errorAlreadyShown = true;
            }

            self.onStatusFailed();
        },

        _setProgressText(text) {
            $("#platesolving-status").find(".text").text(text);
        },

        _showStatus() {
            $("#platesolving-status").removeClass("d-none");
        },

        _hideLoading() {
            $("#platesolving-status").find(".loading").hide();
        },

        _setInfoModalLoading(loading) {
            if (loading) {
                $("#plate-solving-information-modal").find(".loading").show();
            } else {
                setTimeout(() => {
                    $("#plate-solving-information-modal").find(".loading").hide();
                }, 500);
            }
        },

        _updateInfoModal(property, value) {
            $("#plate-solving-information-modal").find("." + property).html(
                value === null || value === undefined ? this.i18n.na : value
            );
        },

        _humanizeStatus(status) {
            switch (status) {
                case Status.MISSING:
                    return this.i18n.statusMissing;
                case Status.PENDING:
                    return this.i18n.statusPending;
                case Status.SUCCESS:
                    return this.i18n.statusSuccess;
                case Status.FAILED:
                    return this.i18n.statusFailed;
                case Status.ADVANCED_PENDING:
                    return this.i18n.statusAdvancedPending;
                case Status.ADVANCED_SUCCESS:
                    return this.i18n.statusAdvancedSuccess;
                case Status.ADVANCED_FAILED:
                    return this.i18n.statusAdvancedFailed;
                default:
                    return this.i18n.na;
            }
        },

        _humanizePixInsightStage(stage) {
            switch (stage) {
                case "START_TASK":
                    return this.i18n.pixInsightStageStartTask;
                case "DOWNLOADING_IMAGE":
                    return this.i18n.pixInsightStageDownloadingImage;
                case "PLATE_SOLVING_IMAGE":
                    return this.i18n.pixInsightStagePlateSolvingImage;
                case "GENERATING_IMAGE_ANNOTATIONS":
                    return this.i18n.pixInsightStageGeneratingImageAnnotations;
                case "PROCESSING_SVG_DOCUMENTS":
                    return this.i18n.pixInsightStageProcessingSvgDocuments;
                case "GENERATING_FINDING_CHARTS":
                    return this.i18n.pixInsightStageGeneratingFindingCharts;
                case "UPLOADING_RESULT":
                    return this.i18n.pixInsightStageUploadingResults;
                case "END_TASK":
                    return this.i18n.pixInsightStageEndTask;
                default:
                    return this.i18n.na;
            }
        }
    };

    Platesolving.advancedSvgLoaded = function () {
        if (!window.bowser) {
            return;
        }

        const browserParser = window.bowser.getParser(window.navigator.userAgent);

        if (!browserParser) {
            return;
        }

        const browser = browserParser.getBrowser();
        const isSafari = browser.name === "Safari";
        const isFirefox = browser.name === "Firefox";
        const isFirefox92 = isFirefox && browser.version.indexOf("92") === 0;

        if (isSafari || isFirefox92) {
            const contentDocument = document.getElementById("advanced-plate-solution-svg").contentDocument;
            contentDocument.querySelector("svg > g").removeAttribute("filter");
        }
    };

    win.AstroBinPlatesolving = Platesolving;
})(window);
