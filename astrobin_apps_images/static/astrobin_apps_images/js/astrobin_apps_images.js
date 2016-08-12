$(document).ready(function() {
    /* TODO: make this a jQuery plugin */
    window.loadAstroBinImages = function(fragment) {
        $(fragment).find('img.astrobin-image').each(function(index) {
            var $img = $(this);
            var random_timeout = Math.floor(Math.random() * 100) + 100; // 100-200 ms

            setTimeout(function() {
                var id = $img.data('id');
                    alias = $img.data('alias'),
                    revision = $img.data('revision'),
                    url = $img.data('get-thumb-url'),
                    loaded = $img.data('loaded'),
                    capty = $img.hasClass('capty');

                function captify($img) {
                    var height = $img.attr('height');
                    $img.capty({animation: 'slide', speed: 200, height: height});
                    $img.closest('.capty-wrapper').find('.capty-target').show();
                }

                if (loaded && capty) {
                    captify($img);
                } else if (!loaded) {
                    $.ajax({
                        dataType: 'json',
                        timeout: 0,
                        cache: true,
                        url: url,
                        success: function(data, status, request) {
                            var $img =
                                $('img.astrobin-image[data-id=' + data.id +
                                '][data-alias=' + data.alias +
                                '][data-revision=' + data.revision +
                                ']');

                            if (data.capty) {
                                $img.load(function() {
                                    captify($img);
                                });
                            }

                            $img
                                .attr('src', data.url)
                                .attr('data-loaded', 'true');
                        }
                    });
                }
            }, random_timeout);
        });
    };

    window.loadAstroBinImages($('body'));
});
