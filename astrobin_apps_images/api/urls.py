from django.conf.urls import include, url
from rest_framework import routers

from astrobin_apps_images.api.views import (
    DeepSkyAcquisitionViewSet, ImageRevisionUploadViewSet, ImageRevisionViewSet, ImageSearchViewSet, ImageUploadViewSet,
    ImageViewSet, SolarSystemAcquisitionViewSet, ThumbnailGroupViewSet, UncompressedSourceUploadViewSet,
)

router = routers.DefaultRouter()
router.register(r'image', ImageViewSet, basename='image')
router.register(r'deep-sky-acquisition', DeepSkyAcquisitionViewSet, basename='deep-sky-acquisition')
router.register(r'solar-system-acquisition', SolarSystemAcquisitionViewSet, basename='solar-system-acquisition')
router.register(r'image-upload', ImageUploadViewSet, basename='image-upload')
router.register(r'image-search', ImageSearchViewSet, basename='image-search')
router.register(r'image-revision', ImageRevisionViewSet, basename='image-revision')
router.register(r'image-revision-upload', ImageRevisionUploadViewSet, basename='image-revision-upload')
router.register(r'thumbnail-group', ThumbnailGroupViewSet, basename='thumbnail-group')
router.register(r'uncompressed-source-upload', UncompressedSourceUploadViewSet, basename='uncompressed-source-upload')

urlpatterns = [
    url('', include(router.urls)),
]
