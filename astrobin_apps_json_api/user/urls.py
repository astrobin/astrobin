from django.conf.urls import url
from django.views.decorators.cache import never_cache

from astrobin_apps_json_api.user.views import (
    DeleteImages, EnableNewGalleryExperience, MarkClickAndDragToastAsSeen, MarkForumUsageModalAsSeen,
    NeverShowEnableNewGalleryExperience, PlateSolutionOverlayOnFullDisabled, RestoreDeletedImages,
    ToggleUseHighContrastThemeCookie,
)
from astrobin_apps_json_api.user.views.delete_revisions import DeleteRevisions
from astrobin_apps_json_api.user.views.dont_show_popup_message_again import DontShowPopupMessageAgain
from astrobin_apps_json_api.user.views.empty_trash import EmptyTrash


urlpatterns = (
    url(r'^user/restore-deleted-images/$', never_cache(RestoreDeletedImages.as_view())),
    url(r'^user/empty-trash/$', never_cache(EmptyTrash.as_view())),
    url(r'^user/delete-images/$', never_cache(DeleteImages.as_view())),
    url(r'^user/delete-revisions/$', never_cache(DeleteRevisions.as_view())),
    url(r'^user/plate-solution-overlay-on-full/$', never_cache(PlateSolutionOverlayOnFullDisabled.as_view())),
    url(r'^user/mark-click-and-drag-toast-as-seen/$', never_cache(MarkClickAndDragToastAsSeen.as_view())),
    url(r'^user/mark-forum-usage-modal-as-seen/$', never_cache(MarkForumUsageModalAsSeen.as_view())),
    url(r'^user/toggle-use-high-contrast-theme-cookie/$', never_cache(ToggleUseHighContrastThemeCookie.as_view())),
    url(r'^user/dont-show-popup-message-again/$', never_cache(DontShowPopupMessageAgain.as_view())),
    url(r'^user/enable-new-gallery-experience/$', never_cache(EnableNewGalleryExperience.as_view())),
    url(r'^user/never-show-enable-new-gallery-experience/$', never_cache(NeverShowEnableNewGalleryExperience.as_view())),
)
