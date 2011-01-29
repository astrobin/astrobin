/*
 * All of AstroBin's javascript and jQuery code.
 */

/**********************************************************************
 * Common
 *********************************************************************/
var common = {
    config: {
        /* Notifications */
        notifications_base_url     : '/activity?id=notification_',
        notifications_element_empty: 'ul#notification-feed li#empty',
        notifications_element_image: 'img#notifications',
        notifications_element_ul   : 'ul#notification-feed',
        notifications_icon_new     : '/static/icons/iconic/orange/new_notifications.png',

        /* Messages */
        messages_base_url          : '/activity?iD=message_',
        messages_element_empty     : 'ul#message-feed li#empty',
        messages_element_image     : 'img#messages',
        messages_element_ul        : 'ul#message-feed',
        messages_icon_new          : '/static/icons/iconic/orange/new_messages.png',
        message_detail_url         : '/messages/detail/'
    },

    listen_for_notifications: function(username, last_modified, etag) {
        $.ajax({
            'beforeSend': function(xhr) {
                xhr.setRequestHeader("If-None-Match", etag);
                xhr.setRequestHeader("If-Modified-Since", last_modified);
            },
            url: common.config.notifications_base_url + username,
            dataType: 'text',
            type: 'get',
            cache: 'false',
            success: function(data, textStatus, xhr) {
                etag = xhr.getResponseHeader('Etag');
                last_modified = xhr.getResponseHeader('Last-Modified');

                json = jQuery.parseJSON(data);

                $(common.config.notifications_element_empty).remove();
                $(common.config.notifications_element_image)
                    .attr('src', common.config.notifications_icon_new);
                $(common.config.notifications_element_ul)
                    .prepend('<li class="unread">'+json['message']+'</li>');

                /* Start the next long poll. */
                listen_for_notifications(username, last_modified, etag);
            }
        });
    },

    listen_for_messages: function(username, last_modified, etag) {
        $.ajax({
            'beforeSend': function(xhr) {
                xhr.setRequestHeader("If-None-Match", etag);
                xhr.setRequestHeader("If-Modified-Since", last_modified);
            },
            url: common.config.messages_base_url + username,
            dataType: 'text',
            type: 'get',
            cache: 'false',
            success: function(data, textStatus, xhr) {
                etag = xhr.getResponseHeader('Etag');
                last_modified = xhr.getResponseHeader('Last-Modified');

                json = jQuery.parseJSON(data);

                $(common.config.messages_element_empty).remove();
                $(common.config.messages_element_image)
                    .attr('src', common.config.messages_icon_new);
                $(common.config.messages_element_ul).prepend('\
                    <li class="unread">\
                        <a href="' + common.config.message_detail_url + json['message_id'] + '">\
                            <strong>'+json['sender']+'</strong>: "' + json['subject'] + '"\
                        </a>\
                    </li>\
                ');

                /* Start the next long poll. */
                listen_for_messages(username, last_modified, etag);
            }
        });
    },

    start_listeners: function(username) {
        setTimeout(function() {
            common.listen_for_notifications(username, '', '');
            common.listen_for_messages(username, '', '');
        }, 1000);
    },

    clearText: function(field) {
        if (field.defaultValue == field.value) field.value = '';
        else if (field.value == '') field.value = field.defaultValue;
    }
};

/**********************************************************************
 * Image detail
 *********************************************************************/
var image_detail = {
    config: {
        /* Menus */
        topmenu   : '.topnav',
        sub       : 'div.sub',
        timeout   : 500,

        /* Rating */
        rating: {
            element       : '#rating',
            icons_path    : '/static/images/raty/',
            rate_url      : '/rate/',
            get_rating_url: '/get_rating/',
            hint_list     : ['bad', 'poor', 'regular', 'good', 'gorgeous'],
            read_only     : true
        }
    },

    globals: {
        /* Menus */
        closeTimer    : 0,
        currentItem   : 0,

        /* Common */
        image_id      : 0,

        /* Rating */
        rating: {
           current: 0
        }
    },

    top_close: function() {
        if (image_detail.globals.currentItem) {
            image_detail.globals.currentItem.css('visibility', 'hidden');
        }
    },

    top_open: function(_parent, _klass) {
        image_detail.top_canceltimer();
        image_detail.top_close();
        image_detail.globals.currentItem =
            _parent.find(_klass).css('visibility', 'visible');
    },

    top_timer: function() {
        image_detail.globals.closetimer =
            window.setTimeout(image_detail.top_close,
                              image_detail.config.timeout);
    },

    top_canceltimer: function() {
        if(image_detail.globals.closetimer) {
            window.clearTimeout(image_detail.globals.closetimer);
            image_detail.globals.closetimer = 0;
        }
    },

    setup_raty: function() {
        $(image_detail.config.rating.element).raty({
            start: image_detail.globals.rating.current,
            path: image_detail.config.rating.icons_path,
            readOnly: image_detail.config.rating.read_only,
            showHalf: true,
            hintList: image_detail.config.rating.hint_list,
            onClick: function(score) {
                $.ajax({
                    url: image_detail.config.rating.rate_url + image_detail.globals.image_id + '/' + score + '/',
                    success: function(data, textStatus, XMLHttpRequst) {
                        $.ajax({
                            url: image_detail.config.rating.get_rating_url + image_detail.config.image_id + '/',
                            success: function(data) {
                                var rating = $.parseJSON(data).rating
                                $.fn.raty.start(rating);
                                $.fn.raty.readOnly(true);
                            }
                        });
                    },
                    error: function(XMLHttpRequest, textStatus, errorThrown) {
                        $.fn.raty.readOnly(true);
                    }
                });
            }
        });
    },

    init: function(image_id, current_rating, config) {
        /* Init */
        image_detail.globals.image_id = image_id;
        image_detail.globals.rating.current = current_rating;
        $.extend(true, image_detail.config, config);

        /* Menus */
        $(image_detail.config.topmenu)
            .find('li')
            .bind('mouseover', function() {
                image_detail.top_open($(this), image_detail.config.sub);
            })
            .bind('mouseout', image_detail.top_timer);

        /* Rating */
        image_detail.setup_raty();
    }
};

