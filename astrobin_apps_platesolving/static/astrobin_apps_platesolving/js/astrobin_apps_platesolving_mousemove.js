(function (win) {
    function PlatesolvingMouseMove(
        $image,
        $tooltip,
        $xRuler,
        $yRuler,
        raMatrix,
        decMatrix,
        matrixRect,
        matrixDelta,
        solvedSizeX,
        solvedSizeY,
        scale
    ) {
        var self = this;

        self.enableCall = true;

        $tooltip.mousemove(function (e) {
            $tooltip.show();
        });

        $image.mousemove(function (e) {
            if (!$tooltip.hasClass('hover-overlay-disabled')) {

                if (!self.enableCall) return;

                self.enableCall = false;

                var x = e.offsetX;
                var y = e.offsetY;
                var scaledX = x * solvedSizeX / $image.outerWidth();
                var scaledY = y * solvedSizeY / $image.outerHeight();

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
                var interpolationText = interpolation.interpolateAsText(
                    scaledX, scaledY, false, true, true);

                $tooltip.show();

                if ($tooltip.hasClass('full')) {
                    $tooltip.css({
                        right: 'calc(50% - ' + $tooltip.outerWidth() / 2 + 'px)'
                    });
                }

                $xRuler.css({top: y}).show();
                $yRuler.css({left: x}).show();

                if ($tooltip.find('.image-coordinates') && x !== undefined) {
                    $tooltip.find('.x').text('x: ' + x);
                    $tooltip.find('.y').text('y: ' + y);
                    $tooltip.find('.image-coordinates').show();
                    $tooltip.find('.image-coordinates abbr').css('display', 'inline-block');
                }

                if ($tooltip.find('.equatorial-coordinates') && interpolationText.alpha !== undefined) {
                    $tooltip.find('.alpha').text('α: ' + interpolationText.alpha);
                    $tooltip.find('.delta').text('δ: ' + interpolationText.delta);
                    $tooltip.find('.equatorial-coordinates').show();
                    $tooltip.find('.equatorial-coordinates abbr').css('display', 'inline-block');
                }

                if ($tooltip.find('.galactic-coordinates') && interpolationText.l !== undefined) {
                    $tooltip.find('.l').text('l: ' + interpolationText.l);
                    $tooltip.find('.b').text('b: ' + interpolationText.b);
                    $tooltip.find('.galactic-coordinates').show();
                    $tooltip.find('.galactic-coordinates abbr').css('display', 'inline-block');
                }

                if ($tooltip.find('.ecliptic-coordinates') && interpolationText.lambda !== undefined) {
                    $tooltip.find('.lambda').text('λ: ' + interpolationText.lambda);
                    $tooltip.find('.beta').text('β: ' + interpolationText.beta);
                    $tooltip.find('.ecliptic-coordinates').show();
                    $tooltip.find('.ecliptic-coordinates abbr').css('display', 'inline-block');
                }
            }

            setTimeout(function () {
                self.enableCall = true;
            }, 10);
        }).mouseleave(function () {
            $tooltip.hide();
            $xRuler.hide();
            $yRuler.hide();
        });
    }

    win.AstroBinPlatesolvingMouseMove = PlatesolvingMouseMove;
})(window);
