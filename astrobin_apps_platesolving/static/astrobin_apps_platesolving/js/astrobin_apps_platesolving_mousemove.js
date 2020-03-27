(function (win) {
    function PlatesolvingMouseMove(raMatrix, decMatrix, matrixRect, matrixDelta, solvedSizeX, solvedSizeY, scale) {

        var self = this;

        self.$image = $('.show-ra-dec-coordinates');
        self.$tooltip = $('#ra-dec-coordinates');
        self.$xRuler = $('#x-ruler');
        self.$yRuler = $('#y-ruler');

        self.enableCall = true;

        self.$tooltip.mousemove(function (e) {
            self.$tooltip.show();
        });

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
                matrixDelta,
                undefined,
                scale);
            var interpolationText = interpolation.interpolateAsText(scaledX, scaledY, false, true, true);

            self.$tooltip.show();

            if (self.$tooltip.hasClass('full')) {
                self.$tooltip.css({
                    right: 'calc(50% - ' + self.$tooltip.outerWidth() / 2 + 'px)'
                });
            }

            self.$xRuler.css({top: y}).show();
            self.$yRuler.css({left: x}).show();

            if (self.$tooltip.find('.image-coordinates') && x !== undefined) {
                self.$tooltip.find('.x').text('x: ' + x);
                self.$tooltip.find('.y').text('y: ' + y);
                self.$tooltip.find('.image-coordinates').show();
                self.$tooltip.find('.image-coordinates abbr').css('display', 'inline-block');
            }

            if (self.$tooltip.find('.equatorial-coordinates') && interpolationText.alpha !== undefined) {
                self.$tooltip.find('.alpha').text('α: ' + interpolationText.alpha);
                self.$tooltip.find('.delta').text('δ: ' + interpolationText.delta);
                self.$tooltip.find('.equatorial-coordinates').show();
                self.$tooltip.find('.equatorial-coordinates abbr').css('display', 'inline-block');
            }

            if (self.$tooltip.find('.galactic-coordinates') && interpolationText.l !== undefined) {
                self.$tooltip.find('.l').text('l: ' + interpolationText.l);
                self.$tooltip.find('.b').text('b: ' + interpolationText.b);
                self.$tooltip.find('.galactic-coordinates').show();
                self.$tooltip.find('.galactic-coordinates abbr').css('display', 'inline-block');
            }

            if (self.$tooltip.find('.ecliptic-coordinates') && interpolationText.lambda !== undefined) {
                self.$tooltip.find('.lambda').text('λ: ' + interpolationText.lambda);
                self.$tooltip.find('.beta').text('β: ' + interpolationText.beta);
                self.$tooltip.find('.ecliptic-coordinates').show();
                self.$tooltip.find('.ecliptic-coordinates abbr').css('display', 'inline-block');
            }

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
