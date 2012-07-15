from astrobin.models import *

import difflib

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.db.models import Q

class ImageAdmin(admin.ModelAdmin):
    fields = (
        'title',
        'subjects',
        'description',
        'focal_length',
        'pixel_size',
        'binning',
        'scaling',
        'imaging_telescopes',
        'guiding_telescopes',
        'mounts',
        'imaging_cameras',
        'guiding_cameras',
        'focal_reducers',
        'software',
        'filters',
        'accessories',
        'user',
        'license',
    )


class UserProfileAdmin(admin.ModelAdmin):
    fields = (
        'website',
        'job',
        'hobbies',
        'timezone',
        'telescopes',
        'mounts',
        'cameras',
        'focal_reducers',
        'software',
        'filters',
        'accessories',
        'follows',
        'default_license',
        'language'
    )


class GearAdmin(admin.ModelAdmin):
    list_display = ('id', 'make', 'name', 'master', 'updated', 'moderator_fixed')
    list_editable = ('make', 'name',)
    search_fields = ('id', 'make', 'name',)
    actions = ['assisted_merge', 'soft_merge',]

    def assisted_merge(modeladmin, request, queryset):
        GearAssistedMerge.objects.all().delete()

        if queryset.count() > 1:
            return

        orphans = queryset.filter(master = None)
        for orphan in orphans:
            matches = difflib.get_close_matches(orphan.name, [x.name for x in queryset], cutoff = 0.6)
            for match in matches:
                slaves = Gear.objects.filter(name = match).exclude(pk = orphan.pk)
                for slave in slaves:
                    # The following line needs some explaining:
                    # With the first Q(), I exclude mutual master/slave
                    # relationship (like a -> b and b -> a).
                    # With the second Q(), I exclude dependencies that generate
                    # a tree deeper than 2 level (a -> b -> c).
                    if not GearAssistedMerge.objects.filter(Q(slave = orphan) | Q(master = slave)):
                        s = difflib.SequenceMatcher(None, orphan.name, match)
                        merge, created = GearAssistedMerge.objects.get_or_create(master = orphan, slave = slave)
                        merge.cutoff = s.quick_ratio()
                        merge.save()

        return HttpResponseRedirect('/admin/astrobin/gearassistedmerge/')
    assisted_merge.short_description = 'Assisted hard merge'

    def soft_merge(modeladmin, request, queryset):
        masters = [x.master for x in queryset]
        if not all(x == masters[0] for x in masters):
            # They're not all the same!
            return

        master = masters[0]
        slaves = [x.slave for x in queryset if x != master]

        for slave in slaves:
            # These are all the items that are slave to this slave.
            slaves_slaves = Gear.objects.filter(master = slave)

            if slave.master:
                slave.master.master = master
                slave.master.master.save()

            for slaves_slave in slaves_slaves:
                slaves_slave.master = master
                slaves_slave.save()

            slave.master = master
            slave.save()
    soft_merge.short_description = 'Soft merge'


class GearAssistedMergeAdmin(admin.ModelAdmin):
    list_display = ('id', 'master',  'slave', 'cutoff')
    list_per_page = 10
    ordering = ('-cutoff', 'master')
    search_fields = ('master',)
    actions = ['hard_merge', 'invert', 'delete_gear_items',]


    def invert(modeladmin, request, queryset):
        for merge in queryset:
            master = merge.master
            slave = merge.slave
            merge.master = slave
            merge.slave = master
            merge.save()

    invert.short_description = 'Invert'


    def delete_gear_items(modeladmin, request, queryset):
        for merge in queryset:
            try:
                merge.master.delete()
                merge.slave.delete()
            except Gear.DoesNotExist:
                pass
            merge.delete()

    delete_gear_items.short_description = "Delete gear items"


    def hard_merge(modeladmin, request, queryset):
        from utils import unique_items
        masters = unique_items([x.master for x in queryset])
        if len(masters) > 1:
            return

        master = masters[0]
        for merge in queryset:
            master.hard_merge(merge.slave)

        # Finally, clear up the temporary model
        queryset.delete()

        return HttpResponseRedirect('/admin/astrobin/gear/')
    hard_merge.short_description = 'Hard merge'


class MountAdmin(admin.ModelAdmin):
    list_display = ('id', 'make', 'name', 'master', 'updated', 'moderator_fixed')
    list_editable = ('make', 'name',)
    search_fields = ('id', 'make', 'name',)


class AppApiRequestAdmin(admin.ModelAdmin):
    list_display = (
        'registrar',
        'name',
        'created',
        'approved',
    )
    list_filter = ('approved',)
    ordering = ('-created',)
    actions = ['approve']

    def approve(modeladmin, request, queryset):
        for api_request in queryset:
            api_request.approve()

    approve.short_description = 'Approve'


class AppAdmin(admin.ModelAdmin):
    list_display = (
        'registrar',
        'name',
        'key',
        'secret',
        'created',
        'active',
    )
    list_filter = ('active',)
    ordering = ('-created',)


class ImageOfTheDayAdmin(admin.ModelAdmin):
    list_display = (
        'image',
        'filename',
        'date',
    )
    ordering = ('-date',)


admin.site.register(Gear, GearAdmin)
admin.site.register(GearUserInfo)
admin.site.register(GearAssistedMerge, GearAssistedMergeAdmin)
admin.site.register(GearMakeAutoRename)
admin.site.register(Telescope)
admin.site.register(Mount, MountAdmin)
admin.site.register(Camera)
admin.site.register(FocalReducer)
admin.site.register(Software)
admin.site.register(Filter)
admin.site.register(Accessory)
admin.site.register(Subject)
admin.site.register(SubjectIdentifier)
admin.site.register(DeepSky_Acquisition)
admin.site.register(SolarSystem_Acquisition)
admin.site.register(Image, ImageAdmin)
admin.site.register(ImageRevision)
admin.site.register(Request)
admin.site.register(ImageRequest)
admin.site.register(ABPOD)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Location)
admin.site.register(MessierMarathon)
admin.site.register(MessierMarathonNominations)
admin.site.register(Comment)
admin.site.register(GearComment)
admin.site.register(AppApiKeyRequest, AppApiRequestAdmin)
admin.site.register(App, AppAdmin)
admin.site.register(ImageOfTheDay, ImageOfTheDayAdmin)
admin.site.register(GlobalStat)
