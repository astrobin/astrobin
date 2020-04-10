var loaded_images = {};
var loaded_hires = {};
var debug = true;

$(document).ready(function () {
    /* TODO: make this a jQuery plugin */
    /*
    $('img.astrobin-image[data-alias=regular]').one("load", function() {
        loadHighDPI($(this));
    });
    $('img.astrobin-image[data-alias=regular_sharpened]').one("load", function() {
        loadHighDPI($(this));
    });    
    */
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
            loaded_images[key] = loaded; 
            loaded_hires[key] = hires_loaded;   
            if (debug) console.log("loadAstroBinImages() | image "+id+" rev="+revision+" alias="+alias+" : loaded="+loaded+" DPR="+devicePixelRatio+
                " src="+$img.attr('src')+" get_thumb_url="+url+
                " enhanced_thumb_url="+enhanced_thumbnail_url+" get_enhanced_thumb_url="+get_enhanced_thumbnail_url);
            if (!loaded) {
                setTimeout(function () {
                    load(url, id, revision, alias, loaded, tries, false);
                }, random_timeout);
            } else if (enhanced_thumbnail_url || get_enhanced_thumbnail_url) {
                loadHighDPI($img);
            }
        });
    };

    window.loadAstroBinImages($('body'));
});

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
    loaded = loaded_images[key] === undefined ? false : loaded_images[key];
    hires_loaded = loaded_hires[key] === undefined ? false : loaded_hires[key];
    if (debug) console.log("loadHighDPI() | image "+key+" : loaded_images["+key+"]="+loaded);
    if (debug) console.log("loadHighDPI() | image "+key+" : loaded_hires["+key+"]="+hires_loaded);
    if (devicePixelRatio > 1) {
        if (loaded) {
            if (!hires_loaded) {
                if (!(enhanced_thumbnail_url === undefined)) {
                    loaded_images[key] = true;
                    loaded_hires[key] = true;
                    $img.attr('data-hires-loaded', true);
                    $img.attr('src', enhanced_thumbnail_url);
                    if (debug) console.log("loadHighDPI() | image "+key+" : replaced src with "+$img.data('enhanced-thumb-url'));
                } else if (!(get_enhanced_thumbnail_url === undefined)) {
                    url = get_enhanced_thumbnail_url;
                    $img.attr('data-hires-loaded', false);
                    if (debug) console.log("loadHighDPI() | image "+key+" : will need to load from "+url);
                    setTimeout(function () {
                        load(get_enhanced_thumbnail_url, id, revision, alias, hires_loaded, tries, true);
                    }, random_timeout);
                }
            } else {
                if (debug) console.log("loadHighDPI() | image "+key+" already in HD");
            }
        } else {
            if (debug) console.log("loadHighDPI() | image "+key+" hasn't finished loading");
            /*
            $('img.astrobin-image[data-alias=regular]').one("load", function() {
                loadHighDPI($(this));
            });
            $('img.astrobin-image[data-alias=regular_sharpened]').one("load", function() {
                loadHighDPI($(this));
            });
            */
        } 
    }
}

function load(url, id, revision, alias, loaded, tries, hires) {       
    if (!loaded && url !== "") {
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
                loaded_images[key] = true;
                $img.attr('data-loaded', 'true')
                    .attr('data-hires-loaded', hires)
                    .attr('src', data.url);
                if (hires) {
                    loaded_hires[key] = true;
                }
                if (debug) console.log("load() | image "+key+" : done");
                delete tries[key];
            }
        });
    }
}
