$(document).ready(function () {
    
    var debug = true;
    
    /* TODO: make this a jQuery plugin */

    window.loadAstroBinImages = function (fragment) {
        var tries = {};

        $(fragment).find('img.astrobin-image').each(function (index) {
            var $img = $(this),
                devicePixelRatio = window.devicePixelRatio,
                random_timeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
                id = $img.data('id'),
                revision = $img.data('revision'),
                alias = $img.data('alias'),
                url = $img.data('get-thumb-url'),
                enhanced_thumbnail_url = $img.data('enhanced-thumb-url'),
                get_enhanced_thumbnail_url = $img.data('get-enhanced-thumb-url'),
                loaded = $img.data('loaded'),
                hires_loaded = $img.data('hires-loaded'),
                key = id + '.' + revision + '.' + alias;
            if (debug) console.log("loadAstroBinImages() | image "+id+" rev="+revision+" alias="+alias+" : loaded="+loaded+" DPR="+devicePixelRatio+
                " src="+$img.attr('src')+" get_thumb_url="+url+
                " enhanced_thumb_url="+enhanced_thumbnail_url+" get_enhanced_thumb_url="+get_enhanced_thumbnail_url);
            if (!loaded) {
                setTimeout(function () {
                    load(url, id, revision, alias, tries, false);
                }, random_timeout);
            } else if (enhanced_thumbnail_url || get_enhanced_thumbnail_url) {
                loadHighDPI($img);
            }
        });
    };

    function loadHighDPI($img) {
        var tries = {},
            devicePixelRatio = window.devicePixelRatio,
            random_timeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
            id = $img.data('id'),
            revision = $img.data('revision'),
            alias = $img.data('alias'),
            url = $img.data('get-thumb-url'),
            enhanced_thumbnail_url = $img.data('enhanced-thumb-url'),
            get_enhanced_thumbnail_url = $img.data('get-enhanced-thumb-url'),
            key = id + '.' + revision + '.' + alias;
    
        if (debug) console.log("loadHighDPI() | image "+key+" : DPR="+devicePixelRatio+
            " src="+$img.attr('src')+" get_url="+url+
            " enhanced_thumb_url="+enhanced_thumbnail_url+" get_enhanced_thumb_url="+get_enhanced_thumbnail_url);
        if (devicePixelRatio > 1) {
            if (!(enhanced_thumbnail_url === undefined)) {
                $img.attr('data-hires-loaded', true);
                $img.attr('src', enhanced_thumbnail_url);
                if (debug) console.log("loadHighDPI() | image "+key+" : replaced src with "+$img.data('enhanced-thumb-url'));
            } else if (!(get_enhanced_thumbnail_url === undefined)) {
                url = get_enhanced_thumbnail_url;
                $img.attr('data-hires-loaded', false);
                if (debug) console.log("loadHighDPI() | image "+key+" : will need to load from "+url);
                setTimeout(function () {
                    load(get_enhanced_thumbnail_url, id, revision, alias, tries, true);
                }, random_timeout);
            }
        }
    }

    function load(url, id, revision, alias, tries, hires) {       
        if (url !== "") {
            key = id + '.' + revision + '.' + alias;
            if (debug) console.log("load() | image "+key+" : loading");
            if (tries[key] === undefined) {
                tries[key] = 0;
            }
            if (tries[key] >= 10) {
                if (debug) console.log("load() | image "+key+" : giving up");
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
                timeout: 0,
                cache: true,
                context: [id, revision, alias, hires, tries],
                url: url,
                timeout: 60000,
                success: function (data, status, request) {
                    var id = this[0],
                        revision = this[1],
                        alias = this[2],
                        hires = this[3],
                        tries = this[4],
                        key = id + '.' + revision + '.' + alias;
                    tries[key] += 1;
                    if (data.url === undefined || data.url === null || data.url.indexOf("placeholder") > -1) {
                        if (debug) console.log("load() | image "+key+" : placeholder obtained");
                        setTimeout(function () {
                            load();
                        }, random_timeout * Math.pow(2, tries[key]));
                        return;
                    }
                    if (debug) console.log("load() | image "+key+" : obtained - new url="+data.url);
                    var $img =
                        $('img.astrobin-image[data-id=' + data.id +
                        (data.hash ? '][data-hash=' + data.hash : "") +
                        '][data-alias=' + alias +
                        '][data-revision=' + data.revision +
                        ']');
                    $img.attr('data-loaded', 'true')
                        .attr('data-hires-loaded', hires)
                        .attr('src', data.url);
                    if (debug) console.log("load() | image "+key+" : done");
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


