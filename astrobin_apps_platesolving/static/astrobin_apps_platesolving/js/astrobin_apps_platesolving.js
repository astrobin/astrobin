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

        this.$root = $('#platesolving-status');
        this.$content = this.$root.find('.progress-text');
        this.$progress = this.$root.find('.progress');
        this.$bar = this.$root.find('.bar');
        this.$icon = this.$root.find('i');

        this.missingCounter = 0;

        $.extend(this, config);

        astrobin_common.init_ajax_csrf_token();
    }

    Platesolving.prototype = {
        process: function () {
            if (this.solution_id === 0 || this.solution_status === Status.MISSING) {
                /* The plate-solving has never been attempted on this resource. */
                this.solve();
            } else if (this.solution_status === Status.SUCCESS && this.perform_advanced === "True") {
                this.solveAdvanced();
            } else {
                this.getStatus();
            }
        },

        solve: function () {
            var self = this;

            self.onStarting();

            $.ajax({
                url: this.solveURL + this.object_id + '/' + this.content_type_id + '/',
                type: 'post',
                timeout: 60000,
                success: function (data, textStatus, jqXHR) {
                    self.solution_id = data.solution;

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
                url: this.solveAdvancedURL + this.object_id + '/' + this.content_type_id + '/',
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

            $.ajax({
                url: self.updateURL + self.solution_id + '/',
                type: 'post',
                timeout: 30000,
                success: function (data, textStatus, jqXHR) {
                    switch (data.status) {
                        case Status.MISSING:
                            self.onStatusMissing();
                            break;
                        case Status.PENDING:
                            self.onStatusPending();
                            break;
                        case Status.FAILED:
                            self.$bar.css({"width": "75%"});
                            self.$icon.attr('class', 'icon-warning-sign');
                            self.$content.text(self.solveFinalizingMsg);
                            $.ajax({
                                url: self.finalizeURL + self.solution_id + '/',
                                type: 'post',
                                timeout: 30000,
                                success: function (data, textStatus, jqXHR) {
                                    self.onStatusFailed();
                                }
                            });
                            break;
                        case Status.SUCCESS:
                            self.$bar.css({"width": self.perform_advanced === "True" ? "50%" : "75%"});
                            self.$icon.attr('class', 'icon-warning-sign');
                            self.$content.text(self.solveFinalizingMsg);
                            $.ajax({
                                url: self.finalizeURL + self.solution_id + '/',
                                type: 'post',
                                timeout: 30000,
                                success: function (data, textStatus, jqXHR) {
                                    self.onStatusSuccess();
                                }
                            });
                            break;
                        case Status.ADVANCED_SUCCESS:
                            self.$bar.css({"width": "75%"});
                            self.$icon.attr('class', 'icon-warning-sign');
                            self.$content.text(self.solveFinalizingMsg);
                            $.ajax({
                                url: self.finalizeAdvancedURL + self.solution_id + '/',
                                type: 'post',
                                timeout: 30000,
                                success: function (data, textStatus, jqXHR) {
                                    self.onStatusAdvancedSuccess();
                                }
                            });
                            break;
                        case Status.ADVANCED_FAILED:
                            self.$bar.css({"width": "75%"});
                            self.$icon.attr('class', 'icon-warning-sign');
                            self.$content.text(self.solveFinalizingMsg);
                            $.ajax({
                                url: self.finalizeAdvancedURL + self.solution_id + '/',
                                type: 'post',
                                timeout: 30000,
                                success: function (data, textStatus, jqXHR) {
                                    self.onStatusAdvancedFailed();
                                }
                            });
                            break;
                        case Status.ADVANCED_PENDING:
                            self.onStatusAdvancedPending();
                            break;
                    }
                }
            });
        },

        onStarting: function () {
            this.missingCounter = 0;
            this.$root.removeClass('hide');
            this.$bar.css({"width": "12.5%"});
            this.$content.text(this.beforeSolveMsg);
        },

        onStartingAdvanced: function () {
            this.missingCounter = 0;
            this.$root.removeClass('hide');
            this.$icon.attr('class', 'icon-ok');
            this.$bar.css({"width": "75%"});
            this.$content.text(this.beforeSolveAdvancedMsg);
        },

        onStarted: function () {
            this.onStatusPending();
        },

        onStartedAdvanced: function () {
            this.onStatusAdvancedPending();
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

            self.$icon.attr('class', 'icon-ok');
            self.$bar.css({"width": self.perform_advanced === "True" ? "25%" : "50%"});
            self.$content.text(self.solveStartedMsg);

            self.$root.removeClass('hide');

            setTimeout(function () {
                self.update();
            }, 3000);
        },

        onStatusAdvancedPending: function () {
            var self = this;

            self.$icon.attr('class', 'icon-ok');
            self.$bar.css({"width": "75%"});
            self.$content.text(self.solveAdvancedStartedMsg);

            self.$root.removeClass('hide');

            setTimeout(function () {
                self.update();
            }, 3000);
        },

        onStatusFailed: function () {
            this.$icon.attr('class', 'icon-fire');
            this.$progress.removeClass('progress-info').addClass('progress-danger');
            this.$bar.css({"width": "100%"});
            this.$content.text(this.solveFailedMsg);
            this.removeStatus();
        },

        onStatusAdvancedFailed: function () {
            this.$icon.attr('class', 'icon-fire');
            this.$progress.removeClass('progress-info').addClass('progress-danger');
            this.$bar.css({"width": "100%"});
            this.$content.text(this.solveAdvancedFailedMsg);
            this.removeStatus();
        },

        onStatusSuccess: function () {
            if (this.perform_advanced === "True") {
                this.solveAdvanced();
            } else {
                this.$content.text(this.solveSuccessMsg);
                this.$icon.attr('class', 'icon-ok');
                this.$progress.removeClass('progress-info').addClass('progress-success');
                this.$bar.css({"width": this.perform_advanced === "True" ? "50%" : "100%"});
                this.removeStatus();
            }
        },

        onStatusAdvancedSuccess: function () {
            this.$icon.attr('class', 'icon-ok');
            this.$progress.removeClass('progress-info').addClass('progress-success');
            this.$bar.css({"width": "100%"});
            this.$content.text(this.solveAdvancedSuccessMsg);
            this.removeStatus();
        },

        removeStatus: function () {
            var self = this;

            setTimeout(function () {
                self.$root.hide('slow');
            }, 5000);
        }
    };

    Platesolving.advancedSvgLoaded = function () {
        var isSafari = navigator.vendor && navigator.vendor.indexOf('Apple') > -1 &&
            navigator.userAgent &&
            navigator.userAgent.indexOf('CriOS') == -1 &&
            navigator.userAgent.indexOf('FxiOS') == -1;

        if (isSafari) {
            var contentDocument = document.getElementById("advanced-plate-solution-svg").contentDocument;
            contentDocument.querySelector("svg > g").removeAttribute("filter");
        }
    };

    win.AstroBinPlatesolving = Platesolving;
})(window);

