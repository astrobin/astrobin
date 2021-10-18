from django.conf.urls import url
from django.views.decorators.cache import never_cache

from astrobin_apps_json_api.common.views import AppConfig, CkEditorUpload
from astrobin_apps_json_api.common.views.url_is_available import UrlIsAvailable

urlpatterns = (
    url(r'^common/app-config/$', AppConfig.as_view()),
    url(r'^common/ckeditor-upload/$', never_cache(CkEditorUpload.as_view())),
    url(r'^common/url-is-available/$', never_cache(UrlIsAvailable.as_view()))
)
