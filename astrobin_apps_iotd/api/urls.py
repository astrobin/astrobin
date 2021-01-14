from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_iotd.api.views.hidden_image_view_set import HiddenImageViewSet
from astrobin_apps_iotd.api.views.review_queue_view_set import ReviewQueueViewSet
from astrobin_apps_iotd.api.views.submission_queue_view_set import SubmissionQueueViewSet
from astrobin_apps_iotd.api.views.submission_view_set import SubmissionViewSet
from astrobin_apps_iotd.api.views.vote_view_set import VoteViewSet

router = routers.DefaultRouter()
router.register(r'submission-queue', SubmissionQueueViewSet, base_name='submission-queue')
router.register(r'submission', SubmissionViewSet, base_name='submission-detail')
router.register(r'review-queue', ReviewQueueViewSet, base_name='review-queue')
router.register(r'vote', VoteViewSet, base_name='vote-detail')
router.register(r'hidden-image', HiddenImageViewSet, base_name='hidden-image')

urlpatterns = [
    url('', include(router.urls)),
]
