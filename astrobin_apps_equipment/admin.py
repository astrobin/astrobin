# -*- coding: utf-8 -*-


from django.contrib import admin

from astrobin_apps_equipment.models import Sensor, Camera
from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_item_listing import EquipmentItemListing
from astrobin_apps_equipment.models.equipment_retailer import EquipmentRetailer


class EquipmentBrandAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'created_by',
        'created',
    )


class EquipmentRetailerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'website',
        'countries',
        'created',
    )


class EquipmentBrandListingAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'retailer',
        'url',
        'created',
    )


class EquipmentItemListingAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'retailer',
        'url',
        'created',
    )


class SensorAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'name',
        'created',
    )


class CameraAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'name',
        'created',
    )

admin.site.register(EquipmentBrand, EquipmentBrandAdmin)
admin.site.register(EquipmentRetailer, EquipmentRetailerAdmin)
admin.site.register(EquipmentBrandListing, EquipmentBrandListingAdmin)
admin.site.register(EquipmentItemListing, EquipmentItemListingAdmin)
admin.site.register(Sensor, SensorAdmin)
admin.site.register(Camera, CameraAdmin)
