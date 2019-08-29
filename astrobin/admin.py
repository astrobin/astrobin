import difflib
from datetime import timedelta

from django.contrib import admin, messages
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe

from astrobin.models import *


class ImageAdmin(admin.ModelAdmin):
    fields = (
        'title',
        'description',
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
        'default_license',
        'language',
    )

    list_display = (
        'user',
        'accept_tos',
        'receive_important_communications',
        'receive_newsletter',
        'receive_marketing_and_commercial_material'
    )

    search_fields = ('user__username',)

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
        'date',
    )
    ordering = ('-date',)


class ImageOfTheDayCandidateAdmin(admin.ModelAdmin):
    list_display = (
        'image',
        'date',
        'position',
    )
    ordering = ('-date', 'position')


class CollectionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'name',
        'description',
        'date_created',
    )
    list_editable = (
        'name',
    )
    list_filter = ('user',)


class BroadcastEmailAdmin(admin.ModelAdmin):
    def submit_email(self, request, obj, recipients):
        if obj.count() != 1:
            self.message_user(
                request,
                "Please select exactly one email",
                messages.ERROR)
        else:
            obj = obj[0]
            for recipient in recipients:
                msg = EmailMessage(
                    obj.subject,
                    mark_safe(obj.message),
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient])
                msg.content_subtype = 'html'
                msg.send()
                self.message_user(
                    request,
                    "Email enqueued to be sent to %d users" % len(recipients))

    def submit_mass_email(self, request, obj):
        recipients = User.objects.all().values_list('email', flat=True)
        self.submit_email(request, obj, recipients)

    def submit_superuser_email(self, request, obj):
        recipients = UserProfile.objects\
            .filter(user__is_superuser = True)\
            .values_list('user__email', flat=True)
        self.submit_email(request, obj, recipients)

    def submit_important_communication(self, request, obj):
        recipients = UserProfile.objects \
            .filter(receive_important_communications=True) \
            .values_list('user__email', flat=True)
        self.submit_email(request, obj, recipients)

    def submit_newsletter(self, request, obj):
        recipients = UserProfile.objects \
            .filter(receive_newsletter=True) \
            .values_list('user__email', flat=True)
        self.submit_email(request, obj, recipients)

    def submit_marketing_and_commercial_material(self, request, obj):
        recipients = UserProfile.objects \
            .filter(receive_marketing_and_commercial_material=True) \
            .values_list('user__email', flat=True)
        self.submit_email(request, obj, recipients)

    def submit_premium_offer_discount(self, request, obj):
        recipients = UserProfile.objects \
            .exclude(premium_offer=None) \
            .exclude(premium_offer_expiration=None) \
            .exclude(premium_offer_expiration__lt=datetime.now())\
            .filter(
                Q(premium_offer_sent = None) |
                Q(premium_offer_sent__lt=datetime.now() - timedelta(days=30))
            )\
            .values_list('user__email', flat=True)
        self.submit_email(request, obj, recipients)
        recipients.update(premium_offer_sent=datetime.now())

    submit_mass_email.short_description = 'Submit mass email (select one only) - DO NOT ABUSE'
    submit_mass_email.allow_tags = True

    submit_superuser_email.short_description = 'Submit email to superusers (select one only)'
    submit_superuser_email.allow_tags = True

    submit_important_communication.short_description = 'Submit important communication (select one only)'
    submit_important_communication.allow_tags = True

    submit_newsletter.short_description = 'Submit newsletter (select one only)'
    submit_newsletter.allow_tags = True

    submit_marketing_and_commercial_material.short_description = 'Submit marketing and commercial material (select one only)'
    submit_marketing_and_commercial_material.allow_tags = True

    submit_premium_offer_discount.short_description = 'Submit Premium discount offer'
    submit_premium_offer_discount.allow_tags = True

    actions = [
        'submit_mass_email',
        'submit_superuser_email',
        'submit_important_communication',
        'submit_newsletter',
        'submit_marketing_and_commercial_material',
        'submit_premium_offer_discount'
    ]

    list_display = ("subject", "created")
    search_fields = ['subject', ]


admin.site.register(Gear, GearAdmin)
admin.site.register(GearUserInfo)
admin.site.register(GearAssistedMerge, GearAssistedMergeAdmin)
admin.site.register(GearMakeAutoRename)
admin.site.register(GearHardMergeRedirect)
admin.site.register(Telescope)
admin.site.register(Mount, MountAdmin)
admin.site.register(Camera)
admin.site.register(FocalReducer)
admin.site.register(Software)
admin.site.register(Filter)
admin.site.register(Accessory)
admin.site.register(DeepSky_Acquisition)
admin.site.register(SolarSystem_Acquisition)
admin.site.register(Image, ImageAdmin)
admin.site.register(ImageRevision)
admin.site.register(Request)
admin.site.register(ImageRequest)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Location)
admin.site.register(AppApiKeyRequest, AppApiRequestAdmin)
admin.site.register(App, AppAdmin)
admin.site.register(ImageOfTheDay, ImageOfTheDayAdmin)
admin.site.register(ImageOfTheDayCandidate, ImageOfTheDayCandidateAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(GlobalStat)
admin.site.register(BroadcastEmail, BroadcastEmailAdmin)

###############################################################################
# Commercial models.                                                          #
###############################################################################
admin.site.register(CommercialGear)
admin.site.register(RetailedGear)
