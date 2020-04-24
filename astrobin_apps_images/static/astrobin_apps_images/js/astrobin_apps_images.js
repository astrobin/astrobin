$(document).ready(function () {
    
    /* TODO: make this a jQuery plugin */

    window.loadAstroBinImages = function (fragment) {
        var tries = {};

        $(fragment).find('img.astrobin-image').each(function (index) {
            var $img = $(this),
                random_timeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
                id = $img.data('id'),
                revision = $img.data('revision'),
                alias = $img.data('alias'),
                url = $img.data('get-thumb-url'),
                enhanced_thumbnail_url = $img.data('enhanced-thumb-url'),
                get_enhanced_thumbnail_url = $img.data('get-enhanced-thumb-url'),
                loaded = $img.data('loaded');

            if (!loaded) {
                setTimeout(function () {
                    load(url, id, revision, alias, tries, false, random_timeout);
                }, random_timeout);
            } else if (enhanced_thumbnail_url || get_enhanced_thumbnail_url) {
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
            random_timeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
            id = $img.data('id'),
            revision = $img.data('revision'),
            alias = $img.data('alias'),
            enhanced_thumbnail_url = $img.data('enhanced-thumb-url'),
            get_enhanced_thumbnail_url = $img.data('get-enhanced-thumb-url');
    
        if (devicePixelRatio > 1) {
            if (enhanced_thumbnail_url !== undefined) {
                $img.attr('data-hires-loaded', true);
                $img.attr('src', enhanced_thumbnail_url);
            } else if (get_enhanced_thumbnail_url !== undefined) {
                $img.attr('data-hires-loaded', false);
                setTimeout(function () {
                    load(get_enhanced_thumbnail_url, id, revision, alias, tries, true, random_timeout);
                }, random_timeout);
            }
        }
    }

    function load(url, id, revision, alias, tries, hires, random_timeout) {       
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
                context: [url, id, revision, alias, hires, tries, random_timeout],
                url: url,
                timeout: 60000,
                success: function (data, status, request) {
                    var url = this[0],
                        id = this[1],
                        revision = this[2],
                        alias = this[3],
                        hires = this[4],
                        tries = this[5],
                        random_timeout = this[6],
                        key = getKey(id, revision, alias);
                    tries[key] += 1;
                    if (data.url === undefined || data.url === null || data.url.indexOf("placeholder") > -1) {
                        setTimeout(function () {
                            load(url, id, revision, alias, tries, hires, random_timeout);
                        }, random_timeout * Math.pow(2, tries[key]));
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


