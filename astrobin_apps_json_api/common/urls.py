from django.conf.urls import url

from astrobin_apps_json_api.common.views import AppConfig, CkEditorUpload

urlpatterns = (
    url(r'^common/app-config/$', AppConfig.as_view()),
    url(r'^common/ckeditor-upload/$', CkEditorUpload.as_view()),
)
