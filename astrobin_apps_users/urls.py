from django.conf.urls import url

from astrobin_apps_users.views import TogglePropertyUsersAjaxView, UserSearchView

urlpatterns = (
    url(
        r'toggleproperty_users_ajax/(?P<property_type>\w+)/(?P<object_id>\d+)/(?P<content_type_id>\d+)/$',
        TogglePropertyUsersAjaxView.as_view(),
        name='astrobin_apps_users.toggleproperty_users_ajax'),
    url(
        r'user_search_ajax/$',
        UserSearchView.as_view(),
        name='astrobin_apps_users.user_search_ajax'),
)
