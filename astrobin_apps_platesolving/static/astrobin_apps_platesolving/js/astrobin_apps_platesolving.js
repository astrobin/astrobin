(function (win) {
    var Status = {
        MISSING: 0,
        PENDING: 1,
        FAILED: 2,
        SUCCESS: 3,
        ADVANCED_PENDING: 4,
        ADVANCED_FAILED: 5,
        ADVANCED_SUCCESS: 6
    };

    function Platesolving(config) {
        this.solveURL = '/platesolving/solve/';
        this.solveAdvancedURL = '/platesolving/solve-advanced/';
        this.apiURL = '/api/v2/platesolving/solutions/';
        this.updateURL = '/platesolving/update/';
        this.finalizeURL = '/platesolving/finalize/';
        this.finalizeAdvancedURL = '/platesolving/finalize-advanced/';

        this.i18n = config.i18n;

        this.missingCounter = 0;
        this.errorAlreadyShown = false;

        $.extend(this, config);

        astrobin_common.init_ajax_csrf_token();
    }

    Platesolving.prototype = {
        process: function () {
            var self = this;

            if (self.solution_id === 0 || self.solution_status === Status.MISSING) {
                /* The plate-solving has never been attempted on this resource. */
                self.solve();
            } else if (self.solution_status === Status.SUCCESS && self.perform_advanced === "True") {
                self.solveAdvanced();
            } else {
                self.getStatus();
            }
        },

        solve: function () {
            var self = this;

            self.onStarting();

            $.ajax({
                url: self.solveURL + self.object_id + '/' + self.content_type_id + '/',
                type: 'post',
                timeout: 60000,
                success: function (data, textStatus, jqXHR) {
                    self.solution_id = data.solution;

                    if (data.error) {
                        self.onError(data.error);
                        return;
                    }

                    if (data.status <= Status.PENDING) {
                        self.onStarted();
                    }
                }
            });
        },

        solveAdvanced: function () {
            var self = this;

            self.onStartingAdvanced();

            $.ajax({
                url: self.solveAdvancedURL + self.object_id + '/' + self.content_type_id + '/',
                type: 'post',
                timeout: 60000,
                success: function (data, textStatus, jqXHR) {
                    self.solution_id = data.solution;

                    if (data.status === Status.ADVANCED_PENDING) {
                        self.onStartedAdvanced();
                    }
                }
            });
        },

        getStatus: function () {
            var self = this;

            $.ajax({
                url: self.apiURL + self.solution_id + '/',
                cache: false,
                success: function (data, textStatus, jqXHR) {
                    if (data.error) {
                        self.onError(data.error);
                        return;
                    }

                    switch (data.status) {
                        case Status.MISSING:
                            self.onStatusMissing();
                            break;
                        case Status.PENDING:
                            self.onStatusPending();
                            break;
                        case Status.FAILED:
                            self.onStatusFailed();
                            break;
                        case Status.SUCCESS:
                            self.onStatusSuccess();
                            break;
                        case Status.ADVANCED_PENDING:
                            self.onStatusAdvancedPending();
                            break;
                        case Status.ADVANCED_FAILED:
                            self.onStatusAdvancedFailed();
                            break;
                        case Status.ADVANCED_SUCCESS:
                            self.onStatusAdvancedSuccess();
                            break;
                    }
                }
            });
        },

        update: function () {
            var self = this;

            self._setInfoModalLoading(true);

            $.ajax({
                url: self.updateURL + self.solution_id + '/',
                type: 'post',
                timeout: 30000,
                success: function (data, textStatus, jqXHR) {
                    if (data.error) {
                        self.onError(data.error);
                        return;
                    }

                    self._setInfoModalLoading(false);


                    self._updateInfoModal("status", self._humanizeStatus(data.status));

                    self._updateInfoModal(
                        "started",
                        `<abbr class="timestamp" data-epoch="${data.started}">...</abbr>`
                    );
                    astrobin_common.init_timestamps();

                    self._updateInfoModal(
                        "astrometry-job",
                        `<a href="http://nova.astrometry.net/status/${data.submission_id}" target="_blank">${data.submission_id}</a>`
                    );

                    self._updateInfoModal("pixinsight-job", data.pixinsight_serial_number);
                    self._updateInfoModal("pixinsight-stage", self._humanizePixInsightStage(data.pixinsight_stage));

                    switch (data.status) {
                        case Status.MISSING:
                            self.onStatusMissing();
                            break;
                        case Status.PENDING:
                            self.onStatusPending();
                            break;
                        case Status.FAILED:
                            self._setProgressBar(75);
                            self._setIcon('icon-warning-sign');
                            self._setProgressText(self.solveFinalizingMsg);
                            $.ajax({
                                url: self.finalizeURL + self.solution_id + '/',
                                type: 'post',
                                timeout: 30000,
                                success: function (data, textStatus, jqXHR) {
                                    if (data.error) {
                                        self.onError(data.error);
                                        return;
                                    }

                                    self.onStatusFailed();
                                }
                            });
                            break;
                        case Status.SUCCESS:
                            self._setProgressBar(self.perform_advanced === "True" ? 50 : 75);
                            self._setIcon('icon-warning-sign');
                            self._setProgressText(self.solveFinalizingMsg);
                            $.ajax({
                                url: self.finalizeURL + self.solution_id + '/',
                                type: 'post',
                                timeout: 30000,
                                success: function (data, textStatus, jqXHR) {
                                    if (data.error) {
                                        self.onError(data.error);
                                        return;
                                    }

                                    self.onStatusSuccess();
                                }
                            });
                            break;
                        case Status.ADVANCED_SUCCESS:
                            self._setProgressBar(75);
                            self._setIcon('icon-warning-sign');
                            self._setProgressText(self.solveFinalizingMsg);
                            $.ajax({
                                url: self.finalizeAdvancedURL + self.solution_id + '/',
                                type: 'post',
                                timeout: 30000,
                                success: function (data, textStatus, jqXHR) {
                                    if (data.error) {
                                        self.onError(data.error);
                                        return;
                                    }

                                    self.onStatusAdvancedSuccess();
                                }
                            });
                            break;
                        case Status.ADVANCED_FAILED:
                            self._setProgressBar(75);
                            self._setIcon('icon-warning-sign');
                            self._setProgressText(self.solveFinalizingMsg);
                            $.ajax({
                                url: self.finalizeAdvancedURL + self.solution_id + '/',
                                type: 'post',
                                timeout: 30000,
                                success: function (data, textStatus, jqXHR) {
                                    if (data.error) {
                                        self.onError(data.error);
                                        return;
                                    }

                                    self.onStatusAdvancedFailed();
                                }
                            });
                            break;
                        case Status.ADVANCED_PENDING:
                            self.onStatusAdvancedPending(data.queue_size);
                            break;
                    }
                }
            });
        },

        onStarting: function () {
            var self = this;

            self.missingCounter = 0;
            self._showStatus();
            self._setProgressBar(12.5);
            self._setProgressText(self.beforeSolveMsg);
        },

        onStartingAdvanced: function () {
            var self = this;

            self.missingCounter = 0;
            self._showStatus();
            self._setIcon('icon-ok');
            self._setProgressBar(75);
            self._setProgressText(self.beforeSolveAdvancedMsg);
        },

        onStarted: function () {
            var self = this;

            self.onStatusPending();
        },

        onStartedAdvanced: function () {
            var self = this;

            self.onStatusAdvancedPending();
        },

        onStatusMissing: function () {
            var self = this;

            if (self.missingCounter < 5)
                self.solve();
            else
                setTimeout(function () {
                    self.update();
                }, 3000);

            self.missingCounter += 1;
        },

        onStatusPending: function () {
            var self = this;

            self._setIcon('icon-ok');
            self._setProgressBar(self.perform_advanced === "True" ? 25 : 50);
            self._setProgressText(self.solveStartedMsg);
            self._showStatus();

            setTimeout(function () {
                self.update();
            }, 3000);
        },

        onStatusAdvancedPending: function (queueSize) {
            var self = this;

            self._setIcon('icon-ok');
            self._setProgressBar(75);
            self._setProgressText(self.solveAdvancedStartedMsg);

            if (queueSize !== null && queueSize !== undefined) {
                self._updateInfoModal("pixinsight-queue-size", queueSize);
            }

            self._showStatus();

            setTimeout(function () {
                self.update();
            }, 3000);
        },

        onStatusFailed: function () {
            var self = this;

            self._setIcon('icon-fire');
            self._switchProgressClasses('info', 'danger');
            self._setProgressBar(100);
            self._setProgressText(self.solveFailedMsg);
        },

        onStatusAdvancedFailed: function () {
            var self = this;

            self._setIcon('icon-fire');
            self._switchProgressClasses('info', 'danger');
            self._setProgressBar(100);
            self._setProgressText(self.solveAdvancedFailedMsg);
        },

        onStatusSuccess: function () {
            var self = this;

            if (self.perform_advanced === "True") {
                self.solveAdvanced();
            } else {
                self._setProgressText(self.solveSuccessMsg);
                self._setIcon('icon-ok');
                self._switchProgressClasses('info', 'success');
                self._setProgressBar(self.perform_advanced === "True" ? 50 :100);
            }
        },

        onStatusAdvancedSuccess: function () {
            var self = this;

            self._setIcon('icon-ok');
            self._switchProgressClasses('info', 'success');
            self._setProgressBar(100);
            self._setProgressText(self.solveAdvancedSuccessMsg);
            self._updateInfoModal("pixinsight-stage", self._humanizePixInsightStage("END_TASK"));
        },

        onError: function (error) {
            var self = this;
            var message;

            if (error.indexOf("Connection refused") > -1 || error.indexOf("timed out") > -1) {
                message = self.i18n.connectionRefused;
            } else if (error.indexOf("500") > -1) {
                message = self.i18n.internalError;
            } else if (error.indexOf("Failure to plate solve image") > -1) {
                message = null;
            } else {
                message = self.i18n.unexpectedError;
            }

            if (!self.errorAlreadyShown && !!message) {
                $.toast({
                    heading: self.i18n.error,
                    text: message,
                    showHideTransition: 'slide',
                    allowToastClose: true,
                    position: 'top-right',
                    loader: false,
                    hideAfter: false,
                    icon: 'error'
                });
                self.errorAlreadyShown = true;
            }

            self.onStatusFailed();
        },

        _setProgressBar: function(percentage) {
            $('#platesolving-status').find('.bar').css({"width": percentage + "%"});
        },

        _setProgressText: function (text) {
            $('#platesolving-status').find('.meter .text').text(text);
        },

        _switchProgressClasses: function (removeClass, addClass) {
            $('#platesolving-status').find('.meter').removeClass(removeClass).addClass(addClass);
        },

        _setIcon: function(icon) {
            $('#platesolving-status').find('.text i').attr('class', icon);
        },

        _showStatus() {
            $('#platesolving-status').removeClass('hide');
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
                    return this.i18n.statusInvalid;
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
                case "GENERATING_FINDING_CHART":
                    return this.i18n.pixInsightStageGeneratingFindingChart;
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
        var isSafari = navigator.vendor && navigator.vendor.indexOf('Apple') > -1 &&
            navigator.userAgent &&
            navigator.userAgent.indexOf('CriOS') === -1 &&
            navigator.userAgent.indexOf('FxiOS') === -1;
        var isFirefox = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;

        if (isSafari || isFirefox) {
            var contentDocument = document.getElementById("advanced-plate-solution-svg").contentDocument;
            contentDocument.querySelector("svg > g").removeAttribute("filter");
        }
    };

    win.AstroBinPlatesolving = Platesolving;
})(window);

