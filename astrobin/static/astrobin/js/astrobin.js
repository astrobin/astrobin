/*****************************************************************
 * Utility prototype overrides
 *****************************************************************/

String.prototype.format = String.prototype.format ||
    function () {
        "use strict";
        let str = this.toString();
        if (arguments.length) {
            const t = typeof arguments[0];
            let key;
            const args = ("string" === t || "number" === t) ?
                Array.prototype.slice.call(arguments)
                : arguments[0];

            for (key in args) {
                str = str.replace(new RegExp("\\{" + key + "\\}", "gi"), args[key]);
            }
        }

        return str;
    };

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
        isTouchDevice() {
            return (('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || (navigator.msMaxTouchPoints > 0));
        },

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

            const options = {
                skin: 'minimalist',
                language: language,
                editorplaceholder: placeholder || '',
                disableNativeSpellChecker: false,
                extraPlugins: '' +
                    'ajax,' +
                    'autocomplete,' +
                    'autogrow,' +
                    'autolink,' +
                    'basicstyles,' +
                    'bbcode,' +
                    'blockquote,' +
                    'button,' +
                    'clipboard,' +
                    'codesnippet,' +
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
                        items: ['addFile', 'addImage', 'CodeSnippet']
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
                codeSnippet_languages: {
                    bash: 'Bash',
                    coffeescript: 'CoffeeScript',
                    cpp: 'C++',
                    cs: 'C#',
                    css: 'CSS',
                    diff: 'Diff',
                    html: 'HTML',
                    java: 'Java',
                    javascript: 'JavaScript',
                    json: 'JSON',
                    objectivec: 'Objective-C',
                    perl: 'Perl',
                    php: 'PHP',
                    python: 'Python',
                    ruby: 'Ruby',
                    sql: 'SQL',
                    vbscript: 'VBScript',
                    xhtml: 'XHTML',
                    xml: 'XML'
                },
                on: {
                    change: function () {
                        this.updateElement();
                    },
                    "simpleuploads.finishedUpload": function () {
                        this.updateElement()
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
            };

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
                case "forum-notice":
                case "image-description":
                    options['height'] = 300;
                    break;
                default:
                    console.error("Unhandled CkEditor options context");
                    return {}
            }

            // Bump this anytime a plugin or other CKEDITOR resource is updated.
            CKEDITOR.timestamp = "2023-08-01";

            return options;
        },

        BBCodeToHtml: function (code, context, language) {
            const fragment = CKEDITOR.htmlParser.fragment.fromBBCode(code);
            const writer = new CKEDITOR.htmlParser.basicWriter();
            const bbcodeFilter = new CKEDITOR.htmlParser.filter();

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
                    },
                    img: function (element) {
                        const src = element.attributes.src;

                        if (src && src.indexOf('/ckeditor-files/') > 0) {
                            const urlPath = new URL(src, window.location.origin).pathname.slice(1);

                            // Synchronous AJAX call to get the thumbnail URL
                            let thumbnailSrc;
                            $.ajax({
                                url: `/json-api/common/ckeditor-upload/?path=${encodeURIComponent(urlPath)}`,
                                async: false,  // Make the request synchronous
                                success: function(data) {
                                    thumbnailSrc = data.thumbnail;
                                },
                                error: function() {
                                    console.error('Error fetching thumbnail.');
                                }
                            });

                            if (thumbnailSrc) {
                                const anchor = new CKEDITOR.htmlParser.element('a');
                                anchor.attributes.href = src;
                                anchor.attributes['data-fancybox'] = '';
                                anchor.attributes.class = 'fancybox'

                                const thumbnailImg = new CKEDITOR.htmlParser.element('img');
                                thumbnailImg.attributes.src = thumbnailSrc;

                                // Add the img element to the anchor
                                anchor.add(thumbnailImg);

                                // Replace the original img element with the new anchor element
                                element.replaceWith(anchor);
                            }
                        }
                    }
                }
            });

            fragment.writeHtml(writer, bbcodeFilter);
            return writer.getHtml(true);
        }
    },

    get_cookie: function (name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    init_ajax_csrf_token: function () {
        $(document).ajaxSend(function (event, xhr, settings) {
            function sameOrigin(url) {
                // url could be relative or scheme relative or absolute
                var host = document.location.host; // host + port
                var protocol = document.location.protocol;
                var sr_origin = '//' + host;
                var origin = protocol + sr_origin;
                // Allow absolute or scheme relative URLs to same origin
                return (url === origin || url.slice(0, origin.length + 1) === origin + '/') ||
                    (url === sr_origin || url.slice(0, sr_origin.length + 1) === sr_origin + '/') ||
                    // or any other URL that isn't scheme relative or absolute i.e relative.
                    !(/^(\/\/|http:|https:).*/.test(url));
            }

            function safeMethod(method) {
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            }

            if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
                xhr.setRequestHeader("X-CSRFToken", astrobin_common.get_cookie('csrftoken'));
            }
        });
    },

    setup_gear_popovers: function () {
        $('.gear-popover-label').each(function () {
            const $label = $(this);

            $label.qtip({
                position: {
                    viewport: $(window)
                },
                show: {
                    event: "mouseenter",
                    solo: true,
                    delay: 500
                },
                hide: {
                    event: 'mouseleave unfocus',
                    delay: 1000,
                    fixed: true
                },
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
                },
                events: {
                    show: function (event, api) {
                        $label.addClass('qtip-open');
                        $(".ui-tooltip .btn-close").one("click", function (e) {
                            api.hide();
                            e.preventDefault();
                        });
                    },

                    hide: function (event, api) {
                        $label.removeClass('qtip-open');
                    },
                },
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

    init_timestamps: function (fragment) {
        if (fragment === undefined) {
            fragment = document;
        }

        $(fragment).find('abbr.timestamp').each(function (index, element) {
            const $el = $(element);
            const datetime = new Date(0);
            const locale = window.navigator.userLanguage || window.navigator.language;
            const now = new Date();

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

    show_page_loading_indicator: function (loadingText) {
        const $pageLoadingIndicator = $('#page-loading-indicator');
        const $pageLoadingText = $('#page-loading-text');
        const $pageLoadingBackdrop = $('#page-loading-indicator-backdrop');

        $pageLoadingBackdrop.css('width', '100%');
        $pageLoadingBackdrop.css('height', '100%');
        $pageLoadingBackdrop.css('opacity', .65);

        $pageLoadingIndicator.css('width', '100%');
        $pageLoadingIndicator.css('height', '100%');
        $pageLoadingIndicator.css('opacity', 1);

        if (loadingText) {
            $pageLoadingText.html($(this).data('loading-text'));
            $pageLoadingText.css('width', '100%');
            $pageLoadingText.css('height', '100%');
            $pageLoadingText.css('opacity', 1);
        }
    },

    hide_page_loading_indicator: function () {
        const $pageLoadingIndicator = $('#page-loading-indicator');
        const $pageLoadingText = $('#page-loading-text');
        const $pageLoadingBackdrop = $('#page-loading-indicator-backdrop');

        $pageLoadingBackdrop.css('width', 0);
        $pageLoadingBackdrop.css('height', 0);
        $pageLoadingBackdrop.css('opacity', 0);

        $pageLoadingIndicator.css('width', 0);
        $pageLoadingIndicator.css('height', 0);
        $pageLoadingIndicator.css('opacity', 0);

        $pageLoadingText.css('width', 0);
        $pageLoadingText.css('height', 0);
        $pageLoadingText.css('opacity', 0);
    },

    init_page_loading_indicator: function () {
        $(window).bind("pagehide", function () {
            setTimeout(function () {
                astrobin_common.hide_page_loading_indicator();
            }, 10);
        });

        $('a:not(.no-page-loader):not([data-fancybox])').live('click', function (event) {
            let url = $(this).attr('href');

            if (!url) {
                return;
            }

            url = url.trim();

            // Skip CKEditor attachments.
            if (url.indexOf('ckeditor-files') > -1) {
                return;
            }

            // Skip cookie consent URLs.
            if (url.indexOf('/cookies/') > -1) {
                return;
            }

            // Skip endless pagination.
            if ($(event.target).hasClass('endless_more')) {
                return;
            }

            // Skip notifications.
            if ($(event.target).closest('.notification-item').length) {
                return;
            }

            // Skip CTRL/Meta clicks
            if (event.metaKey || event.ctrlKey) {
                return;
            }

            // Skip links to new tab/window.
            if (($(this).attr('target') || '_self') !== '_self') {
                return;
            }

            // Skip javascript: links.
            if (url.indexOf('javascript:') === 0) {
                return;
            }

            // Skip anchor links.
            if (url[0] === '#') {
                return;
            }

            // Open external links in new tab.
            if (
                url.indexOf('astrobin.com') === -1 &&
                url.indexOf('localhost') === -1 &&
                url[0] !== '/'
            ) {
                astrobin_common.open_link(url, true);
                event.preventDefault();
                return;
            }

            astrobin_common.show_page_loading_indicator($(this).data('loading-text'));

            return true;
        });
    },

    get_notifications: function () {
        $.ajax({
            url: '/api/v2/notifications/notification/?read=False',
            method: 'GET',
            dataType: 'json',
            timeout: 5000,
            success: function (data) {
                var $modal = $('#notifications-modal');

                if (!data.count) {
                    return;
                }

                var t = document.querySelector('#notification-row-template');
                var $tbody = $modal.find('.table tbody');

                data.results.forEach(function (notification) {
                    t.content.querySelector('.notification-unread').setAttribute('data-id', notification['id']);
                    t.content.querySelector('.notification-content').innerHTML = notification['message'].replace('<a ', '<a data-no-instant ');
                    t.content.querySelector('.timestamp').setAttribute('data-epoch', new Date(notification['created'] + 'Z').getTime());
                    $tbody.append(document.importNode(t.content, true));

                    $tbody.find('.notification-unread[data-id=' + notification['id'] + '] .notification-mark-as-read a').live('click', function () {
                        astrobin_common.mark_notification_as_read(notification['id']);
                    })
                });

                $tbody.find('.no-new-notifications').hide();
                astrobin_common.init_timestamps();

                $('#notifications-count').text(data.count).show();

                $('#mark-all-notifications-as-read').removeAttr('disabled').click(function () {
                    astrobin_common.mark_all_notifications_as_read().then(function () {
                        $tbody.find('.no-new-notifications').show();
                        $modal.modal('hide');
                    });
                });
            }
        });
    },

    mark_notification_as_read: function (notification_id) {
        var $row = $('#notifications-modal tr[data-id=' + notification_id + ']'),
            $check_mark = $row.find('td.notification-mark-as-read a'),
            $loading = $row.find(".notification-mark-as-read .loading"),
            $count_badge = $('#notifications-count'),
            count;

        $check_mark.remove();
        $loading.show();

        return new Promise(function (resolve) {
            if ($row.hasClass("notification-read")) {
                $loading.hide();
                return resolve();
            }

            $.ajax({
                url: '/persistent_messages/mark_read/' + notification_id + '/',
                dataType: 'json',
                success: function () {
                    $row.removeClass('notification-unread');
                    $row.addClass('notification-read');
                    $loading.hide();

                    if ($count_badge.length > 0) {
                        count = parseInt($count_badge.text());
                        if (count === 1) {
                            $count_badge.remove();
                        } else {
                            $count_badge.text(count - 1);
                        }
                    }

                    resolve();
                }
            });
        });

    },

    mark_all_notifications_as_read: function () {
        const $rows = $('#notifications-modal tr:not(.no-new-notifications)'),
            $count_badge = $('#notifications-count'),
            $btn = $('#mark-all-notifications-as-read');
        
        $btn.addClass('running');
        $btn.attr('disabled', 'disabled');

        return new Promise(function (resolve) {
            $.ajax({
                url: '/api/v2/notifications/notification/mark_all_as_read/',
                type: 'put',
                dataType: 'json',
                cache: false,
                timeout: 10000,
                success: function () {
                    $rows.remove();

                    if ($count_badge.length > 0) {
                        $count_badge.remove();
                    }

                    resolve();
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    $.toast({
                        heading: 'Error',
                        text: textStatus,
                        showHideTransition: 'slide',
                        allowToastClose: true,
                        position: 'top-right',
                        loader: false,
                        hideAfter: false,
                        icon: 'error'
                    });
                },
                complete: function () {
                    $btn.removeClass('running');
                }
            });
        });
    },

    register_notification_on_click: function () {
        $(document).ready(function () {
            var urlWithoutNid = astrobin_common.remove_url_param(window.location.href, "nid");
            window.history.replaceState('', document.title, urlWithoutNid);

            $(".notifications-modal .notification-item .notification-content a").live('click', function (event) {
                event.preventDefault();

                var $item = $(this).closest(".notification-item");
                var $loading = $item.find(".notification-mark-as-read .loading")
                var $readMarker = $item.find(".notification-mark-as-read .icon")
                var id = $item.data("id");
                var links = astrobin_common.get_links_in_text($item.find(".notification-content").html());
                var openInNewTab = astrobin_common.config.open_notifications_in_new_tab;

                if (links.length > 0) {
                    var link = astrobin_common.add_or_update_url_param(links[0], "nid", id);

                    if (openInNewTab || event.metaKey || event.ctrlKey) {
                        astrobin_common.mark_notification_as_read(id).then(function () {
                            astrobin_common.open_link(link, true);
                        });
                    } else {
                        $readMarker.hide();
                        $loading.show();
                        astrobin_common.open_link(link, false);
                    }
                }
            })
        });
    },

    open_link(link, openInNewTab) {
        window.open(link, openInNewTab ? "_blank" : "_self");
    },

    get_links_in_text: function (text) {
        var regex = /href="(.*?)"/gm;
        var m;
        var links = [];

        while ((m = regex.exec(text)) !== null) {
            // This is necessary to avoid infinite loops with zero-width matches
            if (m.index === regex.lastIndex) {
                regex.lastIndex++;
            }

            // The result can be accessed through the `m`-variable.
            m.forEach((match, groupIndex) => {
                if (match.indexOf("href") !== 0) {
                    links.push(match);
                }
            });
        }

        return links;
    },

    add_or_update_url_param: function (url, name, value) {
        const i = url.indexOf('#');
        const hash = i === -1 ? '' : url.substr(i);

        url = i === -1 ? url : url.substr(0, i);

        const re = new RegExp("([?&])" + name + "=.*?(&|$)", "i");
        const separator = url.indexOf('?') !== -1 ? "&" : "?";

        if (url.match(re)) {
            url = url.replace(re, '$1' + name + "=" + value + '$2');
        } else {
            url = url + separator + name + "=" + value;
        }

        return url + hash;
    },

    remove_url_param: function (url, parameter) {
        var urlParts = url.split('?');

        if (urlParts.length >= 2) {
            var prefix = encodeURIComponent(parameter) + '=';
            var pars = urlParts[1].split(/[&;]/g);

            for (var i = pars.length; i-- > 0;) {
                if (pars[i].lastIndexOf(prefix, 0) !== -1) {
                    pars.splice(i, 1);
                }
            }

            return urlParts[0] + (pars.length > 0 ? '?' + pars.join('&') : '');
        }

        return url;
    },

    get_selected_text: function () {
        if (document.selection) {
            return document.selection.createRange().text;
        } else {
            return window.getSelection().toString();
        }
    },

    get_indexes: function () {
        $.ajax({
            url: '/api/v2/common/userprofiles/current/',
            method: 'GET',
            dataType: 'json',
            timeout: 5000,
            success: function (data) {
                var userprofile = data[0];

                if (!userprofile.exclude_from_competitions) {
                    var image_index = userprofile.astrobin_index || 0;
                    var contribution_index = userprofile.contribution_index || 0;

                    $('#astrobin-index').text(image_index.toFixed(2));
                    $('#astrobin-index-popover').text(image_index.toFixed(2));
                    $('#astrobin-index-mobile-header').text(image_index.toFixed(2));

                    $('#contribution-index').text(contribution_index.toFixed(2));
                    $('#contribution-index-popover').text(contribution_index.toFixed(2));

                    $('#navbar-user-scores').show();
                }
            }
        });
    },

    init_toggle_high_contrast_theme: function () {
        $(document).ready(function () {
            $('.toggle-high-contrast-theme').on('click', function (event) {
                event.preventDefault();

                $.ajax({
                    url: '/json-api/user/toggle-use-high-contrast-theme-cookie/',
                    type: 'POST',
                    dataType: 'json',
                    timeout: 5000,
                    success: function () {
                        $('#this-operation-will-reload-page-modal').modal('show');
                    }
                });
            });
        });
    },

    init_popup_messages: function () {
      $(document).ready(function () {
         $('.popup-message-dont-show-again').click(function () {
            const popupMessage = $(this).closest('.popup-message');
            const id = popupMessage.data('id');

            $(this).html()

            $.ajax({
                url: `/json-api/user/dont-show-popup-message-again/`,
                type: 'POST',
                dataType: 'json',
                data: {
                    'popup_id': id
                },
                timeout: 5000,
                success: function () {
                     popupMessage.remove();
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    $.toast({
                        heading: 'Error',
                        text: 'An error occurred. Please try again later.',
                        showHideTransition: 'slide',
                        allowToastClose: true,
                        position: 'top-right',
                        loader: false,
                        hideAfter: false,
                        icon: 'error'
                    });
                }
            });
         });
      });
    },

    abuse_report_modal_show: function () {
        return new Promise(function (resolve, reject) {
            const $modal = $('#report-abuse-modal');
            const $reason = $modal.find('#id_reason');
            const $additionalInformation = $modal.find('#id_additional_information');
            const $reportAbuseButton = $modal.find('.btn-primary');
            const $cancelButton = $modal.find('.btn-secondary');

            $reason.val(null).trigger('change');
            $additionalInformation.val('');
            $reportAbuseButton.attr('disabled', 'disabled');
            $reportAbuseButton.removeClass('running');

            $reason.change(function () {
                if ($reason.val()) {
                    $reportAbuseButton.removeAttr('disabled');
                } else {
                    $reportAbuseButton.attr('disabled', 'disabled');
                }
            });

            $reportAbuseButton.click(function () {
                resolve({
                    reason: $reason.val(),
                    additionalInformation: $additionalInformation.val()
                });
            });

            $modal.on('hidden', function () {
                reject();
            })

            $cancelButton.click(function () {
                reject();
            });

            $modal.modal('show');
        });
    },

    abuse_report_modal_hide: function () {
        const $modal = $('#report-abuse-modal');
        $modal.modal('hide');
    },

    abuse_report_modal_set_loading: function () {
        const $modal = $('#report-abuse-modal');
        const $reportAbuseButton = $modal.find('.btn-primary');

        $reportAbuseButton.attr('disabled', 'disabled');
        $reportAbuseButton.addClass('running');
    },

    init_fancybox_toolbar_link_buttons: function (fancybox, slide) {
        const rel = slide.rel;

        setTimeout(() => {
            const $linkButton = $(fancybox.plugins.Toolbar.$container).find('.fancybox__button--viewImagePage');
            const $linkInNewTabButton = $(fancybox.plugins.Toolbar.$container).find('.fancybox__button--viewImagePageInNewTab');

            if (rel !== 'image-list' && rel !== 'revisions') {
                $linkButton.remove();
                $linkInNewTabButton.remove();
            }
        })
    },

    init_fancybox_toolbar_toggle_property_button: function (fancybox, slide, requestUserId) {
        const rel = slide.rel;
        const imageId = slide.id;
        const imageIdOrHash = slide.idOrHash;
        const userId = slide.userId;

        const waitIcon = 'icon-spinner';
        const likeIcon = 'icon-thumbs-up';

        setTimeout(() => {
            const $button = $(fancybox.plugins.Toolbar.$container).find('.fancybox__button--toggleProperty');
            const $icon = $button.find('i');

            if (rel !== 'image-list' || requestUserId === userId || requestUserId === 0) {
                $button.remove();
                return;
            }

            $icon
                .addClass(waitIcon)
                .removeClass(likeIcon);
            $button
                .off('click')
                .attr('disabled', 'disabled');

            $.ajax({
                type: 'get',
                url: '/api/v2/common/contenttypes/?app_label=astrobin&model=image',
                dataType: 'json',
                success: (contentTypeResponse) => {
                    const contentType = contentTypeResponse[0];

                    $.ajax({
                        type: 'get',
                        url: `/api/v2/common/toggleproperties?content_type=${contentType.id}&property_type=like&user_id=${requestUserId}&object_id=${imageId}`,
                        dataType: 'json',
                        success: (togglePropertyResponse) => {
                            const liked = togglePropertyResponse.count > 0;

                            if (liked) {
                                $icon
                                    .removeClass(waitIcon)
                                    .addClass(likeIcon);
                                $button
                                    .attr('disabled', 'disabled');
                                return;
                            }

                            $button
                                .html(`<i class="${likeIcon}"></i>`)
                                .removeAttr('disabled')
                                .data('content-type', contentType.id)
                                .data('object-id', imageId)
                                .one('click', function (e) {
                                    e.preventDefault();

                                    $icon
                                        .removeClass(likeIcon)
                                        .addClass(waitIcon);
                                    $button
                                        .attr('disabled', 'disabled');

                                    $.ajax({
                                        type: 'post',
                                        url: '/api/v2/common/toggleproperties/',
                                        data: {
                                            property_type: 'like',
                                            content_type: contentType.id,
                                            object_id: imageId,
                                            user: requestUserId
                                        },
                                        timeout: 5000,
                                        success: function (response) {
                                            togglePropertyResponse = {
                                                results: [
                                                    response
                                                ]
                                            };

                                            $icon
                                                .removeClass(waitIcon)
                                                .addClass(likeIcon);
                                            $button
                                                .attr('disabled', 'disabled');
                                        },
                                        error: function (XMLHttpRequest, textStatus, errorThrown) {
                                            if (XMLHttpRequest.status === 401) {
                                                window.location.href = `/account/login/?next=/${imageIdOrHash}`;
                                                return;
                                            } else {
                                                $('#cant-like').modal('show');
                                            }

                                            $icon
                                                .removeClass(waitIcon)
                                                .addClass(likeIcon);
                                            $button
                                                .removeAttr('disabled');
                                        }
                                    });
                                })
                        }
                    })
                }
            });
        }, 250);
    },

    init_fancybox_plate_solution: function (fancybox, slide) {
        function observeImageMutations($img) {
            const delay = 100;

            function applyMutations(mutations) {
                if (window.astroBinFancyBoxLastMutation && new Date().getTime() - window.astroBinFancyBoxLastMutation < delay) {
                    return;
                }

                const $solution = $(fancybox.$carousel).find('.fancybox__slide.is-selected .fancybox__overlaySolution');

                mutations.forEach(function () {
                    $solution.attr('style', $img.attr('style'));
                    $solution.css('display', 'block');
                });
            }

            if (!!window.astroBinFancyBoxMutationObserver) {
                window.astroBinFancyBoxMutationObserver.disconnect();
            }

            window.astroBinFancyBoxMutationObserver = new MutationObserver(function (mutations) {
                window.astroBinFancyBoxLastMutation = new Date().getTime();
                const $solution = $(fancybox.$carousel).find('.fancybox__slide.is-selected .fancybox__overlaySolution');
                $solution.css('display', 'none');
                setTimeout(() => applyMutations(mutations), delay + 1);
            });

            if (!!$img && !!$img[0]) {
                window.astroBinFancyBoxMutationObserver.observe($img[0], {
                    attributes: true,
                    attributeFilter: ['style']
                });
            }
        }

        if ($(slide.$image).siblings('.fancybox__overlaySolution').length > 0) {
            observeImageMutations($(fancybox.$carousel).find('.fancybox__slide.is-selected .fancybox__image'));
            return;
        }

        let contentTypeModel;
        let objectId;

        if (slide.finalRevisionLabel === '0') {
            contentTypeModel = 'image';
            objectId = slide.id;
        } else {
            contentTypeModel = 'imagerevision'
            objectId = slide.finalRevisionId;
        }

        $.ajax({
            type: 'get',
            url: `/api/v2/common/contenttypes/?app_label=astrobin&model=${contentTypeModel}`,
            dataType: 'json',
            success: (contentTypeResponse) => {
                const contentType = contentTypeResponse[0];

                $.ajax({
                    type: 'get',
                    url: `/api/v2/platesolving/solutions/?content_type=${contentType.id}&object_id=${objectId}`,
                    dataType: 'json',
                    success: (response) => {
                        if (response.length === 0) {
                            return;
                        }

                        const solution = response[0];

                        const $image = $(slide.$image);
                        let $element = null;

                        if (solution.pixinsight_svg_annotation_hd) {
                            $element = $(
                                `
                                            <div class="fancybox__overlaySolution">
                                                <object
                                                    id="advanced-plate-solution-svg"
                                                    onload="AstroBinPlatesolving.advancedSvgLoaded()"
                                                    type="image/svg+xml"
                                                    data="/platesolving/solution/${solution.id}/svg/hd/">
                                                </object>
                                            </div>
                                        `
                            )
                        } else if (solution.image_file) {
                            $element = $(
                                `
                                            <div class="fancybox__overlaySolution">
                                                <img src="${solution.image_file}" />
                                            </div>
                                        `
                            )
                        }

                        if ($element !== null) {
                            observeImageMutations($image);
                            $image.after($element);
                        }
                    }
                });
            }
        });
    },

    start_fancybox: function (items, options, jumpToSlug) {
        const queryString = window.location.search;
        const urlParams = new URLSearchParams(queryString);
        const autoplay = urlParams.get('autoplay');
        let transitions = urlParams.get('transitions');
        const speed = urlParams.get('speed') || 5000;

        transitions = transitions === null ? 'true' : transitions;

        const transitionDuration = transitions === 'true' ? 0.92 : 0;

        const fancybox = new window.Fancybox(
            items,
            Object.assign(options, {
                slideshow: {
                    delay: speed
                },
                Carousel: {
                    friction: transitionDuration
                }
            })
        );

        if (autoplay === 'true') {
            fancybox.plugins.Toolbar.Slideshow.activate();
        }

        let url = astrobin_common.add_or_update_url_param(window.location.href, 'slideshow', true);
        url = astrobin_common.add_or_update_url_param(url, 'transitions', transitions);

        window.history.pushState({path: url}, '', url);

        if (!!jumpToSlug) {
            const index = items.map(item => item.slug).indexOf(jumpToSlug);
            fancybox.jumpTo(index);
        }
    },

    update_fancybox_share_links: function () {
        $('#fancybox-settings-modal #id_slideshow_share').text(window.location.href);
        $('#fancybox-settings-modal #id_slideshow_share_beginning').text(window.location.href.split('#')[0]);
    },

    setVideoJsPlayerOnFullScreenChange: function (player) {
        player.on('fullscreenchange', function () {
            const isFullscreen = player.isFullscreen();
            const el = player.el().firstChild;

            if (isFullscreen) {
                el.style.maxWidth = `${player.videoWidth()}px`;
                el.style.maxHeight = `${player.videoHeight()}px`;
                el.style.top = `50%`;
                el.style.left = `50%`;
                el.style.transform = `translate(-50%, -50%)`;
                el.style.margin = 'auto';
            } else {
                el.style.maxWidth = '';
                el.style.maxHeight = '';
                el.style.top = '';
                el.style.left = '';
                el.style.transform = '';
                el.style.margin = '';

                // For some reasons, Fancybox registering the click ends up with the fancybox__content being 0px
                setTimeout(() => {
                    const fancyBoxContent = el.closest('.fancybox__content');
                    if (fancyBoxContent) {
                        fancyBoxContent.style.width = `${player.videoWidth()}px`;
                        fancyBoxContent.style.height = `${player.videoHeight()}px`;
                    }
                }, 100);
            }
        });
    },

    init: function (config) {
        function formatSelect2Results(state) {
            if (!state.id) {
                return state.text;
            }

            const parts = state.text.split("///");

            if (parts.length === 2) {
                return $(
                    '<span>' +
                    '<div class="header">' + parts[0] + '</div>' +
                    '<div class="description">' + parts[1] + '</div>' +
                    '</span>'
                );
            } else {
                return state.text;
            }
        }

        function formatSelect2Selection(state) {
            if (!state.id) {
                return state.text;
            }

            const parts = state.text.split("///");

            if (parts.length === 2) {
                return parts[0];
            } else {
                return state.text;
            }
        }

        /* Init */
        $.extend(true, astrobin_common.config, config);

        $(".dropdown-toggle").dropdown();
        $(".carousel").carousel();
        $(".nav-tabs").tab();
        $("[rel=tooltip]").tooltip();
        $(".collapse.in").collapse();

        // date and time pickers
        $("input.timepickerclass").timepicker({});
        $("input.datepickerclass").datepicker({
            dateFormat: 'yy-mm-dd',
            changeMonth: true,
            changeYear: true
        });

        $("#quick-search input").focus(() => {
            if ($(window).width() >= 520) {
                $(".search-nav").css({
                    width: 'calc(100% - ' + (
                        $(".site-nav").outerWidth() + $(".user-nav").outerWidth() + $(".brand").outerWidth()
                    ) + 'px'
                });
            }
        }).blur(() => {
            if ($(window).width() >= 520) {
                $(".search-nav").css({width: "auto"});
            }
        });

        $(window).resize(() => {
            if ($(window).width() >= 520) {
                $(".search-nav").css({width: "auto"});
            } else {
                $(".search-nav").css({width: "calc(100% - 10px)"});
            }
        });

        astrobin_common.init_timestamps();
        astrobin_common.init_page_loading_indicator();

        $("select[multiple]:not(.select2)").not('*[name="license"]').multiselect({
            searchable: false,
            dividerLocation: 0.5
        });

        if (window.innerWidth >= 980) {
            $("select:not([multiple])").select2({
                theme: "flat",
                templateResult: formatSelect2Results,
                templateSelection: formatSelect2Selection
            });
        }

        $("select.select2").select2({
            theme: "flat",
            templateResult: formatSelect2Results,
            templateSelection: formatSelect2Selection
        });

        astrobin_common.init_ajax_csrf_token();

        if (config.is_authenticated) {
            astrobin_common.get_indexes();
            astrobin_common.register_notification_on_click();
            setTimeout(function () {
                astrobin_common.get_notifications();
            }, 1500);
        }

        astrobin_common.init_toggle_high_contrast_theme();

        astrobin_common.init_popup_messages();
    },

    highlightCodePrepare: function () {
        if (typeof hljs !== "undefined") {
            const brPlugin = {
                "before:highlightBlock": ({block}) => {
                    block.innerHTML = block.innerHTML.replace(/<br[ /]*>/g, '\n');
                },
                "after:highlightBlock": ({result}) => {
                    result.value = result.value.replace(/\n/g, "<br>");
                }
            };

            hljs.addPlugin(brPlugin);
            hljs.addPlugin(new CopyButtonPlugin());
        }
    },

    highlightCodeFinalize: function () {
        if (typeof hljs !== "undefined") {
            hljs.initLineNumbersOnLoad();
        }
    },

    highlightCode: function () {
        if (typeof hljs !== "undefined") {
            astrobin_common.highlightCodePrepare();
            hljs.highlightAll();
            astrobin_common.highlightCodeFinalize();

        }
    },

    highlightCodeForElement: function ($element) {
        if (typeof hljs !== "undefined") {
            hljs.highlightElement($element);
            hljs.lineNumbersBlock($element);
        }
    }
};

/**********************************************************************
 * Stats
 *********************************************************************/
astrobin_stats = {
    config: {},

    fetch_iotd_stats: function () {
        const url = "/api/v2/iotd/stats/";

        $("#iotd-stats-modal td").text("...");

        $.ajax({
            url: url,
            method: 'GET',
            dataType: 'json',
            timeout: 5000,
            cache: false,
            success: function (data) {
                const stats = data['results'][0];
                const $header = $("#iotd-stats-modal .modal-header h3");

                $header.text(
                    $header.text().replace('[x]', stats['days'])
                )

                Object.keys(stats).forEach(key => {
                    const $el = $(`#iotd-stats-modal td.${key.replaceAll('_', '-')}`);
                    let text = stats[key];

                    if ($el.closest('.table').hasClass('percentages')) {
                        text = text.toFixed(2) + '%';
                    }

                    $el.text(text);
                });
            }
        })
    },

    init: function (config) {
        /* Init */
        $.extend(true, astrobin_stats.config, config);

        $("#iotd-stats-modal").on("show", function () {
            astrobin_stats.fetch_iotd_stats();
        })
    }
};
