from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_images.api.views import (
    ImageSearchView, ImageUploadViewSet, ImageRevisionViewSet,
    ThumbnailGroupViewSet,
    UncompressedSourceUploadViewSet, ImageRevisionUploadViewSet, ImageViewSet,
)

router = routers.DefaultRouter()
router.register(r'image', ImageViewSet, basename='image')
router.register(r'image-upload', ImageUploadViewSet, basename='image-upload')
router.register(r'image-search', ImageSearchView, basename='image-search')
router.register(r'image-revision', ImageRevisionViewSet, basename='image-revision')
router.register(r'image-revision-upload', ImageRevisionUploadViewSet, basename='image-revision-upload')
router.register(r'thumbnail-group', ThumbnailGroupViewSet, basename='thumbnail-group')
router.register(r'uncompressed-source-upload', UncompressedSourceUploadViewSet, basename='uncompressed-source-upload')

urlpatterns = [
    url('', include(router.urls)),
]
