$(function () {

    var languageCode = $('#nested-comments-language-code').attr('data-value');

    /*******************************************************************
     * APP
     *******************************************************************/

    var nc_app = Em.Application.create({
        rootElement: '#nested-comments',
        ajaxTimeout: 20000,

        baseApiUrl: '/api/v2/',

        ready: function () {
            this.commentsApiUrl = this.baseApiUrl + 'nestedcomments/nestedcomments/';
            this.togglepropertiesApiUrl = this.baseApiUrl + 'common/toggleproperties/';
            this.usersUrl = '/users/';

            this.path = $('#nested-comments-path').attr('data-value');
            this.languagecode = languageCode;
            this.userId = parseInt($('#nested-comments-user-id').attr('data-value'));
            this.username = $('#nested-comments-user-name').attr('data-value');
            this.realName = $('#nested-comments-user-real-name').attr('data-value');
            this.userIsAuthenticated = $('#nested-comments-user-is-authenticated').attr('data-value') == "True";
            this.userIsSuperuser = $('#nested-comments-user-is-superuser').attr('data-value') == "True";
            this.shadowBans = JSON.parse($('#nested-comments-shadow-bans').attr('data-value'));
            this.page_url = $('#nested-comments-page-url').attr('data-value');
            this.loaderGif = $('#nested-comments-loaderGif-url').attr('data-value');
            this.editorPlaceholder = $('#nested-comments-editor-placeholder').attr('data-value');
            this.contentTypeId = $(this.rootElement).attr('data-content-type-id');
            this.contentObjectOwnerId = parseInt($(this.rootElement).attr('data-content-object-owner-id'));
            this.nestedcommentsContentTypeId = $('#nested-comments-comments-content-type-id').attr('data-value');
            this.objectId = $(this.rootElement).attr('data-object-id');

            this.markdownConverter = new Markdown.Converter();
            this.commentStore = [];
        }
    });

    /*******************************************************************
     * BASE VIEWS
     *******************************************************************/

    nc_app.I18nView = Em.View.extend({
        templateName: "i18n",
        tagName: 'span',

        translated: function () {
            return Em.String.htmlSafe(window.astrobin_nestedcomments_i18n[this.value]);
        }.property('value')
    });


    nc_app.LoginOrSignUpView = Em.View.extend({
        templateName: 'login-or-sign-up'
    });

    nc_app.ContributionIndexAlertView = Em.View.extend({
        templateName: "contribution-index-alert"
    });

    nc_app.RichContentEditorHelpView = Em.View.extend({
        templateName: "rich-content-editor-help"
    });

    // A view used to DRY the logic common to views with textareas (top
    // level, edit, reply).
    nc_app.TextareaView = Em.View.extend({
        TypeEnum: {
            TOP_LEVEL: 1,
            EDIT: 2,
            REPLY: 3
        },

        syncInterval: null,
        type: null,

        createSyncInterval: function () {
            var self = this;
            this.set('syncInterval', setInterval(function () {
                self.sync(true);
            }, 200));
        },

        removeSyncInterval: function () {
            if (this.get('syncInterval') === null) {
                return;
            }

            clearInterval(this.get('syncInterval'));
            this.set('syncInterval', null);
        },

        sync: function (syncTextarea) {
            try {
                var textarea = this.$('textarea'),
                    data = CKEDITOR.instances[textarea.attr('id')].getData(),
                    property = null;

                switch (this.get('type')) {
                    case this.TypeEnum.TOP_LEVEL:
                    case this.TypeEnum.REPLY:
                        property = 'comment';
                        break;
                    case this.TypeEnum.EDIT:
                        property = 'parentView.node';
                        break;
                }

                this.set(property + '.html', astrobin_common.utils.BBCodeToHtml(
                    data, "comments", nc_app.languageCode));

                if (typeof syncTextarea !== 'undefined' && syncTextarea) {
                    this.set(property + '.text', data);
                }
            } catch (TypeError) {
                // textarea was not available, probably because the user is
                // not signed in.
            }
        },

        initTextarea: function () {
            var self = this;

            setTimeout(function () {
                var textarea = self.$('textarea');
                CKEDITOR.replace(
                    textarea.attr("id"),
                    astrobin_common.utils.ckeditorOptions(
                        "comments",
                        nc_app.languageCode,
                        nc_app.editorPlaceholder
                    )
                );
                self.createSyncInterval();
            }, 1);
        }
    });

    /*******************************************************************
     * Models
     *******************************************************************/

    nc_app.Comment = Em.Object.extend({
        // Native fields
        id: null,
        author: null,
        content_type: null,
        object_id: null,
        text: '',
        created: null,
        updated: null,
        deleted: null,
        pending_moderation: null,
        parent: null,
        depth: null,
        likes: [],

        // Fields that we compute manually
        ready: false,
        children: null,
        author_username: null,
        author_url: null,
        author_avatar: null,
        authorIsRequestingUser: null,
        userIsContentObjectOwner: null,
        editing: null,
        submitting: null,
        original_text: null, // Text before editing starts
        html: null,

        // Computed properties
        cid: function () {
            return 'c' + this.get('id');
        }.property('id'),

        url: function () {
            return nc_app.page_url + '#' + this.get('cid');
        }.property('id'),

        allowEditing: function () {
            return this.get('deleted') === false;
        }.property('deleted'),

        getHTML: function () {
            const created = new Date(this.created);
            const release = new Date(
                astrobin_common.globals.BREAKAGE_DATES.COMMENTS_MARKDOWN);

            if (created > release) {
                return this.get('html');
            }

            // Old behavior before the move from Markdown to BBCode in 1.26.
            return nc_app.markdownConverter.makeHtml(this.get('text'));
        }.property('html', 'text'),
        
        // Properties for translation
        originalContentId: function() {
            return 'comment-original-content-' + this.get('id');
        }.property('id'),
        
        translatedContentId: function() {
            return 'comment-translated-content-' + this.get('id');
        }.property('id'),
        
        translateButtonId: function() {
            return 'btn-translate-comment-' + this.get('id');
        }.property('id'),

        disallowSaving: function () {
            var submitting = this.get('submitting');
            var hasText = this.get('html') !== null && this.get('html').length > 0;

            return submitting || !hasText;
        }.property('submitting', 'html'),

        shouldNotIndent: function () {
            return this.depth > 10;
        }.property('depth'),

        liked: function () {
            return this.likes.indexOf(nc_app.userId) > -1;
        }.property('likes'),

        likesCount: function () {
            return this.likes.length;
        }.property('likes'),

        hasNoLikes: function () {
            return this.likes.length === 0;
        }.property('likes'),

        hasOneLike: function () {
            return this.likes.length === 1;
        }.property('likes'),

        hasManyLikes: function () {
            return this.likes.length > 1;
        }.property('likes'),

        isPendingModeration: function () {
            return this.pending_moderation && !this.deleted;
        }.property('pending_moderation', 'deleted'),

        displayAvatar: function () {
            return !this.pending_moderation && !this.deleted;
        }.property('pending_moderation', 'deleted'),

        // Functions
        init: function () {
            this._super();

            this.deleted = false;
            this.children = [];

            this.editing = false;
            this.submitting = false;
        }
    });


    /*******************************************************************
     * Views and Controllers
     *******************************************************************/

    nc_app.ApplicationController = Em.Controller.extend();
    nc_app.ApplicationView = Em.View.extend({
        templateName: "nested-comments"
    });


    nc_app.SaveButtonView = Em.View.extend({
        templateName: 'saveButton',
        tagName: 'button',
        classNames: ['btn btn-mini btn-primary'],
        classNameBindings: ['disabled'],
        attributeBindings: ['disabled'],

        disabledBinding: 'parentView.disallowSaving',

        click: function (event) {
            this.get('parentView').save();
            event.preventDefault();
        }
    });


    nc_app.TopLevelController = Em.Controller.extend();
    nc_app.TopLevelView = nc_app.TextareaView.extend({
        templateName: "top-level",
        classNames: 'top-level comment',
        submittingBinding: 'comment.submitting',
        disallowSavingBinding: 'comment.disallowSaving',
        userIsAuthenticated: null,
        collapsed: true,
        syncInterval: null,

        collapse: function () {
            this.set('collapsed', true);
            this.reset();
        },

        uncollapse: function () {
            this.set('collapsed', false);
            this.initTextarea();
        },

        reset: function () {
            var instance = CKEDITOR.instances[self.$('textarea').attr('id')];

            if (instance) {
                instance.setData('');
            }

            var comment = nc_app.get('router.commentsController').createComment();
            this.set('comment', comment);

            this.removeSyncInterval();
        },

        didInsertElement: function () {
            this.set('type', this.TypeEnum.TOP_LEVEL);
            this.reset();
            this.set('userIsAuthenticated', nc_app.userIsAuthenticated);
        },

        save: function () {
            var self = this;
            this.sync(true);
            nc_app.get('router.commentsController').saveNewComment(self.get('comment'))
                .then(function (response, statusText, xhr) {
                    self.collapse();
                });
        },

        SaveCommentButtonView: nc_app.SaveButtonView.extend()
    });


    nc_app.CommentsController = Em.ArrayController.extend({
        content: [], // The top-level comments
        ready: false,
        firstCommentAdded: false,

        findCommentById: function (id, root) {
            var self = this;

            if (root === undefined) {
                for (var i = 0; i < self.content.length; i++) {
                    var comment = self.findCommentById(id, self.content[i]);
                    if (comment !== undefined)
                        return comment;
                }
            } else {
                if (root.get('id') === id)
                    return root;
                for (var i = 0; i < root.get('children').length; i++) {
                    var comment = self.findCommentById(id, root.get('children')[i]);
                    if (comment !== undefined)
                        return comment;
                }
            }
        },

        addComment: function (comment) {
            const self = this;

            if (comment.get('parent') == null) {
                self.pushObject(comment);
            } else {
                var parent = self.findCommentById(comment.get('parent'));
                if (parent !== undefined) {
                    parent.get('children').pushObject(comment);
                } else
                    self.pushObject(comment);
            }

            self.highlightCode(comment);
        },

        createComment: function () {
            return nc_app.Comment.create({
                author: nc_app.userId,
                content_type: nc_app.contentTypeId,
                object_id: nc_app.objectId,
                text: ''
            });
        },

        fetchComments: function (url, data) {
            var self = this;

            if (url != null) {
                $.ajax({
                    url: url,
                    cache: false,
                    timeout: nc_app.ajaxTimeout,
                    dataType: 'json',
                    data: data,
                    success: function (response) {
                        $.each(response, function (i, nc_data) {
                            var comment = nc_app.Comment.create(nc_data);
                            comment.set('authorIsRequestingUser', nc_app.userId === comment.get('author'));
                            comment.set('userIsContentObjectOwner', nc_app.userId === nc_app.contentObjectOwnerId);
                            comment.set('moderationRequested',
                                window.location.search.indexOf('moderate-comment') > -1 &&
                                window.location.hash === '#c{0}'.format(comment.get('id')));
                            comment.set('deleted', nc_data.deleted);
                            comment.set('author_username', nc_data.author_display_name);
                            comment.set('author_url', nc_app.usersUrl + nc_data.author_username);
                            comment.set('author_avatar', nc_data.author_avatar);

                            nc_app.commentStore.push(comment);
                        });

                        // Now that all comments are in commentStore, we can add them to the view
                        $.each(nc_app.commentStore, function (i, comment) {
                            function commentIsShadowBanned(commentId) {
                                if (commentId === null) {
                                    return false;
                                }

                                var comments = nc_app.commentStore.filter(function (comment) {
                                    return comment.id === commentId;
                                });

                                if (comments) {
                                    var comment = comments[0];

                                    if (nc_app.userId !== comment.author && nc_app.shadowBans.indexOf(comment.author) > -1) {
                                        return true;
                                    } else {
                                        return commentIsShadowBanned(comment.parent);
                                    }
                                }

                                return false;
                            }

                            if (nc_app.shadowBans && !commentIsShadowBanned(comment.id)) {
                                self.addComment(comment);
                            }
                        });

                        if (!self.get('ready')) {
                            self.set('ready', true);
                        }
                    }
                });
            }
        },

        find: function () {
            var self = this,
                data = {
                    'content_type': nc_app.contentTypeId,
                    'object_id': nc_app.objectId
                };

            self.fetchComments(nc_app.commentsApiUrl, data);
            return self.content;
        },

        dump: function (comment) {
            data = {
                id: comment.get('id'),
                author: comment.get('author'),
                content_type: comment.get('content_type'),
                object_id: comment.get('object_id'),
                text: comment.get('text'),
                created: comment.get('created'),
                updated: comment.get('updated'),
                deleted: comment.get('deleted') ? 'True' : 'False',
                pending_moderation: comment.get('pending_moderation') ? 'True' : 'False',
                parent: comment.get('parent')
            };

            return data;
        },

        delete_: function (comment) {
            $.ajax({
                type: 'delete',
                url: nc_app.commentsApiUrl + comment.get('id') + '/',
                timeout: nc_app.ajaxTimeout,
                success: function () {
                    comment.set('deleted', true);
                }
            });
        },

        undelete: function (comment) {
            var data = this.dump(comment);

            data.deleted = 'False';

            $.ajax({
                type: 'put',
                url: nc_app.commentsApiUrl + data.id + '/',
                data: data,
                timeout: nc_app.ajaxTimeout,
                success: function (response) {
                    comment.set('deleted', response.deleted);
                },
                error: function (response) {
                    const text = JSON.parse(response.responseText)[0];
                    $.toast({
                        text: text,
                        showHideTransition: 'slide',
                        allowToastClose: true,
                        position: 'top-right',
                        loader: false,
                        hideAfter: false,
                        icon: 'error',
                    });
                }
            });
        },

        startEditing: function (comment) {
            comment.set('original_text', comment.get('text'));
            comment.set('editing', true);
            comment.set('replying', false);
        },

        cancelEditing: function (comment) {
            comment.set('text', comment.get('original_text'));
            comment.set('editing', false);
            this.highlightCode(comment);
        },

        saveEdit: function (comment) {
            const data = this.dump(comment);
            const self = this;

            comment.set('submitting', true);
            $.ajax({
                type: 'put',
                url: nc_app.commentsApiUrl + data.id + '/',
                data: data,
                timeout: nc_app.ajaxTimeout,
                success: function () {
                    comment.set('editing', false);
                    comment.set('submitting', false);
                    self.highlightCode(comment);
                }
            });
        },

        startReplying: function (comment) {
            comment.set('replying', true);
            comment.set('editing', false);
        },

        cancelReplying: function (comment) {
            comment.set('replying', false);
        },

        saveReply: function (comment, parent) {
            const self = this,
                  data = self.dump(comment);

            data['created'] = '1970-01-01';
            data['updated'] = '1970-01-01';

            parent.set('submitting', true);

            $.ajax({
                type: 'post',
                url: nc_app.commentsApiUrl,
                data: data,
                timeout: nc_app.ajaxTimeout,
                success: function (response) {
                    parent.set('replying', false);
                    parent.set('submitting', false);

                    const new_comment = nc_app.Comment.create(response);
                    new_comment.set('author_username', nc_app.realName || nc_app.username);
                    new_comment.set('author_url', nc_app.usersUrl + nc_app.username);
                    new_comment.set('authorIsRequestingUser', true);
                    self.addComment(new_comment);
                    self.set('firstCommentAdded', true);
                }
            });
        },

        like: function (comment) {
            comment.set('liking', true);

            $.ajax({
                type: 'post',
                url: nc_app.togglepropertiesApiUrl,
                data: {
                    property_type: 'like',
                    content_type: nc_app.nestedcommentsContentTypeId,
                    object_id: comment.id,
                    user: nc_app.userId
                },
                timeout: nc_app.ajaxTimeout,
                success: function (response) {
                    comment.set('liking', false);
                    comment.set('likes', comment.likes.concat([nc_app.userId]));
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var errors = JSON.parse(XMLHttpRequest.responseText).non_field_errors;

                    if (!!errors) {
                        errors.forEach(function (error) {
                            if (error === "User does not have the required permissions to like this object") {
                                $('#cant-like').modal('show');
                            }
                        });
                    } else if (XMLHttpRequest.status === 401) {
                        window.location.href = "/account/login/?next=" + encodeURI(nc_app.path + '#c' + comment.id);
                        return;
                    }

                    comment.set('liking', false);
                }
            });
        },

        unlike: function (comment) {
            comment.set('unliking', true);

            $.ajax({
                type: 'get',
                url: nc_app.togglepropertiesApiUrl +
                    "?property_type=like" +
                    "&content_type=" + nc_app.nestedcommentsContentTypeId +
                    "&object_id=" + comment.id +
                    "&user=" + nc_app.userId,
                timeout: nc_app.ajaxTimeout,
                success: function (response) {
                    var togglePropertyId = response.results[0].pk;

                    $.ajax({
                        type: 'delete',
                        url: nc_app.togglepropertiesApiUrl + togglePropertyId + "/",
                        timeout: nc_app.ajaxTimeout,
                        success: function () {
                            comment.set('unliking', false);
                            comment.set('likes', comment.likes.filter(function (userId) {
                                return userId !== nc_app.userId
                            }));
                        },
                        error: function (XMLHttpRequest, textStatus, errorThrown) {
                            var errors = JSON.parse(XMLHttpRequest.responseText);
                            errors.forEach(function (error) {
                                if (error === "Cannot remove this like") {
                                    $('#cant-unlike').modal('show');
                                }
                            });
                            comment.set('unliking', false);
                        }
                    });
                }
            });
        },

        approve: function (comment) {
            comment.set('loading', true);

            $.ajax({
                type: 'post',
                url: nc_app.commentsApiUrl + comment.get('id') + '/approve/',
                timeout: nc_app.ajaxTimeout,
                success: function () {
                    comment.set('loading', false);
                    comment.set('pending_moderation', false);
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    comment.set('loading', false);
                }
            });
        },

        reportAbuse: function (comment) {
            comment.set('loading', true);

            astrobin_common.abuse_report_modal_show().then(
                function (data) {
                    astrobin_common.abuse_report_modal_set_loading();

                    $.ajax({
                        type: 'post',
                        url: '{0}{1}/report-abuse/'.format(nc_app.commentsApiUrl, comment.get('id')),
                        data: {
                            'reason': data.reason,
                            'additional_information': data.additionalInformation
                        },
                        timeout: nc_app.ajaxTimeout,
                        success: function () {
                            comment.set('loading', false);
                            comment.set('deleted', true);
                            comment.set('pending_moderation', false);

                            astrobin_common.abuse_report_modal_hide();
                        },
                        error: function (response) {
                            const text = JSON.parse(response.responseText)[0];
                            $.toast({
                                text: text,
                                showHideTransition: 'slide',
                                allowToastClose: true,
                                position: 'top-right',
                                loader: false,
                                hideAfter: false,
                                icon: 'error',
                            });

                            comment.set('loading', false);

                            astrobin_common.abuse_report_modal_hide();
                        }
                    });
                },
                function () {
                    comment.set('loading', false);
                    astrobin_common.abuse_report_modal_hide();
                }
            );
        },

        saveNewComment: function (comment) {
            const self = this,
                  data = self.dump(comment);

            // Some fake data to work around some djangorestframework
            // deficiencies.
            data['created'] = '1970-01-01';
            data['updated'] = '1970-01-01';
            data['id'] = null;
            data['parent'] = null;

            comment.set('submitting', true);

            return $.ajax({
                type: 'post',
                url: nc_app.commentsApiUrl,
                data: data,
                timeout: nc_app.ajaxTimeout,
                success: function (response) {
                    comment.set('submitting', false);

                    const new_comment = nc_app.Comment.create(response);
                    new_comment.set('author_username', nc_app.realName || nc_app.username);
                    new_comment.set('author_url', nc_app.usersUrl + nc_app.username);
                    new_comment.set('authorIsRequestingUser', true);
                    self.addComment(new_comment);
                    self.set('firstCommentAdded', true);
                }
            });
        },

        highlightCode: function (comment) {
            setTimeout(() => {
                const $elements = document.getElementById(`c${comment.id}`).querySelectorAll("pre code");
                for (const $element of $elements) {
                    astrobin_common.highlightCodeForElement($element);
                }
            }, 500);
        }
    });

    nc_app.CommentsView = Em.View.extend({
        templateName: 'comments',
        classNames: ['comments']
    });

    nc_app.SingleCommentView = Em.View.extend({
        templateName: 'singleComment',
        classNames: ['comment']
    });

    nc_app.PendingModerationInfoForContentObjectOwnerView = Em.View.extend({
        templateName: 'pending-moderation-info-for-content-object-owner'
    });

    nc_app.ModerationRequestedButUnneeded = Em.View.extend({
        templateName: 'moderation-requested-but-unneeded'
    });

    nc_app.PendingModerationInfoForCommentOwnerView = Em.View.extend({
        templateName: 'pending-moderation-info-for-comment-owner'
    });

    nc_app.PendingModerationInfoForEveryoneElseView = Em.View.extend({
        templateName: 'pending-moderation-info-for-everyone-else'
    });

    nc_app.SingleCommentRenderView = Em.View.extend({
        templateName: 'singleCommentRender',
        editingBinding: 'node.editing',
        replyingBinding: 'node.replying',
        submittingBinding: 'node.submitting',
        disallowSavingBinding: 'node.disallowSaving',
        collapsed: false,
        userIsSuperuser: null,
        userIsAuthenticated: null,

        scroll: function () {
            /* Using a timeout here, because the "reply" view is still
             * visible, so we give it time to hide before scrolling. */
            var self = this;
            setTimeout(function () {
                $('html, body').animate({
                    // 60 pixel is the fixed navigation bar
                    scrollTop: self.$().offset().top - 60
                }, 1000);
            }, 250);
        },

        hilight: function () {
            // There can be only one.
            $('.comment.hilight').removeClass('hilight');
            this.$().addClass('hilight');
        },

        didInsertElement: function () {
            this.set('userIsSuperuser', nc_app.userIsSuperuser);
            this.set('userIsAuthenticated', nc_app.userIsAuthenticated);

            var self = this,
                hilighted_comment = location.hash.substr(1);

            if (nc_app.get('router.commentsController.firstCommentAdded')) {
                $('.comment.newlyAdded').removeClass('newlyAdded');
                self.$().addClass('newlyAdded');
                self.scroll();
            }

            if (hilighted_comment === self.get('node.cid')) {
                self.hilight();
                self.scroll();
            }

            function nodeReady() {
                if (!!CKEDITOR.htmlParser.fragment.fromBBCode) {
                    self.set('node.html', astrobin_common.utils.BBCodeToHtml(
                        self.$('textarea').val(), "comments", nc_app.languageCode)
                    );
                    self.set('node.ready', true);
                    
                    // Apply stored translations and check if translation button should be shown
                    setTimeout(function() {
                        self.checkTranslation();
                    }, 100);
                } else {
                    setTimeout(function () {
                        nodeReady();
                    }, 100);
                }
            }

            setTimeout(function () {
                nodeReady();
            }, 1);
        },
        
        // Check if translation is needed and possibly load saved translation
        checkTranslation: function() {
            const node = this.get('node');
            const commentId = node.get('id');
            
            // Skip for deleted comments
            if (node.get('deleted')) {
                return;
            }
            
            // Get user language
            const userLang = (nc_app.languagecode || 'en').split('-')[0].toLowerCase();
            
            // Get comment language
            const commentLang = node.get('detected_language') || 'en';
            
            // If languages don't match and user is authenticated, show translate button
            if (userLang !== commentLang && commentLang !== 'auto' && commentLang !== '' && nc_app.userIsAuthenticated) {
                $(`#${node.get('translateButtonId')}`).css('display', 'inline-block');
                
                // Check if we have a saved translation
                const savedTranslations = astrobin_common.translationSystem.getTranslations('comment');
                const translation = savedTranslations[commentId];
                
                if (translation && translation.translated && translation.content) {
                    // Apply saved translation
                    const $originalContent = $(`#${node.get('originalContentId')}`);
                    const $translatedContent = $(`#${node.get('translatedContentId')}`);
                    const $button = $(`#${node.get('translateButtonId')}`);
                    
                    // Set translated content
                    $translatedContent.html(translation.content);
                    
                    // Show translation
                    $originalContent.hide();
                    $translatedContent.css('display', 'block');
                    
                    // Update button text
                    $button.find('.translate-text').text(window.astrobin_nestedcomments_i18n.seeOriginal);
                }
            }
        },

        loginAndGoToComment: function () {
            window.location.href = '/account/login/?next={0}#{1}'.format(nc_app.path, this.get('node.cid'));
        },

        link: function () {
            this.hilight();
            window.location.assign(window.location.pathname + '#' + this.get('node.cid'));
            this.scroll();
        },

        collapse: function () {
            this.set('collapsed', true);
        },

        uncollapse: function () {
            this.set('collapsed', false);
        },

        delete_: function () {
            nc_app.get('router.commentsController').delete_(this.get('node'));
        },

        undelete: function () {
            nc_app.get('router.commentsController').undelete(this.get('node'));
        },

        edit: function () {
            nc_app.get('router.commentsController').startEditing(this.get('node'));
        },

        saveEdit: function () {
            nc_app.get('router.commentsController').saveEdit(this.get('node'));
        },

        cancelEditing: function () {
            nc_app.get('router.commentsController').cancelEditing(this.get('node'));
        },

        reply: function () {
            nc_app.get('router.commentsController').startReplying(this.get('node'));
        },

        like: function () {
            nc_app.get('router.commentsController').like(this.get('node'));
        },

        unlike: function () {
            nc_app.get('router.commentsController').unlike(this.get('node'));
        },

        approve: function () {
            nc_app.get('router.commentsController').approve(this.get('node'));
        },

        reportAbuse: function () {
            nc_app.get('router.commentsController').reportAbuse(this.get('node'));
        },
        
        translateComment: function() {
            const node = this.get('node');
            const commentId = node.get('id');
            const $originalContent = $(`#${node.get('originalContentId')}`);
            const $translatedContent = $(`#${node.get('translatedContentId')}`);
            const $button = $(`#${node.get('translateButtonId')}`);
            
            // Don't do anything if already in progress
            if ($button.find('.icon-spinner').length > 0) {
                return;
            }
            
            // If already translated, toggle back to original
            if ($translatedContent.is(':visible')) {
                $translatedContent.hide();
                $originalContent.show();
                // No need to change icon class, it's already icon-file-alt
                $button.find('.translate-text').text(window.astrobin_nestedcomments_i18n.translate);
                // Update storage
                astrobin_common.translationSystem.saveTranslation('comment', commentId, false);
                return;
            }
            
            // If content already translated but hidden, just show it
            if ($translatedContent.html() && $translatedContent.html().trim().length > 0) {
                $originalContent.hide();
                $translatedContent.css('display', 'block');  // Force show with CSS
                // Keep the icon-file-alt class for consistency
                $button.find('.translate-text').text(window.astrobin_nestedcomments_i18n.seeOriginal);
                // Update storage
                astrobin_common.translationSystem.saveTranslation(
                    'comment', 
                    commentId, 
                    true, 
                    $translatedContent.html(), 
                    node.get('detected_language')
                );
                return;
            }
            
            // Otherwise, request translation
            $button.find('i').removeClass('icon-file-alt').addClass('icon-spinner');
            
            const originalText = $originalContent.html();
            // Use Django's LANGUAGE_CODE first, with browser language as fallback
            const djangoLang = nc_app.languagecode || 'en';
            const detectedLanguage = node.get('detected_language') || 'auto';
            
            // Use the translation system
            astrobin_common.translationSystem.translateContent({
                text: originalText,
                sourceLanguage: detectedLanguage,
                targetLanguage: djangoLang,
                format: 'html',
                itemType: 'comment',
                itemId: commentId,
                onStart: function() {
                    // Already handled by setting spinner above
                },
                onSuccess: function(translation) {
                    // Set the translated content and make visible
                    $translatedContent.html(translation);
                    
                    // Hide original, show translated
                    $originalContent.hide();
                    $translatedContent.css('display', 'block');  // Force show with CSS
                    
                    // Update button UI
                    $button.find('i').removeClass('icon-spinner').addClass('icon-file-alt');
                    $button.find('.translate-text').text(window.astrobin_nestedcomments_i18n.seeOriginal);
                },
                onError: function(error) {
                    console.error("Translation error:", error);
                    $button.find('i').removeClass('icon-spinner').addClass('icon-file-alt');
                    alert(window.astrobin_nestedcomments_i18n.translationFailed);
                }
            });
        },

        saveReply: function () {
            nc_app.get('router.commentsController').saveReply(
                this.get('replyComment'),
                this.get('node'));
        },

        cancelReplying: function () {
            nc_app.get('router.commentsController').cancelReplying(this.get('node'));
        },

        EditView: nc_app.TextareaView.extend({
            templateName: 'edit',
            tagName: 'form',
            submittingBinding: 'parentView.submitting',
            disallowSavingBinding: 'parentView.disallowSaving',

            didInsertElement: function () {
                this.set('type', this.TypeEnum.EDIT);
                this.initTextarea();
            },

            save: function () {
                this.removeSyncInterval();
                this.sync(true);
                this.get('parentView').saveEdit();
            },

            cancel: function () {
                this.get('parentView').cancelEditing();
                this.removeSyncInterval();
            },

            SaveEditButtonView: nc_app.SaveButtonView.extend()
        }),

        ReplyView: nc_app.TextareaView.extend({
            templateName: 'reply',
            tagName: 'form',
            submittingBinding: 'parentView.submitting',
            disallowSavingBinding: 'comment.disallowSaving',
            userIsAuthenticated: null,

            didInsertElement: function () {
                this.set('userIsAuthenticated', nc_app.userIsAuthenticated);

                var comment = this.get('parentView.controller').createComment();
                comment.set('parent', this.get('parentView.node.id'));
                this.set('comment', comment);
                this.set('parentView.replyComment', comment);

                this.set('type', this.TypeEnum.REPLY);
                this.initTextarea();
            },

            cancel: function () {
                this.get('parentView').cancelReplying();
                this.removeSyncInterval();
            },

            save: function () {
                this.removeSyncInterval();
                this.sync(true);
                this.get('parentView').saveReply();
            },

            SaveReplyButtonView: nc_app.SaveButtonView.extend()
        })
    });

    nc_app.TimeagoView = Em.View.extend({
        templateName: 'timeago',
        tagName: 'abbr',
        classNames: ['timeago'],
        attributeBindings: ['title'],
        titleBinding: "value",

        didInsertElement: function () {
            this._super();
            this.$().attr("title", this.$().attr("title") + " UTC");
            this.$().timeago();
        }
    });

    nc_app.LoaderView = Em.View.extend({
        tagName: 'span',
        classNames: ['loader'],
        loaderUrl: null,
        templateName: 'loader',

        didInsertElement: function () {
            this.set('loaderUrl', nc_app.loaderGif);
        }
    });


    /*******************************************************************
     * Router
     *******************************************************************/

    nc_app.Router = Em.Router.extend({
        location: 'none',

        root: Em.Route.extend({
            index: Em.Route.extend({
                route: '/',
                connectOutlets: function (router) {
                    var ctrl = router.get('applicationController');
                    ctrl.connectOutlet('top-level', 'topLevel');
                    ctrl.connectOutlet('comments', 'comments');

                    router.get('commentsController').find();
                }
            })
        })
    });

    window.NestedCommentsApp = nc_app;

    // Initialize hidden CKEDITOR to access BBCode transformation methods.
    ckeditorOptions = astrobin_common.utils.ckeditorOptions("comments", languageCode);
    CKEDITOR.replace("hidden-textarea", ckeditorOptions);
});
