from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_images.api.views import ImageViewSet, ImageRevisionViewSet, ThumbnailGroupViewSet, \
    UncompressedSourceUploadViewSet

router = routers.DefaultRouter()
router.register(r'image', ImageViewSet, base_name='image')
router.register(r'image-revision', ImageRevisionViewSet, base_name='image-revision')
router.register(r'thumbnail-group', ThumbnailGroupViewSet, base_name='thumbnail-group')
router.register(r'uncompressed-source-upload', UncompressedSourceUploadViewSet, base_name='uncompressed-source-upload')

urlpatterns = [
    url('', include(router.urls)),
]
