# -*- coding: utf-8 -*-


from django.contrib import admin
from safedelete import HARD_DELETE

from astrobin_apps_equipment.models import Sensor, Camera, Telescope, CameraEditProposal, Mount, Filter, Accessory, \
    Software
from astrobin_apps_equipment.models.accessory_edit_proposal import AccessoryEditProposal
from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_item_listing import EquipmentItemListing
from astrobin_apps_equipment.models.equipment_retailer import EquipmentRetailer
from astrobin_apps_equipment.models.filter_edit_proposal import FilterEditProposal
from astrobin_apps_equipment.models.mount_edit_proposal import MountEditProposal
from astrobin_apps_equipment.models.sensor_edit_proposal import SensorEditProposal
from astrobin_apps_equipment.models.software_edit_proposal import SoftwareEditProposal
from astrobin_apps_equipment.models.telescope_edit_proposal import TelescopeEditProposal


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


class EquipmentItemAdmin(admin.ModelAdmin):
    def delete_permanently(self, request, queryset):
        queryset.delete(force_policy=HARD_DELETE)

    delete_permanently.short_description = 'Delete selected items   permanently'

    actions = ['delete_permanently']


class SensorAdmin(EquipmentItemAdmin):
    list_display = (
        'brand',
        'name',
        'created',
    )


class SensorEditProposalAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'name',
        'edit_proposal_created',
    )


class CameraAdmin(EquipmentItemAdmin):
    list_display = (
        'brand',
        'name',
        'modified',
        'cooled',
        'created',
    )


class CameraEditProposalAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'name',
        'edit_proposal_created',
    )


class TelescopeAdmin(EquipmentItemAdmin):
    list_display = (
        'brand',
        'name',
        'created',
    )


class TelescopeEditProposalAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'name',
        'edit_proposal_created',
    )


class MountAdmin(EquipmentItemAdmin):
    list_display = (
        'brand',
        'name',
        'created',
    )


class MountEditProposalAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'name',
        'edit_proposal_created',
    )


class FilterAdmin(EquipmentItemAdmin):
    list_display = (
        'brand',
        'name',
        'created',
    )


class FilterEditProposalAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'name',
        'edit_proposal_created',
    )


class AccessoryAdmin(EquipmentItemAdmin):
    list_display = (
        'brand',
        'name',
        'created',
    )


class AccessoryEditProposalAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'name',
        'edit_proposal_created',
    )


class SoftwareAdmin(EquipmentItemAdmin):
    list_display = (
        'brand',
        'name',
        'created',
    )


class SoftwareEditProposalAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'name',
        'edit_proposal_created',
    )


admin.site.register(EquipmentBrand, EquipmentBrandAdmin)
admin.site.register(EquipmentRetailer, EquipmentRetailerAdmin)
admin.site.register(EquipmentBrandListing, EquipmentBrandListingAdmin)
admin.site.register(EquipmentItemListing, EquipmentItemListingAdmin)
admin.site.register(Sensor, SensorAdmin)
admin.site.register(SensorEditProposal, SensorEditProposalAdmin)
admin.site.register(Camera, CameraAdmin)
admin.site.register(CameraEditProposal, CameraEditProposalAdmin)
admin.site.register(Telescope, TelescopeAdmin)
admin.site.register(TelescopeEditProposal, TelescopeEditProposalAdmin)
admin.site.register(Mount, MountAdmin)
admin.site.register(MountEditProposal, MountEditProposalAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(FilterEditProposal, FilterEditProposalAdmin)
admin.site.register(Accessory, AccessoryAdmin)
admin.site.register(AccessoryEditProposal, AccessoryEditProposalAdmin)
admin.site.register(Software, SoftwareAdmin)
admin.site.register(SoftwareEditProposal, SoftwareEditProposalAdmin)
