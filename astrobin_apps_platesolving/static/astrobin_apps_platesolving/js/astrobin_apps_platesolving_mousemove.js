(function (win) {
    function PlatesolvingMouseMove(raMatrix, decMatrix, matrixRect, matrixDelta, solvedSizeX, solvedSizeY) {
        var self = this;

        self.$image = $('.show-ra-dec-coordinates');
        self.$tooltip = $('#ra-dec-coordinates');
        self.$xRuler = $('#x-ruler');
        self.$yRuler = $('#y-ruler');

        self.enableCall = true;

        self.$image.mousemove(function (e) {
            if (!self.enableCall) return;

            self.enableCall = false;

            var x = e.offsetX;
            var y = e.offsetY;
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
            var interpolationText = interpolation.interpolateAsText(scaledX, scaledY, false);

            self.$tooltip
                .text(
                    'x: ' + x + ' | y: ' + y +
                    ' | α: ' + interpolationText.alpha + ' | δ: ' + interpolationText.delta
                )
                .show();

            self.$xRuler.css({top: y}).show();
            self.$yRuler.css({left: x}).show();

            setTimeout(function () {
                self.enableCall = true;
            }, 10);
        }).mouseleave(function () {
            self.$tooltip.hide();
            self.$xRuler.hide();
            self.$yRuler.hide();
        });
    }

    win.AstroBinPlatesolvingMouseMove = PlatesolvingMouseMove;
})(window);
