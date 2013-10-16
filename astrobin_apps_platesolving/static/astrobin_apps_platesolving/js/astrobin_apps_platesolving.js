(function(win) {
    function Platesolving(config) {
        this.solveURL  = '/platesolving/solve/';
        this.statusURL = '/api/v2/platesolving/solutions/';
        this.updateURL = '/platesolving/update/';

        this.$root = $('#platesolving-status');
        this.$content = this.$root.find('.alert-content');
        this.$alert = this.$root.find('.alert');
        this.$icon = this.$root.find('i');

        this.updateQueries = 0;

        $.extend(this, config);

        astrobin_common.init_ajax_csrf_token();
    }

    Platesolving.prototype = {
        process: function() {
            if (this.solution === 0) {
                /* The platesolving has never been attempted on this resource. */
                this.solve();
            } else {
                this.getStatus();
            }
        },

        solve: function() {
            var self = this;

            self.onStarting();

            $.ajax({
                url: this.solveURL + this.image + '/',
                type: 'post',
                timeout: 30000,
                success: function(data, textStatus, jqXHR) {
                    self.onStarted();
                }
            });
        },

        getStatus: function() {
            var self = this;

            $.ajax({
                url: this.statusURL + this.solution + '/',
                success: function(data, textStatus, jqXHR) {
                    self.dispatchOnStatus(data['status']);
                }
            });
        },

        update: function() {
            var self = this;

            $.ajax({
                url: this.updateURL + this.solution + '/',
                type: 'post',
                timeout: 30000,
                success: function(data, textStatus, jqXHR) {
                    self.updateQueries = self.updateQueries + 1;
                    self.dispatchOnStatus(data['status']);
                }
            });
        },

        dispatchOnStatus: function(status) {
            switch (status) {
                case 0: this.onStatusMissing(); break;
                case 1: this.onStatusPending(); break;
                case 2: this.onStatusFailed(); break;
                case 3: this.onStatusSuccess(); break;
            }
        },

        onStarting: function() {
            this.$root.removeClass('hide');
            this.$content.text(this.beforeSolveMsg);
        },

        onStarted: function() {
            this.$icon.attr('class', 'icon-ok');
            this.$alert.removeClass('alert-warning').addClass('alert-success');
            this.$content.text(this.solveStartedMsg);
        },

        onStatusMissing: function() {
            this.solve();
        },

        onStatusPending: function() {
            var self = this;

            self.$icon.attr('class', 'icon-ok');
            self.$alert.removeClass('alert-warning').addClass('alert-success');
            self.$content.text(self.solveStartedMsg);

            self.$root.removeClass('hide');
            if (self.updateQueries == 0)
                self.update();
            else
                setTimeout(function() {
                    self.update();
                }, 5000);
        },

        onStatusFailed: function() {
            this.$icon.attr('class', 'icon-fire');
            this.$alert.removeClass('alert-warning').addClass('alert-error');
            this.$content.text(this.solveFailedMsg);
            this.removeStatus();
        },

        onStatusSuccess: function() {
            this.$icon.attr('class', 'icon-ok');
            this.$alert.removeClass('alert-warning').addClass('alert-success');
            this.$content.text(this.solveSuccessMsg);
            this.removeStatus();
        },

        removeStatus: function() {
            var self = this;

            setTimeout(function() {
                self.$root.hide('slow');
            }, 5000);
        }
    };

    win.AstroBinPlatesolving = Platesolving;
})(window);

