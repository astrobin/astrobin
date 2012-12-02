$(function() {
    var nc_app = Em.Application.create({
        rootElement: "#nested-comments"
    });

    nc_app.Comment = Em.Object.extend({
       object_id: null,
       content_type_id: null,
       author: null,
       text: null,
       created: null,
       deleted: null
    });
    
    nc_app.ApplicationController = Em.Controller.extend();
    nc_app.ApplicationView = Em.View.extend({
        templateName: "nested-comments"
    });

    nc_app.TopLevelController = Em.Controller.extend();
    app.TopLevelView = Em.View.extend({
        templateName: "top-level"
    });

    nc_app.CommentsController = Em.Controller.extend();
    nc_app.CommentsView = Em.View.extend({
        templateName: "comments"
    });

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
