$(function() {

    /*******************************************************************
    * APP
    *******************************************************************/

    var nc_app = Em.Application.create({
        rootElement: '#nested-comments',
        ajaxTimeout: 20000,

        baseApiUrl: '/api/v2/',
        loaderGif: 'images/ajax-loader.gif',

        ready: function() {
            this.commentsApiUrl = this.baseApiUrl + 'nestedcomments/nestedcomments/';
            this.authorsApiUrl = this.baseApiUrl + 'common/users/';

            this.userId = parseInt($('#nested-comments-user-id').attr('data-value'));
            this.username = $('#nested-comments-user-name').attr('data-value');
            this.userIsAuthenticated = $('#nested-comments-user-is-authenticated').attr('data-value') == "True";
            this.page_url = $('#nested-comments-page-url').attr('data-value');
            this.staticUrl = $('#nested-comments-static-url').attr('data-value');
            this.contentTypeId = $(this.rootElement).attr('data-content-type-id');
            this.objectId = $(this.rootElement).attr('data-object-id');

            this.markdownConverter = new Markdown.Converter();
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
        parent: null,

        // Fields that we compute manually
        children: null,
        author_username: null,
        authorIsRequestingUser: null,
        editing: null,
        submitting: null,
        original_text: null, // Text before editing starts

        // Computed properties
        cid: function() {
            return 'c' + this.get('id');
        }.property('id'),

        url: function() {
            return nc_app.page_url + '#' + this.get('cid');
        }.property('id'),

        allowEditing: function() {
            return this.get('deleted') == false;
        }.property('deleted'),

        markdown: function() {
            var converter = nc_app.markdownConverter;
            var html = converter.makeHtml(this.get('text'));

            return html;
        }.property('text'),

        hasText: function() {
            return this.get('text') != '';
        }.property('text'),

        disallowSaving: function() {
            var submitting = this.get('submitting');
            var hasText = this.get('hasText');

            return submitting || !hasText;
        }.property('submitting', 'text'),

        // Functions
        init: function() {
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

        click: function(event) {
            this.get('parentView').save();
            event.preventDefault();
        }
    });


    nc_app.TopLevelController = Em.Controller.extend();
    nc_app.TopLevelView = Em.View.extend({
        templateName: "top-level",
        classNames: 'comment',
        submittingBinding: 'comment.submitting',
        disallowSavingBinding: 'comment.disallowSaving',
        userIsAuthenticated: null,

        reset: function() {
            var comment = nc_app.get('router.commentsController').createComment();
            this.set('comment', comment);
        },

        didInsertElement: function() {
            this.reset();
            this.set('userIsAuthenticated', nc_app.userIsAuthenticated);
        },

        save: function() {
            var self = this;
            nc_app.get('router.commentsController').saveNewComment(self.get('comment'))
                .then(function(response, statusText, xhr) {
                    self.reset();
                });
        },

        SaveCommentButtonView: nc_app.SaveButtonView.extend()
    });


    nc_app.CommentsController = Em.ArrayController.extend({
        content: [], // The top-level comments
        ready: false,
        firstCommentAdded: false,

        findCommentById: function(id, root) {
            var self = this;

            if (root === undefined) {
                for (var i = 0; i < self.content.length; i++) {
                    var comment = self.findCommentById(id, self.content[i]);
                    if (comment !== undefined)
                        return comment;
                }
            } else {
                if (root.get('id') == id)
                    return root;
                for (var i = 0; i < root.get('children').length; i++) {
                    var comment = self.findCommentById(id, root.get('children')[i]);
                    if (comment !== undefined)
                        return comment;
                }
            }
        },

        addComment: function(comment) {
            var self = this;

            if (comment.get('parent') == null) {
                self.pushObject(comment);
            } else {
                var parent = self.findCommentById(comment.get('parent'));
                if (parent !== undefined) {
                    parent.get('children').pushObject(comment);
                } else
                    self.pushObject(comment);
            }
        },

        createComment: function() {
            return nc_app.Comment.create({
                author: nc_app.userId,
                content_type: nc_app.contentTypeId,
                object_id: nc_app.objectId,
                text: ''
            });
        },

        fetchAuthor: function(comment) {
            var url = nc_app.authorsApiUrl + comment.author + '/';

            $.ajax({
                url: url,
                timeout: nc_app.ajaxTimeout,
                dataType: 'json',
                success: function(response) {
                    comment.set('author_username', response.username);
                }
            });
        },

        fetchComments: function(url, data) {
            var self = this;

            if (url != null) {
                $.ajax({
                    url: url,
                    cache: false,
                    timeout: nc_app.ajaxTimeout,
                    dataType: 'json',
                    data: data,
                    success: function(response) {
                        $.each(response.results, function(i, nc_data) {
                            var comment = nc_app.Comment.create(nc_data);
                            comment.set('authorIsRequestingUser', nc_app.userId == comment.get('author'));
                            self.fetchAuthor(comment);
                            self.addComment(comment);
                        });

                        if (!self.get('ready')) {
                            self.set('ready', true);
                        }

                        self.fetchComments(response.next, data);
                    }
                });
            }
        },

        find: function() {
            var self = this,
                data = {
                    'content_type': nc_app.contentTypeId,
                    'object_id': nc_app.objectId
                };

            self.fetchComments(nc_app.commentsApiUrl, data);
            return self.content;
        },

        dump: function(comment) {
            data = {
                id: comment.get('id'),
                author: comment.get('author'),
                content_type: comment.get('content_type'),
                object_id: comment.get('object_id'),
                text: comment.get('text'),
                created: comment.get('created'),
                updated: comment.get('updated'),
                deleted: comment.get('deleted') ? 'True' : 'False',
                parent: comment.get('parent')
            };

            if (data.parent == null)
                data.parent = 0;

            return data;
        },

        delete_: function(comment) {
            $.ajax({
                type: 'delete',
                url: nc_app.commentsApiUrl + comment.get('id') + '/',
                timeout: nc_app.ajaxTimeout,
                success: function() {
                    comment.set('deleted', true);
                }
            });
        },

        undelete: function(comment) {
            var data = this.dump(comment);

            data.deleted = 'False';

            $.ajax({
                type: 'put',
                url: nc_app.commentsApiUrl + data.id + '/',
                data: data,
                timeout: nc_app.ajaxTimeout,
                success: function(response) {
                    comment.set('deleted', response.deleted);
                }
            });
        },

        startEditing: function(comment) {
            comment.set('original_text', comment.get('text'));
            comment.set('editing', true);
            comment.set('replying', false);
        },

        cancelEditing: function(comment) {
            comment.set('text', comment.get('original_text'));
            comment.set('editing', false);
        },

        saveEdit: function(comment) {
            var data = this.dump(comment);
            if (data.parent == null)
                data.parent = 0;

            comment.set('submitting', true);
            $.ajax({
                type: 'put',
                url: nc_app.commentsApiUrl + data.id + '/',
                data: data,
                timeout: nc_app.ajaxTimeout,
                success: function() {
                    comment.set('editing', false);
                    comment.set('submitting', false);
                }
            });
        },

        startReplying: function(comment) {
            comment.set('replying', true);
            comment.set('editing', false);
        },

        cancelReplying: function(comment) {
            comment.set('replying', false);
        },

        saveReply: function(comment, parent) {
            var self = this,
                data = self.dump(comment);

            data['created'] = '1970-01-01';
            data['updated'] = '1970-01-01';
        
            parent.set('submitting', true);

            $.ajax({
                type: 'post',
                url: nc_app.commentsApiUrl,
                data: data,
                timeout: nc_app.ajaxTimeout,
                success: function(response) {
                    parent.set('replying', false);
                    parent.set('submitting', false);

                    var new_comment = nc_app.Comment.create(response);
                    new_comment.set('author_username', nc_app.username);
                    new_comment.set('authorIsRequestingUser', true);
                    self.addComment(new_comment);
                    self.set('firstCommentAdded', true);
                }
            });
        },

        saveNewComment: function(comment) {
            var self = this,
                data = self.dump(comment);

            // Some fake data to work around some djangorestframework
            // deficiencies.
            data['created'] = '1970-01-01';
            data['updated'] = '1970-01-01';
            data['id'] = 0;
            data['parent'] = 0;
 
            comment.set('submitting', true);

            return $.ajax({
                type: 'post',
                url: nc_app.commentsApiUrl,
                data: data,
                timeout: nc_app.ajaxTimeout,
                success: function(response) {
                    comment.set('submitting', false);

                    var new_comment = nc_app.Comment.create(response);
                    new_comment.set('author_username', nc_app.username);
                    new_comment.set('authorIsRequestingUser', true);
                    self.addComment(new_comment);
                    self.set('firstCommentAdded', true);
                }
            });
        }
    });

    nc_app.CommentsView = Em.View.extend({
        templateName: 'comments',
        classNames: ['comments']
    });


    nc_app.SingleCommentView = Em.View.extend({
        templateName: 'singleComment',
        classNames: ['comment'],
        editingBinding: 'node.editing',
        replyingBinding: 'node.replying',
        submittingBinding: 'node.submitting',
        disallowSavingBinding: 'node.disallowSaving',
        collapsed: false,

        scroll: function() {
            /* Using a timeout here, because the "reply" view is still
             * visible, so we give it time to hide before scrolling. */
            var self = this;
            setTimeout(function() {
                $('html, body').animate({
                    // 55 pixel is the fixed navigation bar
                    scrollTop: self.$().offset().top - 55
                }, 1000);
            }, 250);
        },

        hilight: function() {
            // There can be only one.
            $('.comment.hilight').removeClass('hilight');
            this.$().addClass('hilight');
        },

        didInsertElement: function() {
            var self = this,
                hilighted_comment = location.hash.substr(1);

            if (nc_app.get('router.commentsController.firstCommentAdded')) {
                $('.comment.newlyAdded').removeClass('newlyAdded');
                self.$().addClass('newlyAdded');
                self.scroll();
            }

            if (hilighted_comment == self.get('node.cid')) {
                self.hilight();
                self.scroll();
            }
        },

        link: function() {
            this.hilight();
            window.location.href = '#' + this.get('node.cid');
            this.scroll();
        },

        collapse: function() {
            this.set('collapsed', true);
        },

        uncollapse: function() {
            this.set('collapsed', false);
        },

        delete_: function() {
            nc_app.get('router.commentsController').delete_(this.get('node'));
        },

        undelete: function() {
            nc_app.get('router.commentsController').undelete(this.get('node'));
        },

        edit: function() {
            nc_app.get('router.commentsController').startEditing(this.get('node'));
        },

        saveEdit: function() {
            nc_app.get('router.commentsController').saveEdit(this.get('node'));
        },

        cancelEditing: function() {
            nc_app.get('router.commentsController').cancelEditing(this.get('node'));
        },

        reply: function() {
            nc_app.get('router.commentsController').startReplying(this.get('node'));
        },

        saveReply: function() {
            nc_app.get('router.commentsController').saveReply(
                this.get('replyComment'),
                this.get('node'));
        },

        cancelReplying: function() {
            nc_app.get('router.commentsController').cancelReplying(this.get('node'));
        },

        EditView: Em.View.extend({
            templateName: 'edit',
            tagName: 'form',
            submittingBinding: 'parentView.submitting',
            disallowSavingBinding: 'parentView.disallowSaving',

            didInsertElement: function() {
                this.$('textarea').focus();
            },

            save: function() {
                this.get('parentView').saveEdit();
            },

            cancel: function() {
                this.get('parentView').cancelEditing();
            },

            SaveEditButtonView: nc_app.SaveButtonView.extend()
        }),

        ReplyView: Em.View.extend({
            templateName: 'reply',
            tagName: 'form',
            submittingBinding: 'parentView.submitting',
            disallowSavingBinding: 'comment.disallowSaving',
            userIsAuthenticated: null,

            didInsertElement: function() {
                this.set('userIsAuthenticated', nc_app.userIsAuthenticated);

                var comment = this.get('parentView.controller').createComment();
                comment.set('parent', this.get('parentView.node.id'));
                this.set('comment', comment);
                this.set('parentView.replyComment', comment);

                this.$('textarea').focus();
            },

            cancel: function() {
                this.get('parentView').cancelReplying();
            },

            save: function() {
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

        didInsertElement: function() {
            this._super();
            this.$().timeago();
        }
    });

    nc_app.LoaderView = Em.View.extend({
        tagName: 'span',
        classNames: ['loader'],
        loaderUrl: null,
        templateName: 'loader',

        didInsertElement: function() {
            this.set('loaderUrl', nc_app.staticUrl + nc_app.loaderGif);
        }
    });

    nc_app.PreviewView = Em.View.extend({
        classNames: ['preview'],
        templateName: 'preview'
    });

    nc_app.FormattingHelpView = Em.View.extend({
        classNames: ['formatting-help'],
        templateName: 'formatting-help'
    });


    /*******************************************************************
    * Router
    *******************************************************************/
 
    nc_app.Router = Em.Router.extend({
        location: 'none',

        root: Em.Route.extend({
            index: Em.Route.extend({
                route: '/',
                connectOutlets: function(router) {
                    var ctrl = router.get('applicationController');
                    ctrl.connectOutlet('top-level', 'topLevel');
                    ctrl.connectOutlet('comments', 'comments');

                    router.get('commentsController').find();
                }
            })
        })
    });

    window.NestedCommentsApp = nc_app;
});
