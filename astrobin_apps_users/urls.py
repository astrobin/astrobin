from django.conf.urls import url

from astrobin_apps_users.views import TogglePropertyUsersAjaxView, UserSearchView, BounceIgnoreAndRetryView, \
    ComplaintRemove

urlpatterns = (
    url(
        r'toggleproperty_users_ajax/(?P<property_type>\w+)/(?P<object_id>\d+)/(?P<content_type_id>\d+)/$',
        TogglePropertyUsersAjaxView.as_view(),
        name='astrobin_apps_users.toggleproperty_users_ajax'),
    url(
        r'user_search_ajax/$',
        UserSearchView.as_view(),
        name='astrobin_apps_users.user_search_ajax'),
    url(
        r'bounce_ignore_and_retry/$',
        BounceIgnoreAndRetryView.as_view(),
        name='astrobin_apps_users.bounce_ignore_and_retry'),

    url(
        r'complaint_remove/$',
        ComplaintRemove.as_view(),
        name='astrobin_apps_users.complaint_remove'),
)
