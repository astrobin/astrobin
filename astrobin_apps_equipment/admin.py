# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_brand_retailer import EquipmentBrandRetailer


class EquipmentBrandAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'created_by',
        'created',
    )


class EquipmentBrandRetailerAdmin(admin.ModelAdmin):
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


admin.site.register(EquipmentBrand, EquipmentBrandAdmin)
admin.site.register(EquipmentBrandRetailer, EquipmentBrandRetailerAdmin)
admin.site.register(EquipmentBrandListing, EquipmentBrandListingAdmin)
