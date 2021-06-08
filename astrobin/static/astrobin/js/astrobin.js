/**********************************************************************
 * Common
 *********************************************************************/
astrobin_common = {
    config: {
        image_detail_url: '/',
    },

    globals: {
        BREAKAGE_DATES: {
            COMMENTS_MARKDOWN: "2018-03-31T20:00:00"
        },

        requests: [],
        smart_ajax: $.ajax
    },

    utils: {
        getParameterByName: function (name) {
            name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
            var regexS = "[\\?&]" + name + "=([^&#]*)";
            var regex = new RegExp(regexS);
            var results = regex.exec(window.location.search);
            if (results == null)
                return "";
            else
                return decodeURIComponent(results[1].replace(/\+/g, " "));
        },

        checkParameterExists: function (parameter) {
            //Get Query String from url
            fullQString = window.location.search.substring(1);

            paramCount = 0;
            queryStringComplete = "?";

            if (fullQString.length > 0) {
                //Split Query String into separate parameters
                paramArray = fullQString.split("&");

                //Loop through params, check if parameter exists.
                for (i = 0; i < paramArray.length; i++) {
                    currentParameter = paramArray[i].split("=");
                    if (currentParameter[0] == parameter) //Parameter already exists in current url
                    {
                        return true;
                    }
                }
            }

            return false;
        },

        convertCurrency: function (amount, targetCurrency, precision) {
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
        },

        ckeditorOptions: function (context, language, placeholder) {
            if (!language) {
                language = 'en';
            }

            var options = {
                skin: 'minimalist',
                language: language,
                editorplaceholder: placeholder || '',
                disableNativeSpellChecker: false,
                extraPlugins: '' +
                    'ajax,' +
                    'autocomplete,' +
                    'autolink,' +
                    'basicstyles,' +
                    'bbcode,' +
                    'blockquote,' +
                    'button,' +
                    'clipboard,' +
                    'dialog,' +
                    'dialogui,' +
                    'divarea,' +
                    'editorplaceholder,' +
                    'enterkey,' +
                    'entities,' +
                    'fakeobjects,' +
                    'filebrowser,' +
                    'filetools,' +
                    'floatpanel,' +
                    'floatingspace,' +
                    'font,' +
                    'help,' +
                    'indent,' +
                    'indentlist,' +
                    'lineutils,' +
                    'link,' +
                    'list,' +
                    'magicline,' +
                    'maximize,' +
                    'mentions,' +
                    'menu,' +
                    'notification,' +
                    'notificationaggregator,' +
                    'panel,' +
                    'popup,' +
                    'SimpleLink,' +
                    'simpleuploads,' +
                    'smiley,' +
                    'sourcedialog,' +
                    'specialchar,' +
                    'table,' +
                    'textmatch,' +
                    'textwatcher,' +
                    'toolbar,' +
                    'undo,' +
                    'uploadwidget,' +
                    'widget,' +
                    'widgetselection,' +
                    'xml',
                startupFocus: true,
                disableObjectResizing: true,
                toolbar: [
                    {
                        name: 'help',
                        items: ['HelpButton']
                    },
                    {
                        name: 'document',
                        items: ['Sourcedialog', 'Maximize']
                    },
                    {
                        name: 'clipboard',
                        items: ['Cut', 'Copy', 'Paste', 'Undo', 'Redo']
                    },
                    {
                        name: 'basicstyles',
                        items: ['FontSize', 'Bold', 'Italic', 'Underline', 'Strike', 'RemoveFormat']
                    },
                    {
                        name: 'paragraph',
                        items: ['NumberedList', 'BulletedList', 'Blockquote']
                    },
                    {
                        name: 'links',
                        items: ['SimpleLink', 'Unlink']
                    },
                    {
                        name: 'insert',
                        items: ['addFile', 'addImage']
                    },
                    {
                        name: 'special',
                        items: ['SpecialChar', 'Smiley']
                    }
                ],
                filebrowserUploadUrl: '/json-api/common/ckeditor-upload/',
                mentions: [
                    {
                        feed: '/autocomplete_usernames/?q={encodedQuery}',
                        marker: '@',
                        pattern: new RegExp("\@[_a-zA-Z0-9À-ž ]{2,}"),
                        itemTemplate: '<li data-id="{id}">' +
                            '<img class="avatar" width="40" height="40" src="{avatar}" />' +
                            '<strong class="realname">{realName}</strong><span class="username">({username})</span>' +
                            '</li>',
                        outputTemplate: '<a href="' + window.location.origin + '/users/{username}/">@{displayName}</a><span>&nbsp;</span>',
                    },
                    {
                        feed: '/autocomplete_images/?q={encodedQuery}',
                        marker: '#',
                        pattern: new RegExp("\#[_a-zA-Z0-9À-ž ]{0,}"),
                        itemTemplate: '<li data-id="{id}">' +
                            '<img class="image" width="40" height="40" src="{thumbnail}" />' +
                            '<span class="title">{title}</span>' +
                            '</li>',
                        outputTemplate: '<br/><a href="' + window.location.origin + '{url}">' +
                            '<img src="{thumbnail}"/><br/>' +
                            '{title}' +
                            '</a><br/>',
                    }
                ],
                smiley_columns: 10,
                smiley_path: 'https://cdn.astrobin.com/static/astrobin/emoticons/',
                smiley_descriptions: [
                    'angel',
                    'angry-1',
                    'angry',
                    'arrogant',
                    'bored',
                    'confused',
                    'cool-1',
                    'cool',
                    'crying-1',
                    'crying-2',
                    'crying',
                    'cute',
                    'embarrassed',
                    'emoji',
                    'greed',
                    'happy-1',
                    'happy-2',
                    'happy-3',
                    'happy-4',
                    'happy-5',
                    'happy-6',
                    'happy-7',
                    'happy',
                    'in-love',
                    'kiss-1',
                    'kiss',
                    'laughing-1',
                    'laughing-2',
                    'laughing',
                    'muted',
                    'nerd',
                    'sad-1',
                    'sad-2',
                    'sad',
                    'scare',
                    'serious',
                    'shocked',
                    'sick',
                    'sleepy',
                    'smart',
                    'surprised-1',
                    'surprised-2',
                    'surprised-3',
                    'surprised-4',
                    'surprised',
                    'suspicious',
                    'tongue',
                    'vain',
                    'wink-1',
                    'wink'
                ],
                smiley_images: [
                    'angel.png',
                    'angry-1.png',
                    'angry.png',
                    'arrogant.png',
                    'bored.png',
                    'confused.png',
                    'cool-1.png',
                    'cool.png',
                    'crying-1.png',
                    'crying-2.png',
                    'crying.png',
                    'cute.png',
                    'embarrassed.png',
                    'emoji.png',
                    'greed.png',
                    'happy-1.png',
                    'happy-2.png',
                    'happy-3.png',
                    'happy-4.png',
                    'happy-5.png',
                    'happy-6.png',
                    'happy-7.png',
                    'happy.png',
                    'in-love.png',
                    'kiss-1.png',
                    'kiss.png',
                    'laughing-1.png',
                    'laughing-2.png',
                    'laughing.png',
                    'muted.png',
                    'nerd.png',
                    'sad-1.png',
                    'sad-2.png',
                    'sad.png',
                    'scare.png',
                    'serious.png',
                    'shocked.png',
                    'sick.png',
                    'sleepy.png',
                    'smart.png',
                    'surprised-1.png',
                    'surprised-2.png',
                    'surprised-3.png',
                    'surprised-4.png',
                    'surprised.png',
                    'suspicious.png',
                    'tongue.png',
                    'vain.png',
                    'wink-1.png',
                    'wink.png'
                ],
                specialChars: [
                    '!', '&quot;', '#', '$', '%', '&amp;', "'", '(', ')', '*', '+', '-', '.', '/',
                    '4', '5', '6', '7', '8', '9', ':', ';', '&lt;', '=', '&gt;', '?', '@', '[', ']', '^', '_', '`',
                    '{', '|', '}', '~', '&euro;', '&lsquo;', '&rsquo;', '&ldquo;', '&rdquo;', '&ndash;', '&mdash;',
                    '&iexcl;', '&cent;', '&pound;', '&curren;', '&yen;', '&brvbar;', '&sect;', '&uml;', '&copy;',
                    '&ordf;', '&laquo;', '&not;', '&reg;', '&macr;', '&deg;', '&sup2;', '&sup3;', '&acute;', '&micro;',
                    '&para;', '&middot;', '&cedil;', '&sup1;', '&ordm;', '&raquo;', '&frac14;', '&frac12;', '&frac34;',
                    '&iquest;', '&Agrave;', '&Aacute;', '&Acirc;', '&Atilde;', '&Auml;', '&Aring;', '&AElig;',
                    '&Ccedil;', '&Egrave;', '&Eacute;', '&Ecirc;', '&Euml;', '&Igrave;', '&Iacute;', '&Icirc;',
                    '&Iuml;', '&ETH;', '&Ntilde;', '&Ograve;', '&Oacute;', '&Ocirc;', '&Otilde;', '&Ouml;', '&times;',
                    '&Oslash;', '&Ugrave;', '&Uacute;', '&Ucirc;', '&Uuml;', '&Yacute;', '&THORN;', '&alpha;',
                    '&szlig;', '&agrave;', '&aacute;', '&acirc;', '&atilde;', '&auml;', '&aring;', '&aelig;',
                    '&ccedil;', '&egrave;', '&eacute;', '&ecirc;', '&euml;', '&igrave;', '&iacute;', '&icirc;',
                    '&iuml;', '&eth;', '&ntilde;', '&ograve;', '&oacute;', '&ocirc;', '&otilde;', '&ouml;', '&divide;',
                    '&oslash;', '&ugrave;', '&uacute;', '&ucirc;', '&uuml;', '&yacute;', '&thorn;', '&yuml;', '&OElig;',
                    '&oelig;', '&#372;', '&#374', '&#373', '&#375;', '&sbquo;', '&#8219;', '&bdquo;', '&hellip;',
                    '&trade;', '&#9658;', '&bull;', '&rarr;', '&rArr;', '&hArr;', '&diams;', '&asymp;'
                ],
                fontSize_sizes: "50%/50%;100%/100%;200%/200%",
                on: {
                    change: function () {
                        this.updateElement();
                    },
                    beforeCommandExec: function (event) {
                        // Show the paste dialog for the paste buttons and right-click paste
                        if (event.data.name === "paste") {
                            event.editor._.forcePasteDialog = true;
                        }

                        // Don't show the paste dialog for Ctrl+Shift+V
                        if (event.data.name === "pastetext" && event.data.commandData.from === "keystrokeHandler") {
                            event.cancel();
                        }
                    }
                }
            }

            switch (context) {
                case "forum":
                    options['height'] = 300;
                    options['on']['instanceReady'] = function () {
                        $(".post-form-loading").hide();
                        $(".post-form").show();
                    };
                    break;
                case "comments":
                    options['height'] = 250;
                    break;
                case "private-message":
                    options['height'] = 300;
                    break;
                default:
                    console.error("Unhandled CkEditor options context");
                    return {}
            }

            return options;
        },

        BBCodeToHtml: function (code, context, language) {
            var fragment = CKEDITOR.htmlParser.fragment.fromBBCode(code);
            var writer = new CKEDITOR.htmlParser.basicWriter();
            var bbcodeFilter = new CKEDITOR.htmlParser.filter();

            bbcodeFilter.addRules({
                elements: {
                    blockquote: function (element) {
                        var quoted = new CKEDITOR.htmlParser.element('div');
                        quoted.children = element.children;
                        element.children = [quoted];
                        var citeText = element.attributes.cite;
                        if (citeText) {
                            var cite = new CKEDITOR.htmlParser.element('cite');
                            cite.add(new CKEDITOR.htmlParser.text(citeText.replace(/^"|"$/g, '')));
                            delete element.attributes.cite;
                            element.children.unshift(cite);
                        }
                    },
                    span: function (element) {
                        var bbcode;
                        if ((bbcode = element.attributes.bbcode)) {
                            if (bbcode === 'img') {
                                element.name = 'img';
                                element.attributes.src = element.children[0].value;
                                element.children = [];
                            } else if (bbcode === 'email') {
                                element.name = 'a';
                                element.attributes.href = 'mailto:' + element.children[0].value;
                            }

                            delete element.attributes.bbcode;
                        }
                    },
                    ol: function (element) {
                        if (element.attributes.listType) {
                            if (element.attributes.listType !== 'decimal')
                                element.attributes.style = 'list-style-type:' + element.attributes.listType;
                        } else {
                            element.name = 'ul';
                        }

                        delete element.attributes.listType;
                    },
                    a: function (element) {
                        if (!element.attributes.href)
                            element.attributes.href = element.children[0].value;
                    },
                    smiley: function (element) {
                        element.name = 'img';

                        var editorConfig = astrobin_common.utils.ckeditorOptions(context, language);

                        var description = element.attributes.desc,
                            image = editorConfig.smiley_images[
                                CKEDITOR.tools.indexOf(editorConfig.smiley_descriptions, description)],
                            src = CKEDITOR.tools.htmlEncode(editorConfig.smiley_path + image);

                        element.attributes = {
                            src: src,
                            'data-cke-saved-src': src,
                            class: 'smiley',
                            title: description,
                            alt: description
                        };
                    }
                }
            });

            fragment.writeHtml(writer, bbcodeFilter);
            return writer.getHtml(true);
        }
    },

    init_ajax_csrf_token: function () {
        $(document).ajaxSend(function (event, xhr, settings) {
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

    setup_gear_popovers: function () {
        $('.gear-popover-label').each(function () {
            $(this).qtip({
                position: {
                    viewport: $(window)
                },
                show: "click",
                hide: "unfocus",
                style: {
                    tip: {
                        width: 16,
                        height: 16,
                        offset: 8
                    }
                },
                content: {
                    text: "...",
                    ajax: {
                        loading: false,
                        url: $(this).attr('data-load'),
                        type: 'GET',
                        dataType: 'json',
                        timeout: 5000,
                        success: function (data, status) {
                            this.set('content.text', data.html);
                        }
                    }
                }
            });
        });
    },

    setup_subject_popovers: function () {
        $('.subject-popover').each(function () {
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
                        url: $(this).attr('data-load'),
                        type: 'GET',
                        dataType: 'json',
                        timeout: 5000,
                        success: function (data, status) {
                            this.set('content.text', data.html);
                        }
                    }
                }
            });
        });
    },

    setup_user_popovers: function () {
        $('#navbar-user-scores').each(function () {
            $(this).qtip({
                position: {
                    my: "top center",
                    at: "bottom center"
                },
                show: {
                    solo: true,
                    delay: 500
                },
                hide: {
                    fixed: true,
                    delay: 200
                },
                content: {
                    text: function () {
                        return $("#user-scores-popover");
                    }
                }
            });
        });

        $('.user-popover').each(function () {
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
                        url: $(this).attr('data-load'),
                        type: 'GET',
                        dataType: 'json',
                        timeout: 5000,
                        success: function (data, status) {
                            this.set('content.text', data.html);
                        }
                    }
                }
            });
        });
    },

    init_timestamps: function() {
        $('abbr.timestamp').each(function (index, element) {
            var $el = $(element);
            var datetime = new Date(0);
            var locale = window.navigator.userLanguage || window.navigator.language;
            var now = new Date()

            datetime.setUTCSeconds($el.data('epoch') / 1000);

            $el.attr('title', datetime.toISOString());

            if (datetime < now && now - datetime < 1000 * 60 * 60 * 24 * 30) {
                $el.text(datetime.toLocaleString(locale));
                $el.timeago();
            } else {
                $el.text(datetime.toLocaleDateString(locale));
                $el.attr('title', datetime.toLocaleTimeString(locale));
            }
        });
    },

    init_page_loading_indicator: function() {
        $('a:not(.bb-quote-link)').live('click', function (event) {
            var url = $(this).attr('href');

            if (!url) {
                return;
            }

            // Skip external links.
            if (url.indexOf('astrobin.com') === -1 && url.indexOf('localhost') === -1 && url[0] !== '/') {
                return;
            }

            // Skip endless pagination.
            if ($(event.target).hasClass('endless_more')) {
                return;
            }

            var target = $(this).attr('target');
            var $pageLoader = $('#page-loading-indicator');
            var $pageLoaderBackdrop = $('#page-loading-indicator-backdrop');

            if (!target) {
                target = '_self';
            }

            $pageLoaderBackdrop.css('width', '100%');
            $pageLoaderBackdrop.css('height', '100%');
            $pageLoaderBackdrop.css('opacity', .65);

            $pageLoader.css('width', '100%');
            $pageLoader.css('height', '100%');
            $pageLoader.css('opacity', 1);

            window.open(url, target);
            event.preventDefault();
        });
    },

    get_notifications_count: function() {
        $.ajax({
            url: '/api/v2/notifications/notification/get_unread_count/',
            method: 'GET',
            dataType: 'json',
            timeout: 5000,
            success: function(data) {
                $('#notifications-count').text(data).show();
            }
        });
    },

    init: function (config) {
        /* Init */
        $.extend(true, astrobin_common.config, config);

        $('.dropdown-toggle').dropdown();
        $('.carousel').carousel();
        $('.nav-tabs').tab();
        $('[rel=tooltip]').tooltip();
        $('.collapse.in').collapse();

        // date and time pickers
        $('input').filter('.timepickerclass').timepicker({});
        $('input').filter('.datepickerclass').datepicker({
            dateFormat: 'yy-mm-dd',
            changeMonth: true,
            changeYear: true
        });

        astrobin_common.init_timestamps();
        astrobin_common.init_page_loading_indicator();

        if (window.innerWidth >= 980) {
            $("select:not([multiple])").select2({theme: "flat"});
        }

        $("select[multiple]:not(.select2)").not('*[name="license"]').multiselect({
            searchable: false,
            dividerLocation: 0.5
        });

        $("select.select2").select2({
            theme: "flat"
        });

        astrobin_common.init_ajax_csrf_token();
        astrobin_common.get_notifications_count();
    }
};

/**********************************************************************
 * Stats
 *********************************************************************/
astrobin_stats = {
    config: {},

    globals: {
        previousPoint: null
    },

    /* Private */
    _showTooltip: function (x, y, contents) {
        $('<div id="stats-tooltip">' + contents + '</div>').css({
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
    enableTooltips: function (plot) {
        $(plot).bind("plothover", function (event, pos, item) {
            if (item) {
                if (astrobin_stats.globals.previousPoint != item.dataIndex) {
                    astrobin_stats.globals.previousPoint = item.dataIndex;

                    $("#stats-tooltip").remove();
                    var x = item.datapoint[0].toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    astrobin_stats._showTooltip(item.pageX, item.pageY, y);
                }
            } else {
                $("#stats-tooltip").remove();
                astrobin_stats.globals.previousPoint = null;
            }
        });
    },

    plot: function (id, url, timeout, data, options) {
        $.ajax({
            url: url,
            method: 'GET',
            dataType: 'json',
            timeout: timeout,
            cache: false,
            success: function (series) {
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

    plot_pie: function (id, url, timeout, data, options) {
        $.ajax({
            url: url,
            method: 'GET',
            dataType: 'json',
            timeout: timeout,
            cache: false,
            success: function (series) {
                $.plot(
                    $(id),
                    series['flot_data'],
                    series['flot_options']);
            }
        });
    },


    init: function (config) {
        /* Init */
        $.extend(true, astrobin_stats.config, config);
    }
};
