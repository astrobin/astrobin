$(function() {

    /*******************************************************************
    * APP
    *******************************************************************/

    var nc_app = Em.Application.create({
        rootElement: '#nested-comments',
        baseApiURL: '/api/v2/nestedcomments/',
        ready: function() {
            this.user_id = parseInt($('#nested-comments-user-id').attr('data-value'));
            this.page_url = $('#nested-comments-page-url').attr('data-value');
            this.static_url = $('#nested-comments-static-url').attr('data-value');
        },
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
        text: null,
        created: null,
        updated: null,
        deleted: null,
        parent: null,

        // Fields that we compute manually
        author_username: null,
        authorIsRequestingUser: null,
        editing: false,
        submitting: false,
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
     });


    /*******************************************************************
    * Views and Controllers
    *******************************************************************/
   
    nc_app.ApplicationController = Em.Controller.extend();
    nc_app.ApplicationView = Em.View.extend({
        templateName: "nested-comments"
    });


    nc_app.TopLevelController = Em.Controller.extend();
    nc_app.topLevelController = nc_app.TopLevelController.create();
    nc_app.TopLevelView = Em.View.extend({
        templateName: "top-level"
    });


    nc_app.CommentsController = Em.Controller.extend({
        tree: null,

        addComment: function(comment) {
            var self = this;

            if (self.get('tree') == null) {
                self.set('tree', new Arboreal());
            }

            // djangorestframework has trouble with null values:
            // https://github.com/tomchristie/django-rest-framework/pull/356
            if (comment.parent == null || comment.parent == comment.id) {
                self.get('tree').appendChild(comment);
            } else {
                var parent = self.tree.find(function(node) {
                    return comment.parent = node.data.id;
                });

                if (parent != null) {
                    parent.appendChild(comment);
                }
            }
        },

        fetchAuthor: function(comment) {
            var url = nc_app.baseApiURL + 'users/' + comment.author + '/';

            $.ajax({
                url: url,
                cache: false,
                timeout: 10000,
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
                    timeout: 10000,
                    dataType: 'json',
                    data: data,
                    success: function(response) {
                        $.each(response.results, function(i, nc_data) {
                            var comment = nc_app.Comment.create(nc_data);
                            comment.set('authorIsRequestingUser', nc_app.user_id == comment.get('author'));
                            self.fetchAuthor(comment);
                            self.addComment(comment);
                        });

                        self.fetchComments(response.next, data);
                    }
                });
            }
        },

        find: function() {
            var self = this,
                content_type_id = $(nc_app.rootElement).attr('data-content-type-id'),
                object_id = $(nc_app.rootElement).attr('data-object-id'),
                url = nc_app.baseApiURL + 'nestedcomments/',
                data = {
                    'content_type': content_type_id,
                    'object_id': object_id,
                };

            self.fetchComments(url, data);
            return self.content;
        },

        dump: function(comment) {
            var data = {
                id: comment.get('id'),
                author: comment.get('author'),
                content_type: comment.get('content_type'),
                object_id: comment.get('object_id'),
                text: comment.get('text'),
                created: comment.get('created'),
                updated: comment.get('updated'),
                deleted: comment.get('deleted') ? 'True' : 'False',
                parent: comment.get('parent')
            }

            // djangorestframework has trouble with null values:
            // https://github.com/tomchristie/django-rest-framework/pull/356
            if (comment.get('parent'))
                data['parent'] = comment.get('parent');
            else
                data['parent'] = comment.get('id');

            return data;
        },

        delete: function(comment) {
            $.ajax({
                type: 'delete',
                url: nc_app.baseApiURL + 'nestedcomments/' + comment.get('id') + '/',
                timeout: 10000,
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
                url: nc_app.baseApiURL + 'nestedcomments/' + data.id + '/',
                data: data,
                timeout: 10000,
                success: function(response) {
                    comment.set('deleted', response.deleted);
                }
            });
        },

        startEditing: function(comment) {
            comment.set('original_text', comment.get('text'));
            comment.set('editing', true);
        },

        cancelEditing: function(comment) {
            comment.set('editing', false);
            comment.set('text', comment.get('original_text'));
        },

        save: function(comment) {
            var data = this.dump(comment);

            comment.set('submitting', true);
            $.ajax({
                type: 'put',
                url: nc_app.baseApiURL + 'nestedcomments/' + data.id + '/',
                data: data,
                timeout: 10000,
                success: function() {
                    comment.set('editing', false);
                    comment.set('submitting', false);
                }
            });
        }
    });
    nc_app.commentsController = nc_app.CommentsController.create();

    nc_app.CommentsView = Em.View.extend({
        templateName: 'comments',
        classNames: ['comments'],

        SingleCommentView: Em.View.extend({
            templateName: 'singleComment',
            classNames: ['comment'],

            EditView: Em.View.extend({
                templateName: 'edit',
                tagName: 'form',
                classNames: ['form-horizontal'],
                loader_gif: 'images/ajax-loader.gif',

                didInsertElement: function() {
                    this.loader_url = nc_app.static_url + this.loader_gif;
                },

                save: function(comment) {
                    this.get('parentView.controller').save(comment);
                },

                SaveButtonView: Em.View.extend({
                    templateName: 'saveButton',
                    tagName: 'a',
                    classNames: ['btn btn-mini btn-primary'],
                    attributeBindings: ['href'],

                    href: '#',

                    save: function(comment) {
                        this.get('parentView').save(comment);
                    },

                    click: function(event) {
                        this.save(this.comment);
                        event.preventDefault();
                    }
                })
            })
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
                },

                deleteComment: function(router, event) {
                    router.get('commentsController').delete(event.view.node.data);
                },
                undeleteComment: function(router, event) {
                    router.get('commentsController').undelete(event.view.node.data);
                },
                editComment: function(router, event) {
                    router.get('commentsController').startEditing(event.view.node.data);
                },
                cancelEditingComment: function(router, event) {
                    router.get('commentsController').cancelEditing(event.view.comment);
                }
            })
        })
    });

    window.NestedCommentsApp = nc_app;
});
