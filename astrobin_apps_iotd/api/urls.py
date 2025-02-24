from django.conf.urls import url, include
from django.urls import re_path
from django.views.decorators.cache import never_cache
from rest_framework import routers

from astrobin_apps_iotd.api.views.current_iotd_view_set import CurrentIotdViewSet
from astrobin_apps_iotd.api.views.dismissed_image_view_set import DismissedImageViewSet
from astrobin_apps_iotd.api.views.future_iotds_view_set import FutureIotdsViewSet
from astrobin_apps_iotd.api.views.hidden_image_view_set import HiddenImageViewSet
from astrobin_apps_iotd.api.views.iotd_archive_view_set import IotdArchiveViewSet
from astrobin_apps_iotd.api.views.judgement_queue_view_set import JudgementQueueViewSet
from astrobin_apps_iotd.api.views.review_queue_view_set import ReviewQueueViewSet
from astrobin_apps_iotd.api.views.reviewer_seen_image_view_set import ReviewerSeenImageViewSet
from astrobin_apps_iotd.api.views.staff_member_settings_view_set import StaffMemberSettingsViewSet
from astrobin_apps_iotd.api.views.stats_view_set import StatsViewSet
from astrobin_apps_iotd.api.views.submission_queue_view_set import SubmissionQueueViewSet
from astrobin_apps_iotd.api.views.submission_view_set import SubmissionViewSet
from astrobin_apps_iotd.api.views.submitter_seen_image_view_set import SubmitterSeenImageViewSet
from astrobin_apps_iotd.api.views.top_pick_archive_view_set import TopPickArchiveViewSet
from astrobin_apps_iotd.api.views.top_pick_nominations_archive_view_set import TopPickNominationsArchiveViewSet
from astrobin_apps_iotd.api.views.vote_view_set import VoteViewSet
from astrobin_apps_iotd.views import ImageStats

router = routers.DefaultRouter()

router.register(r'staff-member-settings', StaffMemberSettingsViewSet, basename='staff-member-settings')
router.register(r'hidden-image', HiddenImageViewSet, basename='hidden-image')
router.register(r'dismissed-image', DismissedImageViewSet, basename='dismissed-image')
router.register(r'submitter-seen-image', SubmitterSeenImageViewSet, basename='submitter-seen-image')
router.register(r'reviewer-seen-image', ReviewerSeenImageViewSet, basename='reviewer-seen-image')

router.register(r'submission-queue', SubmissionQueueViewSet, basename='submission-queue')
router.register(r'submission', SubmissionViewSet, basename='submission-detail')

router.register(r'review-queue', ReviewQueueViewSet, basename='review-queue')
router.register(r'vote', VoteViewSet, basename='vote-detail')

router.register(r'judgement-queue', JudgementQueueViewSet, basename='judgement-queue')
router.register(r'future-iotds', FutureIotdsViewSet, basename='future-iotds')
router.register(r'current-iotd', CurrentIotdViewSet, basename='current-iotd')

router.register(
    r'top-pick-nominations-archive',
    TopPickNominationsArchiveViewSet,
    basename='top-pick-nominations-archive',
)
router.register(
    r'top-pick-archive',
    TopPickArchiveViewSet,
    basename='top-pick-archive',
)
router.register(
    r'iotd-archive',
    IotdArchiveViewSet,
    basename='iotd-archive',
)

router.register(r'stats', StatsViewSet, basename='stats')

urlpatterns = [
    re_path(
        r'^image-stats/(?P<image_id>\w+)/$',
        never_cache(ImageStats.as_view()),
        name='image-stats'
    ),
    url('', include(router.urls)),
]
