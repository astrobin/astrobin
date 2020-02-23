from django.conf.urls import url

from astrobin_apps_json_api.user.views import MarkCorruptedImagesBannerAsSeen

urlpatterns = (
    url(r'^user/mark-corrupted-images-banner-as-seen/$', MarkCorruptedImagesBannerAsSeen.as_view()),
)
