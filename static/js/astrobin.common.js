function listen_for_notifications(username, last_modified, etag) {
    $.ajax({
        'beforeSend': function(xhr) {
            xhr.setRequestHeader("If-None-Match", etag);
            xhr.setRequestHeader("If-Modified-Since", last_modified);
        },
        url: '/activity?id=notification_' + username,
        dataType: 'text',
        type: 'get',
        cache: 'false',
        success: function(data, textStatus, xhr) {
            etag = xhr.getResponseHeader('Etag');
            last_modified = xhr.getResponseHeader('Last-Modified');

            json = jQuery.parseJSON(data);

            $('ul#notification-feed li#empty').remove();
            $('img#notifications').attr('src', '/static/icons/iconic/orange/new_notifications.png');
            $('ul#notification-feed').prepend('<li class="unread">'+json['message']+'</li>');

            /* Start the next long poll. */
            listen_for_notifications(username, last_modified, etag);
        }
    });
};


function listen_for_messages(username, last_modified, etag) {
    $.ajax({
        'beforeSend': function(xhr) {
            xhr.setRequestHeader("If-None-Match", etag);
            xhr.setRequestHeader("If-Modified-Since", last_modified);
        },
        url: '/activity?id=message_' + username,
        dataType: 'text',
        type: 'get',
        cache: 'false',
        success: function(data, textStatus, xhr) {
            etag = xhr.getResponseHeader('Etag');
            last_modified = xhr.getResponseHeader('Last-Modified');

            json = jQuery.parseJSON(data);

            $('ul#message-feed li#empty').remove();
            $('img#messages').attr('src', '/static/icons/iconic/orange/new_messages.png');
            $('ul#message-feed').prepend('\
                <li class="unread">\
                    <a href="#"><strong>'+json['originator']+'</strong>: "' + json['object'] + '"</a>\
                </li>');

            /* Start the next long poll. */
            listen_for_messages(username, last_modified, etag);
        }
    });
};


function start_listeners(username) {
    setTimeout(function() {
        listen_for_notifications(username, '', '');
        listen_for_messages(username, '', '');
    }, 1000);
}


function clearText(field) {
    if (field.defaultValue == field.value) field.value = '';
    else if (field.value == '') field.value = field.defaultValue;
}

