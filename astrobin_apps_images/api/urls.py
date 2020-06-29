from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_images.api.views import ImageViewSet

router = routers.DefaultRouter()
router.register(r'image', ImageViewSet, base_name='image')

urlpatterns = [
    url('', include(router.urls)),
]
