from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_equipment import views

router = routers.DefaultRouter()
router.register(r'brands', views.BrandViewSet)
router.register(r'equipment-items', views.EquipmentItemViewSet)

urlpatterns = [
    url(r'^', include(router.urls))
]
