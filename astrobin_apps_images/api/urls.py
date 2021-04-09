from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_images.api.views import ImageUploadViewSet, ImageRevisionViewSet, ThumbnailGroupViewSet, \
    UncompressedSourceUploadViewSet, ImageRevisionUploadViewSet, ImageViewSet

router = routers.DefaultRouter()
router.register(r'image', ImageViewSet, base_name='image')
router.register(r'image-upload', ImageUploadViewSet, base_name='image-upload')
router.register(r'image-revision', ImageRevisionViewSet, base_name='image-revision')
router.register(r'image-revision-upload', ImageRevisionUploadViewSet, base_name='image-revision-upload')
router.register(r'thumbnail-group', ThumbnailGroupViewSet, base_name='thumbnail-group')
router.register(r'uncompressed-source-upload', UncompressedSourceUploadViewSet, base_name='uncompressed-source-upload')

urlpatterns = [
    url('', include(router.urls)),
]
