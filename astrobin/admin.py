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
    list_display = ('name', 'master')
    search_fields = ('name',)
    list_filter = ('master',)
    actions = ['assisted_merge']

    def assisted_merge(modeladmin, request, queryset):
        GearAssistedMerge.objects.all().delete()

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
                    if not GearAssistedMerge.objects.filter(Q(slave = orphan) | Q(master = slave)) \
                       and not GearNeverMerge.objects.filter(Q(master = orphan) & Q(label = match)):
                        s = difflib.SequenceMatcher(None, orphan.name, match)
                        merge, created = GearAssistedMerge.objects.get_or_create(master = orphan, slave = slave)
                        merge.cutoff = s.quick_ratio()
                        merge.save()

        return HttpResponseRedirect('/admin/astrobin/gearassistedmerge/')

    assisted_merge.short_description = 'Assisted merge'


class GearAssistedMergeAdmin(admin.ModelAdmin):
    list_display = ('master', 'slave', 'cutoff')
    ordering = ('-cutoff', 'name')
    list_per_page = 10
    search_fields = ('master',)
    actions = ['soft_merge', 'hard_merge', 'invert', 'delete_gear_items', 'never_merge']


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

    delete_gear_items.short_description = "Delete grar items"


    def never_merge(modeladmin, request, queryset):
        for merge in queryset:
            nevermerge = GearNeverMerge.objects.get_or_create(master = merge.master, label = merge.slave.name)
            merge.delete()

    never_merge.short_description = "Never merge"


    def soft_merge(modeladmin, request, queryset):
        pass
    soft_merge.short_description = 'Soft merge'

    def hard_merge(modeladmin, request, queryset):
        import operator

        for merge in queryset:
            merge_done = False
            # Find matching slaves in images
            types = {
                'imaging_telescopes': Telescope,
                'guiding_telescopes': Telescope,
                'mounts': Mount,
                'imaging_cameras': Camera,
                'guiding_cameras': Camera,
                'focal_reducers': FocalReducer,
                'software': Software,
                'filters': Filter,
                'accessories': Accessory,
            }
            filters = reduce(operator.or_, [Q(**{'%s__gear_ptr__pk' % t: merge.slave.pk}) for t in types])
            images = Image.objects.filter(filters).distinct()
            for image in images:
                changed = False
                for name, klass in types.iteritems():
                    slave = getattr(image, name).filter(pk = merge.slave.pk)
                    if slave:
                        try:
                            getattr(image, name).add(klass.objects.get(gear_ptr = merge.master))
                            getattr(image, name).remove(slave[0])
                            merge_done = True
                            changed = True
                        except klass.DoesNotExist:
                            continue
                if changed:
                    image.save()

            # Find matching slaves in user profiles
            types = {
                'telescopes': Telescope,
                'mounts': Mount,
                'cameras': Camera,
                'focal_reducers': FocalReducer,
                'software': Software,
                'filters': Filter,
                'accessories': Accessory,
            }
            filters = reduce(operator.or_, [Q(**{'%s__gear_ptr__pk' % t: merge.slave.pk}) for t in types])
            owners = UserProfile.objects.filter(filters).distinct()
            for owner in owners:
                changed = False
                for name, klass in types.iteritems():
                    slave = getattr(owner, name).filter(pk = merge.slave.pk)
                    if slave:
                        try:
                            getattr(owner, name).add(klass.objects.get(gear_ptr = merge.master))
                            getattr(owner, name).remove(slave[0])
                            merge_done = True
                            changed = True
                        except klass.DoesNotExist:
                            continue
                if changed:
                    owner.save()

            if merge_done:
                automerge = GearAutoMerge.objects.get_or_create(master = merge.master, label = merge.slave.name)

        # Only now, delete all the slaves. We must delete at the end because
        # We might have the same slave respond to different masters.
        for merge in queryset:
            merge.slave.delete()

        # Finally, clear up the temporary model
        queryset.delete()

    hard_merge.short_description = 'Hard merge'


admin.site.register(Gear, GearAdmin)
admin.site.register(GearAssistedMerge, GearAssistedMergeAdmin)
admin.site.register(Telescope)
admin.site.register(Mount)
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
admin.site.register(LocationRequest)
admin.site.register(ImageRequest)
admin.site.register(ABPOD)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Location)
