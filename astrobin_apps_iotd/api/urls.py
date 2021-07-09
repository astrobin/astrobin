from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_iotd.api.views.dismissed_image_view_set import DismissedImageViewSet
from astrobin_apps_iotd.api.views.hidden_image_view_set import HiddenImageViewSet
from astrobin_apps_iotd.api.views.review_queue_view_set import ReviewQueueViewSet
from astrobin_apps_iotd.api.views.submission_queue_view_set import SubmissionQueueViewSet
from astrobin_apps_iotd.api.views.submission_view_set import SubmissionViewSet
from astrobin_apps_iotd.api.views.vote_view_set import VoteViewSet

router = routers.DefaultRouter()
router.register(r'submission-queue', SubmissionQueueViewSet, basename='submission-queue')
router.register(r'submission', SubmissionViewSet, basename='submission-detail')
router.register(r'review-queue', ReviewQueueViewSet, basename='review-queue')
router.register(r'vote', VoteViewSet, basename='vote-detail')
router.register(r'hidden-image', HiddenImageViewSet, basename='hidden-image')
router.register(r'dismissed-image', DismissedImageViewSet, basename='dismissed-image')

urlpatterns = [
    url('', include(router.urls)),
]
