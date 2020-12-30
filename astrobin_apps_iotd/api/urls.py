from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_iotd.api.views.submission_queue_view_set import SubmissionQueueViewSet
from astrobin_apps_iotd.api.views.submission_view_set import SubmissionViewSet

router = routers.DefaultRouter()
router.register(r'submission-queue', SubmissionQueueViewSet, base_name='submission-queue')
router.register(r'submission', SubmissionViewSet, base_name='submission-detail')

urlpatterns = [
    url('', include(router.urls)),
]
