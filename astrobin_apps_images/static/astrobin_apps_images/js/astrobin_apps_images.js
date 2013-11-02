$(document).ready(function() {
    /* TODO: make this a jQuery plugin */
    window.loadAstroBinImages = function(fragment) {
        $(fragment).find('img.astrobin-image[data-loaded=false]').each(function(index) {
            var $img = $(this);
            var id = $img.attr('data-id');
            var alias = $img.attr('data-alias');
            var revision = $img.attr('data-revision');
            var mod = $img.attr('data-mod');
            var animated = $img.attr('data-animated');
            var url = '/' + id + '/'

            if (revision != '' && revision != 'final')
                url += revision + '/thumb/';
            else
                url += 'thumb/';

            url += alias + '/';

            if (mod != '' && mod != 'None' && mod != 'regular')
                url += mod + '/';

            if (animated == 'True') {
                url += '?animated'
            }

            /* TODO: verify that this works in all browsers. */
            $.ajax({
                dataType: 'json',
                timeout: 0,
                cache: true,
                url: url,
                success: function(data, status, request) {
                    var $img = $('img.astrobin-image[data-id=' + data.id + '][data-alias=' + alias + '][data-revision=' + revision +']');

                    if (alias == 'thumb' || alias == 'gallery') {
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
        });
    }

    window.loadAstroBinImages($('body'));
});
