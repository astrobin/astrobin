from django.conf.urls import url

from astrobin_apps_json_api.i18n.views import I18nMessages

urlpatterns = (
    url(r'^i18n/messages/(?P<code>\w+(-\w+)?)/$', I18nMessages.as_view()),
)
