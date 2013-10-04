$(document).ready(function() {
    /* TODO: make this a jQuery plugin */
    window.loadAstroBinImages = function(fragment) {
        /* We're relayouting all of them... how inefficient! */
        $('.js-masonry').each(function() {
            var masonry = $(this).data('masonry');
            if (masonry !== undefined) {
                masonry.reloadItems();
                masonry.layout();
            }
        });

        $(fragment).find('img.astrobin-image[data-loaded=false]').each(function(index) {
            var $img = $(this);
            var id = $img.attr('data-id');
            var alias = $img.attr('data-alias');
            var revision = $img.attr('data-revision');
            var mod = $img.attr('data-mod');
            var url = '/' + id + '/'

            if (revision != '' && revision != 'final')
                url += revision + '/thumb/';
            else
                url += 'thumb/';

            url += alias + '/';

            if (mod != '' && mod != 'None' && mod != 'regular')
                url += mod + '/';

            /* TODO: verify that this works in all browsers. */
            $.ajax({
                dataType: 'json',
                timeout: 0,
                cache: true,
                url: url,
                success: function(data, status, request) {
                    $('img.astrobin-image[data-id=' + data.id + '][data-alias=' + alias + '][data-revision=' + revision +']')
                        .attr('src', data.url)
                        .attr('data-loaded', 'true');
                }
            });
        });
    }

    window.loadAstroBinImages($('body'));
});
