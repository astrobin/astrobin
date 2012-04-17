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

        /* Requests */
        requests_base_url          : '/activity/?id=request_',
        requests_element_empty     : 'ul#request-feed li#empty',
        requests_element_image     : 'img#requests',
        requests_element_ul        : 'ul#request-feed',
        request_detail_url         : '/requests/detail/',

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
        }
    },

    globals: {
        requests: [],
        smart_ajax: $.ajax,
        current_username: ''
    },

    utils: {
       getParameterByName: function(name) {
           name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
           var regexS = "[\\?&]" + name + "=([^&#]*)";
           var regex = new RegExp(regexS);
           var results = regex.exec(window.location.search);
           if(results == null)
               return "";
           else
               return decodeURIComponent(results[1].replace(/\+/g, " "));
       },
       checkParameterExists: function(parameter) {
           //Get Query String from url
           fullQString = window.location.search.substring(1);

           paramCount = 0;
           queryStringComplete = "?";

           if(fullQString.length > 0)
           {
               //Split Query String into separate parameters
               paramArray = fullQString.split("&");

               //Loop through params, check if parameter exists.  
               for (i=0;i<paramArray.length;i++)
               {
                   currentParameter = paramArray[i].split("=");
                   if(currentParameter[0] == parameter) //Parameter already exists in current url
                   {
                       return true;
                   }
               }
           }

           return false;
       }
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
                $(common.config.notifications_element_ul)
                    .prepend('<li class="unread">'+json['message']+'</li>');

                /* Start the next long poll. */
                common.listen_for_notifications(username, last_modified, etag);
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
            common.listen_for_requests(username, '', '');
        }, 1000);
    },

    clearText: function(field) {
        if (field.defaultValue == field.value) field.value = '';
        else if (field.value == '') field.value = field.defaultValue;
    },

    showHideAdvancedSearch: function() {
    },

    init_ajax_csrf_token: function() {
        $(document).ajaxSend(function(event, xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            function sameOrigin(url) {
                // url could be relative or scheme relative or absolute
                var host = document.location.host; // host + port
                var protocol = document.location.protocol;
                var sr_origin = '//' + host;
                var origin = protocol + sr_origin;
                // Allow absolute or scheme relative URLs to same origin
                return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
                    (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
                    // or any other URL that isn't scheme relative or absolute i.e relative.
                    !(/^(\/\/|http:|https:).*/.test(url));
            }

            function safeMethod(method) {
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            }

            if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        });
    },

    setup_follow: function() {
        $(common.config.follow_action.element).live('click', function() {
            var follow_a = $(this);

            $('<div id="dialog-confirm"\
                    title="' + common.config.follow_action.dialog.title + '">\
               </div>')
                .html('\
                        <p>\
                            <span class="ui-icon ui-icon-info" style="float:left; margin:0 7px 20px 0;"></span>\
                            ' + common.config.follow_action.dialog.body + '\
                        </p>')
                .dialog({
                    resizable: false,
                    height: common.config.follow_action.dialog.height,
                    modal: true,
                    buttons: [
                        {
                            text: 'OK',
                            class: 'btn btn-primary',
                            click: function() {
                                var dlg = $(this)
                                $.ajax({
                                    url: common.config.follow_action.url + common.globals.current_username,
                                    dataType: 'json',
                                    timeout: 5000,
                                    cache: false,
                                    success: function() {
                                        dlg.dialog('close');
                                        follow_a.html('<i class="icon-unfollow"></i> ' + common.config.follow_action.stop_following);
                                        follow_a.removeClass('follow').addClass('unfollow');
                                    },
                                    error: function(jqXHR, textStatus, errorThrown) {
                                    }
                                });
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            class: 'btn',
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
        $(common.config.unfollow_action.element).live('click', function() {
            var unfollow_a = $(this);

            $('<div id="dialog-confirm"\
                    title="' + common.config.unfollow_action.dialog.title + '">\
               </div>')
                .html('\
                        <p>\
                            <span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>\
                            ' + common.config.unfollow_action.dialog.body + '\
                        </p>')
                .dialog({
                    resizable: false,
                    height: common.config.unfollow_action.dialog.height,
                    modal: true,
                    buttons: [
                        {
                            text: 'OK',
                            class: 'btn btn-primary',
                            click: function() {
                                var dlg = $(this)
                                $.ajax({
                                    url: common.config.unfollow_action.url + common.globals.current_username,
                                    dataType: 'json',
                                    timeout: 5000,
                                    cache: false,
                                    success: function() {
                                        dlg.dialog('close');
                                        unfollow_a.html('<i class="icon-follow"></i> ' + common.config.unfollow_action.follow);
                                        unfollow_a.removeClass('unfollow').addClass('follow');
                                    },
                                    error: function(jqXHR, textStatus, errorThrown) {
                                    }
                                });
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            class: 'btn',
                            click: function() {
                                $(this).dialog('close');
                            }
                        }
                    ]
                });
            return false;
        });
    },

    setup_gear_popovers: function(follow_text, unfollow_text) {
        $('.gear-popover').each(function() {
            $(this).qtip({
                position: {
                    my: "left center",
                    at: "right center"
                },
                show: {
                    solo: true
                },
                hide: {
                    fixed: true,
                    delay: 1000
                },
                content: {
                    text: "...",
                    ajax: {
                        loading: false,
                        url:  $(this).attr('data-load'),
                        type: 'GET',
                        dataType: 'json',
                        success: function(data, status) {
                            this.set('content.text', data.html);
                        }
                    }
                }
            });
        });

        $('.follow-gear').live('click', function() {
            var $link = $(this);
            $.ajax({
                url: $link.attr('href'),
                timeout: 5000,
                cache: false,
                dataType: 'json',
                beforeSend: function() {
                    $link.text("...");
                    $link.addClass('disabled');
                },
                success: function(data) {
                    $link.text(unfollow_text);
                    $link.attr('href', '/unfollow_gear/' + $link.attr('data-gear') + '/');
                    $link.removeClass('follow-gear').addClass('unfollow-gear');
                    $link.removeClass('disabled');
                },
                error: function() {
                }
            });

            return false;
        });

        $('.unfollow-gear').live('click', function() {
            var $link = $(this);
            $.ajax({
                url: $link.attr('href'),
                timeout: 5000,
                cache: false,
                dataType: 'json',
                beforeSend: function() {
                    $link.text("...");
                    $link.addClass('disabled');
                },
                success: function(data) {
                    $link.text(follow_text);
                    $link.attr('href', '/follow_gear/' + $link.attr('data-gear') + '/');
                    $link.removeClass('unfollow-gear').addClass('follow-gear');
                    $link.removeClass('disabled');
                },
                error: function() {
                    alert("error");
                }
            });

            return false;
        });
    },

    setup_subject_popovers: function(follow_text, unfollow_text) {
        $('.subject-popover').each(function() {
            $(this).qtip({
                position: {
                    my: "left center",
                    at: "right center"
                },
                show: {
                    solo: true
                },
                hide: {
                    fixed: true,
                    delay: 1000
                },
                content: {
                    text: "...",
                    ajax: {
                        loading: false,
                        url:  $(this).attr('data-load'),
                        type: 'GET',
                        dataType: 'json',
                        success: function(data, status) {
                            this.set('content.text', data.html);
                        }
                    }
                }
            });
        });

        $('.follow-subject').live('click', function() {
            var $link = $(this);
            $.ajax({
                url: $link.attr('href'),
                timeout: 5000,
                cache: false,
                dataType: 'json',
                beforeSend: function() {
                    $link.text("...");
                    $link.addClass('disabled');
                },
                success: function(data) {
                    $link.text(unfollow_text);
                    $link.attr('href', '/unfollow_subject/' + $link.attr('data-subject') + '/');
                    $link.removeClass('follow-subject').addClass('unfollow-subject');
                    $link.removeClass('disabled');
                },
                error: function() {
                }
            });

            return false;
        });

        $('.unfollow-subject').live('click', function() {
            var $link = $(this);
            $.ajax({
                url: $link.attr('href'),
                timeout: 5000,
                cache: false,
                dataType: 'json',
                beforeSend: function() {
                    $link.text("...");
                    $link.addClass('disabled');
                },
                success: function(data) {
                    $link.text(follow_text);
                    $link.attr('href', '/follow_subject/' + $link.attr('data-subject') + '/');
                    $link.removeClass('unfollow-subject').addClass('follow-subject');
                    $link.removeClass('disabled');
                },
                error: function() {
                    alert("error");
                }
            });

            return false;
        });
    },

    init: function(current_username, config) {
        /* Init */
        common.globals.current_username = current_username;
        $.extend(true, common.config, config);

        /* Following */
        common.setup_follow();
        common.setup_unfollow();
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
            uploadingText: '',
            width: 300
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
            half: false,
            showHalf: true,
            hintList: image_detail.config.rating.hint_list,
            space: false,
            size: 24,
            starHalf: 'star-half-big.png',
            starOff:  'star-off-big.png',
            starOn:   'star-on-big.png',
            click: function(score) {
                $.ajax({
                    url: image_detail.config.rating.rate_url + image_detail.globals.image_id + '/' + score + '/',
                    timeout: 5000,
                    success: function(data, textStatus, XMLHttpRequst) {
                        $.ajax({
                            url: image_detail.config.rating.get_rating_url + image_detail.globals.image_id + '/',
                            timeout: 5000,
                            dataType: 'json',
                            success: function(data) {
                                var rating = data.rating
                                $(image_detail.config.rating.element).raty('start', rating);
                                $(image_detail.config.rating.element).raty('readOnly', true);
                                $(image_detail.config.rating.element).raty('fixHint');
                                $('.rating-current .rating').text(rating);
                                $('.rating-current .number').text(parseInt($('.rating-current .number').text()) + 1);
                            },
                            error: function(XMLHttpRequest, textStatus, errorThrown) {
                            }
                        });
                    },
                    error: function(XMLHttpRequest, textStatus, errorThrown) {
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
                    <div class="upload-revision">\
                    <p>\
                        ' + image_detail.config.upload_revision_action.dialog.body + '\
                    </p>\
                    <form id="upload-revision" action="' + image_detail.config.upload_revision_action.url + '" method="post" enctype="multipart/form-data">\
                        ' + image_detail.config.upload_revision_action.form_html + '\
                        <div style="display:none;"><input type="hidden" id="csrfmiddlewaretoken" name="csrfmiddlewaretoken" value="' + image_detail.config.upload_revision_action.csrf_token + '" /></div> \
                        <input type="hidden" name="image_id" value="' + image_detail.globals.image_id  + '"/>\
                    </form>\
                    <div style="text-align:center" class="progressbar"><img src="/static/images/loading-bar.gif" alt=""/></div>\
                    </div>\
                ')
                .dialog({
                    width: image_detail.config.upload_revision_action.width,
                    resizable: false,
                    modal: true});

            $('input:file').uniform(
               {fileDefaultText: image_detail.config.upload_revision_action.fileDefaultText,
                fileBtnText: image_detail.config.upload_revision_action.fileBtnText
               }
            );
            $('form#upload-revision').live('submit', function() {
                form = $(this);
                progressbar = form.parent().find('.progressbar');

                form.hide();
                progressbar.show();

                return true;
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
                            class: 'btn btn-primary',
                            click: function() {
                                $(this).dialog('close');
                                window.location = image_detail.config.delete_action.url + image_detail.globals.image_id;
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            class: 'btn',
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
                            class: 'btn btn-primary',
                            click: function() {
                                $(this).dialog('close');
                                window.location = image_detail.config.delete_revision_action.url + image_detail.globals.revision_id;
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            class: 'btn',
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
                            class: 'btn btn-primary',
                            click: function() {
                                $(this).dialog('close');
                                window.location = image_detail.config.delete_original_action.url + image_detail.globals.image_id;
                            }
                        },
                        {
                            text: $.i18n._('Cancel'),
                            class: 'btn',
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

    setup_plot_overlay: function() {
        $('img.plot-overlay').mouseover(function() {
            $(this).animate({opacity: 1.0});
        }).mouseout(function() {
            $(this).animate({opacity: 0.0});
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

        /* View more subjects */
        image_detail.setup_view_more_subjects();

        /* Plot overlay mouse-over */
        image_detail.setup_plot_overlay();
    }
};

/**********************************************************************
 * Stats
 *********************************************************************/
var stats = {
    config: {
    },

    globals: {
        previousPoint: null
    },

    /* Private */
    _showTooltip: function(x, y, contents) {
        $('<div id="stats-tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y - 25,
            left: x,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            color: '#000',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    },

    /* Public */
    enableTooltips: function(plot) {
        $(plot).bind("plothover", function (event, pos, item) {
            if (item) {
                if (stats.globals.previousPoint != item.dataIndex) {
                    stats.globals.previousPoint = item.dataIndex;

                    $("#stats-tooltip").remove();
                    var x = item.datapoint[0].toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    stats._showTooltip(item.pageX, item.pageY, y);
                }
            }
            else {
                $("#stats-tooltip").remove();
                stats.globals.previousPoint = null;
            }
        });
    },

    plot: function(id, url, timeout, data, options) {
        $.ajax({
            url: url,
            method: 'GET',
            dataType: 'json',
            timeout: timeout,
            success: function(series) {
                $.plot(
                    $(id),
                    [{
                        label: series['flot_label'],
                        color: "#CC4B2E",
                        data: series['flot_data']
                    }],
                    series['flot_options']);
            }
        });
    },

    init: function(config) {
        /* Init */
        $.extend(true, stats.config, config);
    }
};

