# -*- coding: utf-8 -*-


from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from safedelete import HARD_DELETE

from astrobin_apps_equipment.models import (
    AccessoryMigrationRecord, CameraMigrationRecord, EquipmentItemMarketplaceListing,
    EquipmentItemMarketplaceListingLineItem, EquipmentItemMarketplaceListingLineItemImage,
    EquipmentItemMarketplaceOffer, EquipmentItemMarketplacePrivateConversation, EquipmentPreset,
    FilterMigrationRecord, MountMigrationRecord,
    Sensor, Camera, SoftwareMigrationRecord, Telescope,
    CameraEditProposal, Mount,
    Filter, Accessory,
    Software, EquipmentItemGroup, TelescopeMigrationRecord,
)
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

class EquipmentItemGroupAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )

class EquipmentItemMigrationRecordAdmin(admin.ModelAdmin):
    list_display = (
        'image', 'from_gear', 'to_item', 'created'
    )


class EquipmentItemMarketplaceListingAdmin(admin.ModelAdmin):
    list_display = (
        'hash',
        'created',
        'user',
        'expiration',
    )

    search_fields = (
        'hash',
        'user__username',
    )

    readonly_fields = (
        'id',
        'hash',
        'user',
        'created',
        'view_line_items',
    )

    def view_line_items(self, obj) -> str:
        line_items = obj.line_items.all()
        line_item_links = [
            format_html(
                '<a href="{}">{}</a>',
                reverse(
                    "admin:astrobin_apps_equipment_equipmentitemmarketplacelistinglineitem_change",
                    args=(line_item.id,)
                ),
                line_item.item_content_object
            )
            for line_item in line_items
        ]
        return format_html("<br>".join(line_item_links))

    view_line_items.short_description = 'Line Items'


class EquipmentItemMarketplaceListingLineItemAdmin(admin.ModelAdmin):
    list_display = (
        'hash',
        'created',
        'listing',
        'user',
        'price',
        'currency',
    )

    search_fields = (
        'hash',
        'user__username',
    )

    readonly_fields = (
        'id',
        'hash',
        'user',
        'created',
        'view_listing',
        'view_images',
    )

    exclude = (
        'listing',
        'sold_to',
        'reserved_to',
    )

    def view_listing(self, obj) -> str:
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                "admin:astrobin_apps_equipment_equipmentitemmarketplacelisting_change",
                args=(obj.listing.id,)
            ),
            obj.listing
        )

    def view_images(self, obj) -> str:
        images = obj.images.all()
        image_links = [
            format_html(
                '<a href="{}">{}</a>',
                reverse(
                    "admin:astrobin_apps_equipment_equipmentitemmarketplacelistinglineitemimage_change",
                    args=(image.id,)
                ),
                image.image_file.url
            )
            for image in images
        ]
        return format_html("<br>".join(image_links))

    view_images.short_description = 'Images'


class EquipmentItemMarketplaceListingLineItemImageAdmin(admin.ModelAdmin):
    list_display = (
        'hash',
        'line_item',
        'user',
        'w',
        'h',
    )

    search_fields = (
        'hash',
        'user__username',
    )

    readonly_fields = (
        'id',
        'hash',
        'w',
        'h',
        'user',
        'created',
        'view_line_item',
    )

    exclude = (
        'line_item',
    )

    def view_line_item(self, obj) -> str:
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                "admin:astrobin_apps_equipment_equipmentitemmarketplacelistinglineitem_change",
                args=(obj.line_item.id,)
            ),
            obj.line_item
        )


class EquipmentItemMarketplacePrivateConversationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'listing',
        'created',
    )

    search_fields = (
        'user__username',
        'listing__hash',
    )

    readonly_fields = (
        'id',
        'user',
        'listing',
        'created',
    )

    exclude = (
        'comments',
    )


class EquipmentItemMarketplaceOfferAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'listing',
        'line_item',
        'created',
        'amount',
        'status',
    )

    search_fields = (
        'user__username',
        'listing__hash',
        'line_item__hash',
    )

    readonly_fields = (
        'id',
        'user',
        'listing',
        'line_item',
        'created',
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
admin.site.register(EquipmentItemGroup, EquipmentItemGroupAdmin)
admin.site.register(EquipmentPreset)
admin.site.register(TelescopeMigrationRecord, EquipmentItemMigrationRecordAdmin)
admin.site.register(CameraMigrationRecord, EquipmentItemMigrationRecordAdmin)
admin.site.register(MountMigrationRecord, EquipmentItemMigrationRecordAdmin)
admin.site.register(FilterMigrationRecord, EquipmentItemMigrationRecordAdmin)
admin.site.register(AccessoryMigrationRecord, EquipmentItemMigrationRecordAdmin)
admin.site.register(SoftwareMigrationRecord, EquipmentItemMigrationRecordAdmin)
admin.site.register(EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingAdmin)
admin.site.register(EquipmentItemMarketplaceListingLineItem, EquipmentItemMarketplaceListingLineItemAdmin)
admin.site.register(EquipmentItemMarketplaceListingLineItemImage, EquipmentItemMarketplaceListingLineItemImageAdmin)
admin.site.register(EquipmentItemMarketplacePrivateConversation, EquipmentItemMarketplacePrivateConversationAdmin)
admin.site.register(EquipmentItemMarketplaceOffer, EquipmentItemMarketplaceOfferAdmin)
