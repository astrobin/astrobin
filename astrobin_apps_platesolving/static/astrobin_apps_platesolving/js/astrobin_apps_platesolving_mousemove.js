(function (win) {
    function PlatesolvingMouseMove(raMatrix, decMatrix, matrixRect, matrixDelta, solvedSizeX, solvedSizeY) {
        var self = this;

        self.$image = $('.show-ra-dec-coordinates');
        self.$tooltip = $('#ra-dec-coordinates');

        this.position = [
            self.$image.offset().left,
            self.$image.offset().top,
            self.$image.offset().left + this.$image.outerWidth(),
            self.$image.offset().top + this.$image.outerHeight()
        ];

        self.enableCall = true;

        self.$image.mousemove(function (e) {
            if (!self.enableCall) return;

            self.enableCall = false;

            var x = e.pageX - self.position[0];
            var y = e.pageY - self.position[1];

            var scaledX = x * solvedSizeX / self.$image.outerWidth();
            var scaledY = y * solvedSizeY / self.$image.outerHeight();

            var interpolation = new CoordinateInterpolation(
                raMatrix,
                decMatrix,
                matrixRect[0],
                matrixRect[1],
                matrixRect[2],
                matrixRect[3],
                matrixDelta);
            var interpolationText = interpolation.interpolateAsText(scaledX, scaledY);

            self.$tooltip
                .text(interpolationText.alpha + ', ' + interpolationText.delta)
                .css({
                    left: x - self.$tooltip.width() / 2 - 10,
                    top: y - 42
                })
                .show();

            setTimeout(function () {
                self.enableCall = true;
            }, 25);
        }).mouseleave(function () {
            self.$tooltip.hide();
        });
    }

    win.AstroBinPlatesolvingMouseMove = PlatesolvingMouseMove;
})(window);

