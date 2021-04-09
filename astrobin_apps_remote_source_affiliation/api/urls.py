from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_remote_source_affiliation.api.views.remote_source_affiliate_view_set import \
    RemoteSourceAffiliateViewSet

router = routers.DefaultRouter()
router.register(r'remote-source-affiliate', RemoteSourceAffiliateViewSet, base_name='remote-source-affiliate')

urlpatterns = [
    url('', include(router.urls)),
]
