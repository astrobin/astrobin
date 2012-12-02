$(function() {

    /*******************************************************************
    * APP
    *******************************************************************/

    var nc_app = Em.Application.create({
        rootElement: "#nested-comments"
    });


    /*******************************************************************
    * Models
    *******************************************************************/

    nc_app.User = Em.Object.extend({
        username: null
    });

    nc_app.ContentType = Em.Object.extend({
        name: null,
        app_label: null,
        model: null
    });

    nc_app.Comment = Em.Object.extend({
       author: null,
       content_type_id: null,
       object_id: null,
       text: null,
       created: null,
       updated: null,
       deleted: null,
       parent: null
    });

    /*******************************************************************
    * Resources
    *******************************************************************/

    nc_app.UserResource = Ember.Resource.define({
        url: '/api/v2/nestedcomments/users',
        schema: {
            username: String
        }
    });

    nc_app.ContentTypeResource = Ember.Resource.define({
        url: '/api/v2/nestedcomments/contenttypes',
        schema: {
            name: String,
            app_label: String,
            model: String
        }
    });

    nc_app.CommentResource = Ember.Resource.define({
        url: '/api/v2/nestedcomments/nestedcomments',
        schema: {
            author: {
                type: nc_app.User
            },
            content_type: {
                type: nc_app.ContentType
            },
            object_id: Number,
            text: String,
            created: Date,
            updated: Date,
            deleted: Boolean,
            parent: {
                type: nc_app.Comment
            }
        }
    });


    /*******************************************************************
    * Views and Controllers
    *******************************************************************/
   
    nc_app.ApplicationController = Em.Controller.extend();
    nc_app.ApplicationView = Em.View.extend({
        templateName: "nested-comments"
    });

    nc_app.TopLevelController = Em.Controller.extend();
    nc_app.TopLevelView = Em.View.extend({
        templateName: "top-level"
    });

    nc_app.CommentsController = Em.Controller.extend();
    nc_app.CommentsView = Em.View.extend({
        templateName: "comments"
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
                    ctrl.connectOutlet('top-level', 'TopLevel');
                    ctrl.connectOutlet('comments', 'Comments');
                }
            })
        })
    });
});
