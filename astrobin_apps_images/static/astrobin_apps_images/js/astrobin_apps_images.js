$(document).ready(function() {
    /* TODO: make this a jQuery plugin */
    window.loadAstroBinImages = function(fragment) {
        $(fragment).find('img.astrobin-image[data-loaded=false]').each(function(index) {
            var $img = $(this);
            var random_timeout = Math.floor(Math.random() * 100) + 100; // 100-200 ms

            setTimeout(function() {
                var id = $img.attr('data-id');
                var alias = $img.attr('data-alias');
                var revision = $img.attr('data-revision');
                var url = $img.attr('data-get-thumb-url');

                $.ajax({
                    dataType: 'json',
                    timeout: 0,
                    cache: true,
                    url: url,
                    success: function(data, status, request) {
                        var $img = $('img.astrobin-image[data-id=' + data.id + '][data-alias=' + alias + '][data-revision=' + revision +']');

                        if ($img.hasClass('capty')) {
                            $img.load(function() {
                                $img.capty({animation: 'slide', speed: 200, height: $img.height()});
                                $img.closest('.capty-wrapper').find('.capty-target').show();
                            });
                        }

                        $img
                            .attr('src', data.url)
                            .attr('data-loaded', 'true');
                    }
                });
            }, random_timeout);
        });
    };

    window.loadAstroBinImages($('body'));
});
