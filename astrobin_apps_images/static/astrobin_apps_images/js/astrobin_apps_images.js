$(document).ready(function() {
    window.loadAstroBinImages = function(fragment) {
        $('.astrobin-thumbnails').justifiedGallery();

        $(fragment).find('img.astrobin-image').each(function(index) {
            var $img = $(this);
            var random_timeout = Math.floor(Math.random() * 100) + 100; // 100-200 ms

            setTimeout(function() {
                var id = $img.data('id');
                    alias = $img.data('alias'),
                    revision = $img.data('revision'),
                    url = $img.data('get-thumb-url'),
                    loaded = $img.data('loaded');

                if (!loaded && url !== "") {
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

                            $img
                                .attr('src', data.url)
                                .attr('data-loaded', 'true');
                        }
                    });
                }
            }, random_timeout);
        });
    };

    $('.astrobin-thumbnails').justifiedGallery({
        rowHeight: 220,
        selector: 'a, div:not(.endless_container)'
    });

   window.loadAstroBinImages($('body'));
});
