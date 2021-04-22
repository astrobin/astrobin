$(document).ready(function () {
    window.loadAstroBinImages = function (fragment) {
        var tries = {};

        $(fragment).find('img.astrobin-image').each(function () {
            var $img = $(this),
                randomTimeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
                id = $img.data('id'),
                revision = $img.data('revision'),
                alias = $img.data('alias'),
                url = $img.data('get-thumb-url'),
                regularLargeThumbnailUrl = $img.data('regular-large-thumb-url'),
                getRegularLargeThumbnailUrl = $img.data('get-regular-large-thumb-url'),
                enhancedThumbnailUrl = $img.data('enhanced-thumb-url'),
                getEnhancedThumbnailUrl = $img.data('get-enhanced-thumb-url'),
                loaded = $img.data('loaded');

            if (!loaded) {
                setTimeout(function () {
                    load(url, id, revision, alias, tries, false, randomTimeout).then(function (url) {
                        $img.attr('data-loaded', 'true')
                            .attr('src', url);
                    });
                }, randomTimeout);
            } else {
                if (regularLargeThumbnailUrl || getRegularLargeThumbnailUrl) {
                    loadRegularLarge($img);
                }

                if (enhancedThumbnailUrl || getEnhancedThumbnailUrl) {
                    loadHighDPI($img);
                }
            }
        });
    };

    function getKey(id, revision, alias) {
        return id + '.' + revision + '.' + alias;
    }

    function loadRegularLarge($img) {
        var tries = {},
            devicePixelRatio = window.devicePixelRatio,
            randomTimeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
            id = $img.data('id'),
            revision = $img.data('revision'),
            alias = $img.data('alias'),
            regularLargeThumbnailUrl = $img.data('regular-large-thumb-url'),
            getRegularLargeThumbnailUrl = $img.data('get-regular-large-thumb-url'),
            $enhancementLoadingIndicator = $('.main-image > .enhancement-loading-indicator');

        if ($img.attr('data-regular-large-loaded') === 'true') {
            return;
        }

        if ($img.width() <= 620 || devicePixelRatio > 1) {
            return;
        }

        $enhancementLoadingIndicator.show();

        if (regularLargeThumbnailUrl !== undefined) {
            $img.attr('data-regular-large-loaded', true);
            $img.one('load', function () {
                $enhancementLoadingIndicator.hide();
            });
            $img.attr('src', regularLargeThumbnailUrl);
            return;
        }

        if (getRegularLargeThumbnailUrl !== undefined) {
            $img.attr('data-regular-large-loaded', false);
            setTimeout(function () {
                load(getRegularLargeThumbnailUrl, id, revision, alias, tries, false, randomTimeout).then(function (url) {
                    $img.one('load', function () {
                        $enhancementLoadingIndicator.hide();
                    });
                    $img.attr('data-loaded', 'true')
                        .attr('data-regular-large-loaded', true)
                        .attr('data-hires-loaded', false)
                        .attr('src', url);
                });
            }, randomTimeout);
        }
    }

    function loadHighDPI($img) {
        var tries = {},
            devicePixelRatio = window.devicePixelRatio,
            randomTimeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
            id = $img.data('id'),
            revision = $img.data('revision'),
            alias = $img.data('alias'),
            enhancedThumbnailUrl = $img.data('enhanced-thumb-url'),
            getEnhancedThumbnailUrl = $img.data('get-enhanced-thumb-url'),
            $enhancementLoadingIndicator = $('.main-image > .enhancement-loading-indicator');

        if ($img.attr('data-hires-loaded') === 'true') {
            return;
        }

        if (devicePixelRatio <= 1) {
            return;
        }

        $enhancementLoadingIndicator.show();

        if (enhancedThumbnailUrl !== undefined) {
            $img.attr('data-hires-loaded', true);
            $img.one('load', function() {
                $enhancementLoadingIndicator.hide();
            });
            $img.attr('src', enhancedThumbnailUrl);
            return;
        }

        if (getEnhancedThumbnailUrl !== undefined) {
            $img.attr('data-hires-loaded', false);
            setTimeout(function () {
                load(getEnhancedThumbnailUrl, id, revision, alias, tries, true, randomTimeout).then(function(url) {
                    $img.one('load', function () {
                        $enhancementLoadingIndicator.hide();
                    });
                    $img.attr('data-loaded', 'true')
                        .attr('data-hires-loaded', true)
                        .attr('src', url);
                });
            }, randomTimeout);
        }
    }

    function load(url, id, revision, alias, tries, hires, randomTimeout) {
        return new Promise(function(resolve) {
            if (url !== "") {
                key = getKey(id, revision, alias);
                if (tries[key] === undefined) {
                    tries[key] = 0;
                }
                if (tries[key] >= 10) {
                    img
                        .attr(
                            'src',
                            'https://placehold.jp/222/e0e0e0/' + img.width() + 'x' + img.height() +
                            '.png?text=%E2%8F%B3')
                        .attr('data-loaded', 'true');
                    return;
                }

                $.ajax({
                    dataType: 'json',
                    cache: true,
                    context: [url, id, revision, alias, hires, tries, randomTimeout],
                    url: url,
                    timeout: 60000,
                    success: function (data, status, request) {
                        var url = this[0],
                            id = this[1],
                            revision = this[2],
                            alias = this[3],
                            hires = this[4],
                            tries = this[5],
                            randomTimeout = this[6],
                            key = getKey(id, revision, alias);

                        tries[key] += 1;

                        if (data.url === undefined || data.url === null || data.url.indexOf("placeholder") > -1) {
                            setTimeout(function () {
                                load(url, id, revision, alias, tries, hires, randomTimeout);
                            }, randomTimeout * Math.pow(2, tries[key]));
                            return;
                        }

                        var $img =
                            $('img.astrobin-image[data-id=' + data.id +
                                (data.hash ? '][data-hash=' + data.hash : "") +
                                '][data-alias=' + alias +
                                '][data-revision=' + data.revision +
                                ']');

                        delete tries[key];

                        if (['regular', 'regular_sharpened'].indexOf(alias) > -1) {
                            loadRegularLarge($img);
                        }

                        if (!hires && ([
                            'regular', 'regular_sharpened', 'regular_large', 'regular_large_sharpened'
                        ].indexOf(alias) > -1)) {
                            loadHighDPI($img);
                        }

                        resolve(data.url);
                    }
                });
            }
        });
    }

    window.loadAstroBinImages($('body'));
});


