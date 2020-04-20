from astrobin_apps_json_api.common.urls import urlpatterns as common_urls
from astrobin_apps_json_api.i18n.urls import urlpatterns as i18n_urls
from astrobin_apps_json_api.user.urls import urlpatterns as user_urls

app_name = "astrobin_apps_json_api"
urlpatterns = common_urls + i18n_urls + user_urls
