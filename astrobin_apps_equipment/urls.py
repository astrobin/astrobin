from django.conf.urls import url

from astrobin_apps_equipment.views import EquipmentItemPopover

app_name = 'equipment'

urlpatterns = (
    url(r'^item-popover/(?P<type>\w+)/(?P<pk>\d+)/(?P<image_id>\w+)/$', EquipmentItemPopover.as_view(), name='item-popover'),
)
