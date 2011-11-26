/*
 * All of AstroBin's javascript and jQuery code.
 */

/**********************************************************************
 * Common
 *********************************************************************/
var common = {
    config: {
        image_detail_url           : '/',
        /* Notifications */
        notifications_base_url     : '/activity?id=notification_',
        notifications_element_empty: 'ul#notification-feed li#empty',
        notifications_element_image: 'img#notifications',
        notifications_element_ul   : 'ul#notification-feed',
        notifications_icon_new     : '/static/icons/iconic/orange/new_notifications.png',

        /* Messages */
        messages_base_url          : '/activity?id=message_',
        messages_element_empty     : 'ul#message-feed li#empty',
        messages_element_image     : 'img#messages',
        messages_element_ul        : 'ul#message-feed',
        messages_icon_new          : '/static/icons/iconic/orange/new_messages.png',
        message_detail_url         : '/messages/detail/',


        /* Requests */
        requests_base_url          : '/activity/?id=request_',
        requests_element_empty     : 'ul#request-feed li#empty',
        requests_element_image     : 'img#requests',
        requests_element_ul        : 'ul#request-feed',
        requests_icon_new          : '/static/icons/iconic/orange/new_requests.png',
        request_detail_url         : '/requests/detail/'
    },

    globals: {
        requests: [],
        smart_ajax: $.ajax
    },

    listen_for_notifications: function(username, last_modified, etag) {
        common.globals.smart_ajax({
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
                common.listen_for_notifications(username, last_modified, etag);
            }
        });
    },

    listen_for_messages: function(username, last_modified, etag) {
        common.globals.smart_ajax({
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
                common.listen_for_messages(username, last_modified, etag);
            }
        });
    },

    listen_for_requests: function(username, last_modified, etag) {
        common.globals.smart_ajax({
            'beforeSend': function(xhr) {
                xhr.setRequestHeader("If-None-Match", etag);
                xhr.setRequestHeader("If-Modified-Since", last_modified);
            },
            url: common.config.requests_base_url + username,
            dataType: 'text',
            type: 'get',
            cache: 'false',
            success: function(data, textStatus, xhr) {
                etag = xhr.getResponseHeader('Etag');
                last_modified = xhr.getResponseHeader('Last-Modified');

                json = jQuery.parseJSON(data);

                $(common.config.requests_element_empty).remove();
                $(common.config.requests_element_image)
                    .attr('src', common.config.requests_icon_new);
                $(common.config.requests_element_ul).prepend('\
                    <li class="unread">\
                        <a href="' + common.config.image_detail_url + json['image_id'] + '/">' + json['message'] + '\
                        </a>\
                    </li>\
                ');

                /* Start the next long poll. */
                common.listen_for_requests(username, last_modified, etag);
            }
        });
    },


    start_listeners: function(username) {
        common.globals.smart_ajax = function(settings) {
            // override complete() operation
            var complete = settings.complete;
            settings.complete = function(xhr) {
                if (xhr) {
                    // xhr may be undefined, for example when downloading JavaScript
                    for (var i = 0, len = common.globals.requests.length; i < len; ++i) {
                        if (common.globals.requests[i] == xhr) {
                            // drop completed xhr from list
                            common.globals.requests.splice(i, 1);
                            break;
                        }
                    }
                }
                // execute base
                if (complete) {
                    complete.apply(this, arguments)
                }
            }

            var r = $.ajax.apply(this, arguments);
            if (r) {
                // r may be undefined, for example when downloading JavaScript
                common.globals.requests.push(r);
            }
            return r;
        };

        setTimeout(function() {
            common.listen_for_notifications(username, '', '');
            common.listen_for_messages(username, '', '');
            common.listen_for_requests(username, '', '');
        }, 1000);
    },

    clearText: function(field) {
        if (field.defaultValue == field.value) field.value = '';
        else if (field.value == '') field.value = field.defaultValue;
    },

    showHideAdvancedSearch: function() {
        $('form#advanced_search').slideToggle('slow');
    }
};

/**********************************************************************
 * Image detail
 *********************************************************************/
var image_detail = {
    config: {
        /* Menus */
        topmenu   : '.topnav',
        submenu   : 'div.sub',
        timeout   : 500,

        /* Rating */
        rating: {
            element       : '#rating',
            icons_path    : '/static/images/raty/',
            rate_url      : '/rate/',
            get_rating_url: '/get_rating/',
            hint_list     : ['bad', 'poor', 'regular', 'good', 'gorgeous'],
            read_only     : true
        },

        upload_revision_action: {
            dialog: {
                title: '',
                body : ''
            },
            element  : 'a.upload-revision',
            form_html: '',
            csrf_token: '',
            url       : '/upload/revision/process/',
            fileDefaultText: '',
            fileBtnText: '',
            uploadingText: ''
        },

        delete_action: {
            dialog: {
                title : '',
                body  : '',
                button: '',
                height: 230
            },
            element: 'a.delete-everything',
            url    : '/delete/'
        },

        delete_revision_action: {
            dialog: {
                title : '',
                body  : '',
                button: '',
                height: 230
            },
            element: 'a.delete-revision',
            url    : '/delete/revision/'
        },

        delete_original_action: {
            dialog: {
                title : '',
                body  : '',
                button: '',
                height: 230
            },
            element: 'a.delete-original',
            url    : '/delete/original/'
        },

        follow_action: {
            dialog: {
                title : '',
                body  : '',
                button: '',
                height: 230
            },
            element       : 'a.follow',
            url           : '/follow/',
            stop_following: ''
        },

        unfollow_action: {
            dialog: {
                title : '',
                body  : '',
                button: '',
                height: 230
            },
            element       : 'a.unfollow',
            url           : '/unfollow/',
            follow        : ''
        },

        message_action: {
            dialog: {
                title : '',
                body  : '',
                button: ''
            },
            element  : 'a.send-private-message',
            form_html: '',
            csrf_token: '',
            url      : ''
        },

        bring_to_attention_action: {
            dialog: {
                title : '',
                body  : '',
                button: '',
                height: 400
            },
            element  : 'a.bring-to-attention',
            form_html: '',
            autocomplete: {
                startText: '',
                emptyText: ''
            },
            url: ''
        },

        image_request_additional_information_action: {
            dialog: {
                title: '',
                body: ''
            },
            element: 'a.image-request-additional-information',
            url    : '/request/image/additional_information/'
        },

        image_request_fits_action: {
            dialog: {
                title: '',
                body: ''
            },
            element: 'a.image-request-fits',
            url    : '/request/image/fits/'
        }
    },

    globals: {
        /* Menus */
        closeTimer    : 0,
        currentItem   : 0,

        /* Common */
        image_id      : 0,
        revision_id   : 0,
        image_username: '',

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

    setup_upload_revision: function() {
        $(image_detail.config.upload_revision_action.element).click(function() {
            var dlg = $('\
                <div id="dialog-attention" title="' + image_detail.config.upload_revision_action.dialog.title + '"></div>')
                .html('\
                    <div class="sided-main-content-popup">\
                    <p>\
                        ' + image_detail.config.upload_revision_action.dialog.body + '\
                    </p>\
                    <form id="upload-revision" action="' + image_detail.config.upload_revision_action.url + '" method="post" enctype="multipart/form-data">\
                        ' + image_detail.config.upload_revision_action.form_html + '\
                        <div style="display:none;"><input type="hidden" id="csrfmiddlewaretoken" name="csrfmiddlewaretoken" value="' + image_detail.config.upload_revision_action.csrf_token + '" /></div> \
                        <input type="hidden" name="image_id" value="' + image_detail.globals.image_id  + '"/>\
                    </form>\
                    </div>\
                ')
                .dialog({
                    resizable: false,
                    modal: true});

            $('input:file').uniform(
               {fileDefaultText: image_detail.config.upload_revision_action.fileDefaultText,
                fileBtnText: image_detail.config.upload_revision_action.fileBtnText
               }
            );
            $('form#upload-revision input').live('change', function() {
                $('form#upload-revision').append('\
                    <p style="text-align:center">\
                        <img style="margin: 10px" alt="' + image_detail.config.upload_revision_action.uploadingText + '" src="/static/images/ajax-loader.gif"/>\
                    </p>');

                $('form#upload-revision').submit();
            });

        });
    },

    setup_delete: function() {
        $(image_detail.config.delete_action.element).click(function() {
            $('<div id="dialog-confirm" title="' +
              image_detail.config.delete_action.dialog.title +
              '"></div>')
                .html('\
                        <p>\
                            <span class="ui-icon ui-icon-alert"\
                                  style="float:left; margin:0 7px 20px 0;">\
                            </span>' + image_detail.config.delete_action.dialog.body + '\
                        </p>')
                .dialog({
                    resizable: false,
                    height: image_detail.config.delete_action.dialog.height,
                    modal: true,
                    buttons: [
                        {
                            text: 'OK',
                            click: function() {
                                $(this).dialog('close');
                                window.location = image_detail.config.delete_action.url + image_detail.globals.image_id;
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            click: function() {
                                $(this).dialog('close');
                            }
                        }
                    ]
                });

            return false;
        });
    },

    setup_delete_revision: function() {
        $(image_detail.config.delete_revision_action.element).click(function() {
            $('<div id="dialog-confirm" title="' +
              image_detail.config.delete_revision_action.dialog.title +
              '"></div>')
                .html('\
                        <p>\
                            <span class="ui-icon ui-icon-alert"\
                                  style="float:left; margin:0 7px 20px 0;">\
                            </span>' + image_detail.config.delete_revision_action.dialog.body + '\
                        </p>')
                .dialog({
                    resizable: false,
                    height: image_detail.config.delete_revision_action.dialog.height,
                    modal: true,
                    buttons: [
                        {
                            text: 'OK',
                            click: function() {
                                $(this).dialog('close');
                                window.location = image_detail.config.delete_revision_action.url + image_detail.globals.revision_id;
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            click: function() {
                                $(this).dialog('close');
                            }
                        }
                    ]
                });

            return false;
        });
    },

    setup_delete_original: function() {
        $(image_detail.config.delete_original_action.element).click(function() {
            $('<div id="dialog-confirm" title="' +
              image_detail.config.delete_original_action.dialog.title +
              '"></div>')
                .html('\
                        <p>\
                            <span class="ui-icon ui-icon-alert"\
                                  style="float:left; margin:0 7px 20px 0;">\
                            </span>' + image_detail.config.delete_original_action.dialog.body + '\
                        </p>')
                .dialog({
                    resizable: false,
                    height: image_detail.config.delete_original_action.dialog.height,
                    modal: true,
                    buttons: [
                        {
                            text: 'OK',
                            click: function() {
                                $(this).dialog('close');
                                window.location = image_detail.config.delete_original_action.url + image_detail.globals.image_id;
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            click: function() {
                                $(this).dialog('close');
                            }
                        }
                    ]
                });

            return false;
        });
    },

    setup_follow: function() {
        $(image_detail.config.follow_action.element).live('click', function() {
            var follow_a = $(this);
            var span = follow_a.parent();

            $('<div id="dialog-confirm"\
                    title="' + image_detail.config.follow_action.dialog.title + '">\
               </div>')
                .html('\
                        <p>\
                            <span class="ui-icon ui-icon-info" style="float:left; margin:0 7px 20px 0;"></span>\
                            ' + image_detail.config.follow_action.dialog.body + '\
                        </p>')
                .dialog({
                    resizable: false,
                    height: image_detail.config.follow_action.dialog.height,
                    modal: true,
                    buttons: [
                        {
                            text: 'OK',
                            click: function() {
                                var dlg = $(this)
                                $.ajax({
                                    url: image_detail.config.follow_action.url + image_detail.globals.image_username,
                                    success: function() {
                                        dlg.dialog('close');
                                        follow_a.remove();
                                        span.html('<a class="unfollow" href="#">' +
                                            image_detail.config.follow_action.stop_following +
                                            '</a>');
                                        span.parent().removeClass('icon-follow');
                                        span.parent().addClass('icon-unfollow');
                                    }
                                });
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            click: function() {
                                $(this).dialog('close');
                            }
                        }
                    ]
                });
                return false;
        });
    },

    setup_unfollow: function() {
        $(image_detail.config.unfollow_action.element).live('click', function() {
            var unfollow_a = $(this);
            var span = unfollow_a.parent();

            $('<div id="dialog-confirm"\
                    title="' + image_detail.config.unfollow_action.dialog.title + '">\
               </div>')
                .html('\
                        <p>\
                            <span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>\
                            ' + image_detail.config.unfollow_action.dialog.body + '\
                        </p>')
                .dialog({
                    resizable: false,
                    height: image_detail.config.unfollow_action.dialog.height,
                    modal: true,
                    buttons: [
                        {
                            text: 'OK',
                            click: function() {
                                var dlg = $(this)
                                $.ajax({
                                    url: image_detail.config.unfollow_action.url + image_detail.globals.image_username,
                                    success: function() {
                                        dlg.dialog('close');
                                        unfollow_a.remove();
                                        span.html('<a class="follow" href="#">' +
                                            image_detail.config.unfollow_action.follow +
                                            '</a>');
                                        span.parent().removeClass('icon-unfollow');
                                        span.parent().addClass('icon-follow');
                                    }
                                });
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            click: function() {
                                $(this).dialog('close');
                            }
                        }
                    ]
                });
            return false;
        });
    },

    setup_send_message: function() {
        $(image_detail.config.message_action.element).click(function() {
            var dlg = $('<div id="dialog-message" title="' + image_detail.config.message_action.dialog.title + '"></div>')
                .html('\
                    <div class="sided-main-content-popup">\
                    <form id="private-message" action="" method="post">\
                        ' + image_detail.config.message_action.form_html + '\
                        <div style="display:none;"><input type="hidden" id="csrfmiddlewaretoken" name="csrfmiddlewaretoken" value="' + image_detail.config.message_action.csrf_token + '" /></div> \
                        <input type="hidden" name="to_user" value="' + image_detail.globals.image_username  + '"/>\
                        <input id="send" class="button submit-button" type="button" value="' + image_detail.config.message_action.dialog.button  + '" />\
                    </form>\
                    </div>\
                ')
                .dialog({
                    resizable: true,
                    modal: true});

                $('form#private-message #send').one('click', function() {
                    $.post(image_detail.config.message_action.url,
                           $("form#private-message").serialize(),
                           function() {
                                dlg.dialog('close');
                           });
                });
            return false;
        });
    },

    setup_bring_to_attention: function() {
        $(image_detail.config.bring_to_attention_action.element).click(function() {
            var dlg = $('\
                <div id="dialog-attention" title="' + image_detail.config.bring_to_attention_action.dialog.title + '"></div>')
                .html('\
                    <div class="sided-main-content-popup">\
                    <p>\
                        ' + image_detail.config.bring_to_attention_action.dialog.body + '\
                    </p>\
                    <form id="attention" action="" method="post">\
                        ' + image_detail.config.bring_to_attention_action.form_html + '\
                        <input type="hidden" name="image_id" value="' + image_detail.globals.image_id  + '"/>\
                        <input id="submit"\
                               class="button submit-button"\
                               type="button"\
                               value="' + image_detail.config.bring_to_attention_action.dialog.button + '"/>\
                    </form>\
                    </div>\
                ')
                .dialog({
                    resizable: false,
                    height: image_detail.config.bring_to_attention_action.dialog.height,
                    modal: true});

            $('#id_user').autoSuggest('/autocomplete_usernames/', {
                asHtmlID: 'user',
                selectedItemProp: 'name',
                searchObjProps: 'name',
                preFill: '',
                selectedItemProp: 'name',
                selectedValuesProp: 'name',
                startText: image_detail.config.bring_to_attention_action.autocomplete.startText,
                emptyText: image_detail.config.bring_to_attention_action.autocomplete.emptyText
            });

            $('form#attention #submit').one('click', function() {
                $.post(image_detail.config.bring_to_attention_action.url,
                       $("form#attention").serialize(),
                       function() {
                            dlg.dialog('close');
                       });
            });
            return false;
        });
    },

    setup_image_request_additional_information: function() {
        var dlg = $(image_detail.config.image_request_additional_information_action.element).click(function() {
            $('<div id="dialog-confirm" title="' +
              image_detail.config.image_request_additional_information_action.dialog.title +
              '"></div>')
                .html('\
                        <p>\
                            <span class="ui-icon ui-icon-info"\
                                  style="float:left; margin:0 7px 20px 0;">\
                            </span>' + image_detail.config.image_request_additional_information_action.dialog.body + '\
                        </p>')
                .dialog({
                    resizable: false,
                    modal: true,
                    buttons: [
                        {
                            text: 'OK',
                            click: function() {
                                $(this).dialog('close');
                                $.ajax({
                                    url: image_detail.config.image_request_additional_information_action.url +
                                         image_detail.globals.image_id + '/',
                                    success: function() {
                                        dlg.dialog('close');
                                    }
                                });
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            click: function() {
                                $(this).dialog('close');
                            }
                        }
                    ]
                });
            return false;
        });
    },

    setup_image_request_fits: function() {
        var dlg = $(image_detail.config.image_request_fits_action.element).click(function() {
            $('<div id="dialog-confirm" title="' +
              image_detail.config.image_request_fits_action.dialog.title +
              '"></div>')
                .html('\
                        <p>\
                            <span class="ui-icon ui-icon-info"\
                                  style="float:left; margin:0 7px 20px 0;">\
                            </span>' + image_detail.config.image_request_fits_action.dialog.body + '\
                        </p>')
                .dialog({
                    resizable: false,
                    modal: true,
                    buttons: [
                        {
                            text: 'OK',
                            click: function() {
                                $(this).dialog('close');
                                $.ajax({
                                    url: image_detail.config.image_request_fits_action.url +
                                         image_detail.globals.image_id + '/',
                                    success: function() {
                                        dlg.dialog('close');
                                    }
                                });
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            click: function() {
                                $(this).dialog('close');
                            }
                        }
                    ]
                });
             return false;
        });
    },

    setup_view_more_subjects: function() {
        var $hidden = $('#more-subjects .hidden');
        var $more = $('#more-subjects .more');
        var $collapse = $('#more-subjects .collapse');

        $hidden.hide();
        $more.show();

        $more.find('a').click(function() {
            $hidden.slideDown();
            $more.hide();
            $collapse.show();
            return false;
        });          

        $collapse.find('a').click(function() {
            $hidden.slideUp();
            $collapse.hide();
            $more.show();
            return false;
        });          
    },

    init: function(image_id, revision_id, image_username, current_rating, config) {
        /* Init */
        image_detail.globals.image_id = image_id;
        image_detail.globals.revision_id = revision_id;
        image_detail.globals.image_username = image_username;
        image_detail.globals.rating.current = parseInt(current_rating);
        $.extend(true, image_detail.config, config);

        /* Rating */
        image_detail.setup_raty();

        /* Revisions */
        image_detail.setup_upload_revision();

        /* Delete */
        image_detail.setup_delete();
        image_detail.setup_delete_revision();
        image_detail.setup_delete_original();

        /* Following */
        image_detail.setup_follow();
        image_detail.setup_unfollow();

        /* Messaging */
        image_detail.setup_send_message();

        /* Bring to a user's attention */
        image_detail.setup_bring_to_attention();

        /* Requests */
        image_detail.setup_image_request_additional_information();
        image_detail.setup_image_request_fits();

        /* View more subjects */
        image_detail.setup_view_more_subjects();
    }
};

