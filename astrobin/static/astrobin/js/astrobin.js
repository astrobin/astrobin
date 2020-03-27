/**********************************************************************
 * Common
 *********************************************************************/
astrobin_common = {
    config: {
        image_detail_url           : '/',

        /* Notifications */
        notifications_base_url     : '/activity?id=notification_',
        notifications_element_empty: 'ul#notification-feed li#empty',
        notifications_element_image: 'img#notifications',
        notifications_element_ul   : 'ul#notification-feed'
    },

    globals: {
        BREAKAGE_DATES: {
            COMMENTS_MARKDOWN: "2018-03-31T20:00:00"
        },

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
               for (i=0;i<paramArray.length;i++) {
                   currentParameter = paramArray[i].split("=");
                   if (currentParameter[0] == parameter) //Parameter already exists in current url
                   {
                       return true;
                   }
               }
           }

            return false;
        },

        convertCurrency: function(amount, targetCurrency, precision) {
            // CHF is the base.
            var rates = {
                USD: 1.03,
                EUR: 0.93,
                GBP: 0.78
            };

            if (precision === undefined) {
                precision = 2;
            }

            var converted = parseInt(amount, 10) * rates[targetCurrency];
            return (Math.round(converted * 100) / 100).toFixed(precision);
        }
    },

    listen_for_notifications: function(username, last_modified, etag) {
        astrobin_common.globals.smart_ajax({
            'beforeSend': function(xhr) {
                xhr.setRequestHeader("If-None-Match", etag);
                xhr.setRequestHeader("If-Modified-Since", last_modified);
            },
            url: astrobin_common.config.notifications_base_url + username,
            dataType: 'text',
            type: 'get',
            cache: 'false',
            success: function(data, textStatus, xhr) {
                etag = xhr.getResponseHeader('Etag');
                last_modified = xhr.getResponseHeader('Last-Modified');

                json = jQuery.parseJSON(data);

                $(astrobin_common.config.notifications_element_empty).remove();
                $(astrobin_common.config.notifications_element_ul)
                    .prepend('<li class="unread">'+json['message']+'</li>');

                /* Start the next long poll. */
                astrobin_common.listen_for_notifications(username, last_modified, etag);
            }
        });
    },

    start_listeners: function(username) {
        astrobin_common.globals.smart_ajax = function(settings) {
            // override complete() operation
            var complete = settings.complete;
            settings.complete = function(xhr) {
                if (xhr) {
                    // xhr may be undefined, for example when downloading JavaScript
                    for (var i = 0, len = astrobin_common.globals.requests.length; i < len; ++i) {
                        if (astrobin_common.globals.requests[i] == xhr) {
                            // drop completed xhr from list
                            astrobin_common.globals.requests.splice(i, 1);
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
                astrobin_common.globals.requests.push(r);
            }
            return r;
        };

        setTimeout(function() {
            astrobin_common.listen_for_notifications(username, '', '');
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

    setup_gear_popovers: function() {
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
                        timeout: 5000,
                        success: function(data, status) {
                            this.set('content.text', data.html);
                            window.loadAstroBinImages(data.html);
                        }
                    }
                }
            });
        });
    },

    setup_subject_popovers: function() {
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
                        timeout: 5000,
                        success: function(data, status) {
                            this.set('content.text', data.html);
                        }
                    }
                }
            });
        });
    },

    setup_user_popovers: function() {
        $('.user-popover').each(function() {
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
                        timeout: 5000,
                        success: function(data, status) {
                            this.set('content.text', data.html);
                        }
                    }
                }
            });
        });
    },

    mark_notification_as_read: function(notification_id) {
        $.ajax({
            url: '/persistent_messages/mark_read/' + notification_id + '/',
            dataType: 'json',
            success: function() {
                var $row = $('#notifications-modal tr[data-id=' + notification_id + ']'),
                    $check_mark = $row.find('td.notification-mark-as-read a'),
                    $count_badge = $('#notifications_count'),
                    count;

                $row.removeClass('notification-unread');
                $row.addClass('notification-read');
                $check_mark.remove();

                if ($count_badge.length > 0) {
                    count = parseInt($count_badge.text());
                    if (count == 1) {
                        $count_badge.remove();
                    } else {
                        $count_badge.text(count - 1);
                    }
                }

                $.ajax({
                    url: '/notifications/clear-template-cache/',
                    type: 'POST',
                    dataType: 'json',
                    timeout: 1000
                });
            }
        });
    },

    init: function(current_username, config) {
        /* Init */
        astrobin_common.globals.current_username = current_username;
        $.extend(true, astrobin_common.config, config);

        $('.dropdown-toggle').dropdown();
        $('.carousel').carousel();
        $('.nav-tabs').tab();
        $('[rel=tooltip]').tooltip();
        $('.collapse.in').collapse();

        // date and time pickers
        $('input').filter('.timepickerclass').timepicker({});
        $('input').filter('.datepickerclass').datepicker({'dateFormat':'yy-mm-dd'});

        $('abbr.timeago').timeago();

        $("select[multiple]").not('*[name="license"]').multiselect({
            searchable: false,
            dividerLocation: 0.5
        });

        $('textarea.bocde').wysibb({
            buttons: "bold,italic,underline,|,img,link,|,bullist,numlist,|,code"
        });

        astrobin_common.init_ajax_csrf_token();
   }
};

/**********************************************************************
 * Stats
 *********************************************************************/
astrobin_stats = {
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
                if (astrobin_stats.globals.previousPoint != item.dataIndex) {
                    astrobin_stats.globals.previousPoint = item.dataIndex;

                    $("#stats-tooltip").remove();
                    var x = item.datapoint[0].toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    astrobin_stats._showTooltip(item.pageX, item.pageY, y);
                }
            }
            else {
                $("#stats-tooltip").remove();
                astrobin_stats.globals.previousPoint = null;
            }
        });
    },

    plot: function(id, url, timeout, data, options) {
        $.ajax({
            url: url,
            method: 'GET',
            dataType: 'json',
            timeout: timeout,
            cache: false,
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

    plot_pie: function(id, url, timeout, data, options) {
        $.ajax({
            url: url,
            method: 'GET',
            dataType: 'json',
            timeout: timeout,
            cache: false,
            success: function(series) {
                $.plot(
                    $(id),
                    series['flot_data'],
                    series['flot_options']);
            }
        });
    },


    init: function(config) {
        /* Init */
        $.extend(true, astrobin_stats.config, config);
    }
};
