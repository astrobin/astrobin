jQuery.comet = {

    fetching: false,
    settings: {},
    url: '',
    bound: {},
    connect: function(url, options) {
        jQuery.comet.settings = jQuery.extend({
            timeout: 60000,
            onError: null,
            requestMethod: 'GET',
            typeAttr: 'type',
            dataAttr: 'data'
        }, options);
        jQuery.comet.url = url;
        jQuery.comet.fetch();
    },

    fetch: function() {
        if (jQuery.comet.fetching)
            return;

        jQuery.comet.fetching = true;
        $.ajax({
            type: jQuery.comet.settings.requestMethod,
            url: jQuery.comet.url,
        
            async: true,
            cache: true,
            timeout: jQuery.comet.settings.timeout,
            ifModified: true,
        
            success: function(data) {
                jQuery.comet.fetching = false;
                jQuery.comet.handle_update(data);
                setTimeout(jQuery.comet.fetch, 1);
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                jQuery.comet.fetching = false;
                if (textStatus == 'timeout') {
                    jQuery.comet.fetch()
                } else {
                    if (jQuery.comet.settings.onError != null) {
                        jQuery.comet.settings.onError(XMLHttpRequest, textStatus, errorThrown);
                    }
                    setTimeout(jQuery.comet.fetch, 10000);
                }
                
            }
        });
    },

    handle_update: function(update) {
        type = null;
        data = update;
        
        if (update[jQuery.comet.settings.typeAttr]) {
            type = update[jQuery.comet.settings.typeAttr];
        }
        if (update[jQuery.comet.settings.dataAttr]) {
            data = update[jQuery.comet.settings.dataAttr];
        }
        
        jQuery(document).trigger(type + ".comet", [data, type]);
    },

};
