from django.conf.urls import url
from django.views.decorators.cache import never_cache

from astrobin_apps_json_api.user.views import RestoreDeletedImages, \
    DeleteImages, PlateSolutionOverlayOnFullDisabled, MarkClickAndDragToastAsSeen, \
    MarkForumUsageModalAsSeen, ToggleUseHighContrastThemeCookie
from astrobin_apps_json_api.user.views.delete_revisions import DeleteRevisions

urlpatterns = (
    url(r'^user/restore-deleted-images/$', never_cache(RestoreDeletedImages.as_view())),
    url(r'^user/delete-images/$', never_cache(DeleteImages.as_view())),
    url(r'^user/delete-revisions/$', never_cache(DeleteRevisions.as_view())),
    url(r'^user/plate-solution-overlay-on-full/$', never_cache(PlateSolutionOverlayOnFullDisabled.as_view())),
    url(r'^user/mark-click-and-drag-toast-as-seen/$', never_cache(MarkClickAndDragToastAsSeen.as_view())),
    url(r'^user/mark-forum-usage-modal-as-seen/$', never_cache(MarkForumUsageModalAsSeen.as_view())),
    url(r'^user/toggle-use-high-contrast-theme-cookie/$', never_cache(ToggleUseHighContrastThemeCookie.as_view())),
)
