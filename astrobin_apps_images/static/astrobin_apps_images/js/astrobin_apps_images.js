$(document).ready(function () {
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
                key = id + '.' + revision + '.' + alias;

                console.log("loadAstroBinImages() | image "+id+" alias="+alias+" : loaded="+loaded+" DPR="+devicePixelRatio+
                " src ="+$img.attr('src')+" get_url="+url+
                " enhanced_thumb_url="+enhanced_thumbnail_url+" get_enhanced_thumb_url="+get_enhanced_thumbnail_url);

            setTimeout(function () {
                load(url, $img, loaded, tries);
            }, random_timeout);
        });
    };

    function loadHighDPI(img) {
        var tries = {},
            devicePixelRatio = window.devicePixelRatio,
            random_timeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
            id = img.data('id'),
            revision = img.data('revision'),
            alias = img.data('alias'),
            url = img.data('get-thumb-url'),
            enhanced_thumbnail_url = img.data('enhanced-thumb-url'),
            get_enhanced_thumbnail_url = img.data('get-enhanced-thumb-url'),
            loaded = img.data('loaded'),
            hires_loaded = img.data('hires-loaded');
            loading = false;
        console.log("loadHighDPI() | image "+id+" alias="+alias+" : loaded="+loaded+" hires_loaded="+hires_loaded+" DPR="+devicePixelRatio+
            " src ="+img.attr('src')+" get_url="+url+
            " enhanced_thumb_url="+enhanced_thumbnail_url+" get_enhanced_thumb_url="+get_enhanced_thumbnail_url);
        if (devicePixelRatio > 1) {
            if (!hires_loaded) {
                if (!(enhanced_thumbnail_url === undefined)) {
                    loaded = true;
                    hires_loaded = true;
                    img.attr('data-hires-loaded', hires_loaded);
                    img.attr('src', enhanced_thumbnail_url);
                    console.log("loadHighDPI() | image "+id+" alias="+alias+" : replaced src with "+img.data('enhanced-thumb-url'));
                } else if (!(get_enhanced_thumbnail_url === undefined)) {
                    url = get_enhanced_thumbnail_url;
                    loaded = false;
                    hires_loaded = false;
                    img.attr('data-hires-loaded', hires_loaded);
                    console.log("loadHighDPI() | image "+id+" alias="+alias+" : will need to load from "+url);
                    setTimeout(function () {
                        load(get_enhanced_thumbnail_url, img, hires_loaded, tries);
                    }, random_timeout);
                }
            }
        }
    }

    function load(url, img, loaded, tries) {
        var 
            id = img.data('id'),
            revision = img.data('revision'),
            alias = img.data('alias');
        
        if (!loaded && url !== "") {
            key = id + '.' + revision + '.' + alias;
            console.log("load() | image "+id+" alias="+alias+" : loading");
            if (tries[key] === undefined) {
                tries[key] = 0;
            }
            if (tries[key] >= 10) {
                console.log("load() | image "+id+" alias="+alias+" : giving up");
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
                url: url,
                timeout: 60000,
                success: function (data, status, request) {
                    tries[key] += 1;
                    if (data.url === undefined || data.url === null || data.url.indexOf("placeholder") > -1) {
                        console.log("load() | image "+id+" alias="+alias+" placeholder obtained");
                        setTimeout(function () {
                            load();
                        }, random_timeout * Math.pow(2, tries[key]));
                        return;
                    }
                    console.log("load() | image "+id+" alias="+alias+" : obtained - new url="+data.url);
                    var $img =
                        $('img.astrobin-image[data-id=' + data.id +
                        (data.hash ? '][data-hash=' + data.hash : "") +
                        '][data-alias=' + alias +
                        '][data-revision=' + data.revision +
                        ']');
                    $img.attr('data-loaded', 'true')
                        .attr('data-hires-loaded', 'true')
                        .attr('src', data.url);
                    console.log("load() | image "+id+" alias="+alias+" : done");
                    delete tries[key];
                }
            });
        }
    }

    $('img.astrobin-image[data-alias=regular]').one("load", function() {
        loadHighDPI($(this));
    });
    $('img.astrobin-image[data-alias=regular_sharpened]').one("load", function() {
        loadHighDPI($(this));
    });
    
    window.loadAstroBinImages($('body'));
});

