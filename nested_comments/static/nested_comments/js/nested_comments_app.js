$(function() {

    /*******************************************************************
    * APP
    *******************************************************************/

    var nc_app = Em.Application.create({
        rootElement: '#nested-comments',
        baseApiURL: '/api/v2/nestedcomments/'
    });


    /*******************************************************************
    * Models
    *******************************************************************/

    nc_app.User = Em.Object.extend({
        id: null,
        username: null
    });

    nc_app.ContentType = Em.Object.extend({
        id: null,
        name: null,
        app_label: null,
        model: null
    });

    nc_app.Comment = Em.Object.extend({
        id: null,
        author: null,
        author_username: null,
        content_type: null,
        object_id: null,
        text: null,
        created: null,
        updated: null,
        deleted: null,
        parent: null,
        top: null,
        children: []
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

            if (comment.parent == null) {
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
        }
    });
    nc_app.commentsController = nc_app.CommentsController.create();
    nc_app.CommentsView = Em.View.extend({
        templateName: 'comments',
        classNames: ['comments'],
    });

    nc_app.SingleCommentView = Em.View.extend({
        templateName: 'singleComment',
        classNames: ['comment', 'comment-container']
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
                }
            })
        })
    });

    window.NestedCommentsApp = nc_app;
});
