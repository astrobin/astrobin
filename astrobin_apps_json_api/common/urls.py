from django.conf.urls import url
from django.views.decorators.cache import never_cache

from astrobin_apps_json_api.common.views import AppConfig, CkEditorUpload

urlpatterns = (
    url(r'^common/app-config/$', never_cache(AppConfig.as_view())),
    url(r'^common/ckeditor-upload/$', never_cache(CkEditorUpload.as_view())),
)
