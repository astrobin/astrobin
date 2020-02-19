$(document).ready(function () {
    /* TODO: make this a jQuery plugin */
    window.loadAstroBinImages = function (fragment) {
        var tries = {};

        $(fragment).find('img.astrobin-image').each(function (index) {
            var $img = $(this),
                random_timeout = Math.floor(Math.random() * 100) + 100, // 100-200 ms
                id = $img.data('id'),
                hash = $img.data('hash'),
                revision = $img.data('revision'),
                alias = $img.data('alias'),
                url = $img.data('get-thumb-url'),
                loaded = $img.data('loaded'),
                key = id + '.' + revision + '.' + alias;

            function load() {
                if (!loaded && url !== "") {
                    if (tries[key] === undefined) {
                        tries[key] = 0;
                    }

                    if (tries[key] >= 10) {
                        $img
                            .attr(
                                'src',
                                'https://placehold.jp/222/e0e0e0/' + $img.width() + 'x' + $img.height() +
                                '.png&text=%E2%8F%B3')
                            .attr('data-loaded', 'true');
                        return;
                    }

                    $.ajax({
                        dataType: 'json',
                        timeout: 0,
                        cache: true,
                        url: url,
                        timeouot: 60000,
                        success: function (data, status, request) {
                            tries[key] += 1;
                            if (data.url === undefined || data.url === null || data.url.indexOf("placeholder") > -1) {
                                setTimeout(function () {
                                    load();
                                }, random_timeout * Math.pow(2, tries[key]));
                                return;
                            }

                            var $img =
                                $('img.astrobin-image[data-id=' + data.id +
                                    (data.hash ? '][data-hash=' + data.hash : "") +
                                    '][data-alias=' + data.alias +
                                    '][data-revision=' + data.revision +
                                    ']');

                            $img
                                .attr('src', data.url)
                                .attr('data-loaded', 'true');

                            delete tries[key];
                        }
                    });
                }
            }

            setTimeout(function () {
                load();
            }, random_timeout);
        });
    };

    window.loadAstroBinImages($('body'));
});
