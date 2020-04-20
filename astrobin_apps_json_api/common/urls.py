from django.conf.urls import url

from astrobin_apps_json_api.common.views import AppConfig

urlpatterns = (
    url(r'^common/app-config/$', AppConfig.as_view()),
)
