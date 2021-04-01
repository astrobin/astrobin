$(document).ready(function () {
    window.loadAstroBinImages = function (fragment) {
        var tries = {};

        $(fragment).find('img.astrobin-image').each(function (index) {
            var $img = $(this),
                randomTimeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
                id = $img.data('id'),
                revision = $img.data('revision'),
                alias = $img.data('alias'),
                url = $img.data('get-thumb-url'),
                enhancedThumbnailUrl = $img.data('enhanced-thumb-url'),
                getEnhancedThumbnailUrl = $img.data('get-enhanced-thumb-url'),
                loaded = $img.data('loaded');

            if (!loaded) {
                setTimeout(function () {
                    load(url, id, revision, alias, tries, false, randomTimeout);
                }, randomTimeout);
            } else if (enhancedThumbnailUrl || getEnhancedThumbnailUrl) {
                loadHighDPI($img);
            }
        });
    };

    function getKey(id, revision, alias) {
        return id + '.' + revision + '.' + alias;
    }

    function loadHighDPI($img) {
        var tries = {},
            devicePixelRatio = window.devicePixelRatio,
            randomTimeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
            id = $img.data('id'),
            revision = $img.data('revision'),
            alias = $img.data('alias'),
            enhancedThumbnailUrl = $img.data('enhanced-thumb-url'),
            getEnhancedThumbnailUrl = $img.data('get-enhanced-thumb-url');
    
        if (devicePixelRatio > 1 || $img.width() > 620) {
            if (enhancedThumbnailUrl !== undefined) {
                $img.attr('data-hires-loaded', true);
                $img.attr('src', enhancedThumbnailUrl);
            } else if (getEnhancedThumbnailUrl !== undefined) {
                $img.attr('data-hires-loaded', false);
                setTimeout(function () {
                    load(getEnhancedThumbnailUrl, id, revision, alias, tries, true, randomTimeout);
                }, randomTimeout);
            }
        }
    }

    function load(url, id, revision, alias, tries, hires, randomTimeout) {
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

                    $img.attr('data-loaded', 'true')
                        .attr('data-hires-loaded', hires)
                        .attr('src', data.url);

                    delete tries[key];

                    if (!hires && (alias === 'regular' || alias === 'regular_sharpened')) {
                        loadHighDPI($img);
                    }
                }
            });
        }
    }

    window.loadAstroBinImages($('body'));
});


