from django.conf.urls import url
from django.views.decorators.cache import never_cache

from astrobin_apps_json_api.user.views import MarkCorruptedImagesBannerAsSeen, RestoreDeletedImages, \
    ConfirmImageRecovery, DeleteImages, PlateSolutionOverlayOnFullDisabled, MarkClickAndDragToastAsSeen, \
    MarkForumUsageModalAsSeen
from astrobin_apps_json_api.user.views.confirm_revision_recovery import ConfirmRevisionRecovery
from astrobin_apps_json_api.user.views.delete_revisions import DeleteRevisions

urlpatterns = (
    url(r'^user/mark-corrupted-images-banner-as-seen/$', never_cache(MarkCorruptedImagesBannerAsSeen.as_view())),
    url(r'^user/restore-deleted-images/$', never_cache(RestoreDeletedImages.as_view())),
    url(r'^user/confirm-image-recovery/$', never_cache(ConfirmImageRecovery.as_view())),
    url(r'^user/confirm-revision-recovery/$', never_cache(ConfirmRevisionRecovery.as_view())),
    url(r'^user/delete-images/$', never_cache(DeleteImages.as_view())),
    url(r'^user/delete-revisions/$', never_cache(DeleteRevisions.as_view())),
    url(r'^user/plate-solution-overlay-on-full/$', never_cache(PlateSolutionOverlayOnFullDisabled.as_view())),
    url(r'^user/mark-click-and-drag-toast-as-seen/$', never_cache(MarkClickAndDragToastAsSeen.as_view())),
    url(r'^user/mark-forum-usage-modal-as-seen/$', never_cache( MarkForumUsageModalAsSeen.as_view())),
)
