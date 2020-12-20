from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_iotd.api.views.submission_queue_view_set import SubmissionQueueViewSet

router = routers.DefaultRouter()
router.register(r'submission-queue', SubmissionQueueViewSet, base_name='submission-queue')

urlpatterns = [
    url('', include(router.urls)),
]
