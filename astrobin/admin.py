from datetime import timedelta, datetime

from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from astrobin.models import Gear, GearUserInfo, Telescope, \
    Mount, Camera, FocalReducer, Software, Filter, Accessory, DeepSky_Acquisition, SolarSystem_Acquisition, Image, \
    ImageRevision, Request, ImageRequest, UserProfile, Location, AppApiKeyRequest, App, ImageOfTheDay, \
    ImageOfTheDayCandidate, Collection, GlobalStat, BroadcastEmail
from astrobin.tasks import send_broadcast_email
from astrobin.utils import inactive_accounts
from astrobin_apps_premium.utils import premium_get_valid_usersubscription


class ImageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'hash',
        'title',
        'user',
    )

    fields = (
        'hash',
        'title',
        'description',
        'description_bbcode',
        'license',
    )

    search_fields = (
        'hash',
        'title',
        'user__username',
    )


class UserProfileAdmin(admin.ModelAdmin):
    fields = (
        'website',
        'job',
        'hobbies',
        'telescopes',
        'mounts',
        'cameras',
        'focal_reducers',
        'software',
        'filters',
        'accessories',
        'default_license',
        'language',
        'astrobin_index_bonus',
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
    list_display = ('id', 'make', 'name', 'master', 'updated',)
    list_editable = ('make', 'name',)
    search_fields = ('id', 'make', 'name',)


class MountAdmin(admin.ModelAdmin):
    list_display = ('id', 'make', 'name', 'master', 'updated',)
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
        elif recipients.count() > 0:
            send_broadcast_email.delay(obj[0].id, list(recipients))
            self.message_user(
                request,
                "Email enqueued to be sent to %d users" % len(recipients))

    def submit_mass_email(self, request, obj):
        recipients = User.objects.all().values_list('email', flat=True)
        self.submit_email(request, obj, recipients)

    def submit_superuser_email(self, request, obj):
        recipients = UserProfile.objects \
            .filter(user__is_superuser=True) \
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
        profiles = UserProfile.objects \
            .exclude(premium_offer=None) \
            .exclude(premium_offer_expiration=None) \
            .exclude(premium_offer_expiration__lt=datetime.now()) \
            .filter(receive_marketing_and_commercial_material=True) \
            .filter(
            Q(premium_offer_sent=None) |
            Q(premium_offer_sent__lt=datetime.now() - timedelta(days=30))
        )

        profiles = [x for x in profiles if premium_get_valid_usersubscription(x.user) is None]

        recipients = UserProfile.objects.filter(pk__in=[x.pk for x in profiles])
        self.submit_email(request, obj, recipients.values_list("user__email", flat=True))
        recipients.update(premium_offer_sent=datetime.now())

    def submit_inactive_email_reminder(self, request, obj):
        recipients = inactive_accounts()
        self.submit_email(request, obj, recipients.values_list('user__email', flat=True))
        recipients.update(inactive_account_reminder_sent=timezone.now())

    def submit_recovered_images_notice_de(self, request, obj):
        recipients = User.objects \
            .filter(userprofile__deleted=None, userprofile__language='de',
                    userprofile__recovered_images_notice_sent=None,
                    image__recovered__isnull=False) \
            .distinct() \
            .values_list('email', flat=True)
        self.submit_email(request, obj, recipients)
        UserProfile.objects.filter(user__email__in=recipients).update(recovered_images_notice_sent=datetime.now())

    def submit_recovered_images_notice_en(self, request, obj):
        recipients = User.objects \
            .filter(userprofile__deleted=None, userprofile__recovered_images_notice_sent=None,
                    image__recovered__isnull=False) \
            .exclude(userprofile__language__in=['it', 'fr', 'de', 'es', 'pt']) \
            .distinct() \
            .values_list('email', flat=True)
        self.submit_email(request, obj, recipients)
        UserProfile.objects.filter(user__email__in=recipients).update(recovered_images_notice_sent=datetime.now())

    def submit_recovered_images_notice_es(self, request, obj):
        recipients = User.objects \
            .filter(userprofile__deleted=None, userprofile__language='es',
                    userprofile__recovered_images_notice_sent=None,
                    image__recovered__isnull=False) \
            .distinct() \
            .values_list('email', flat=True)
        self.submit_email(request, obj, recipients)
        UserProfile.objects.filter(user__email__in=recipients).update(recovered_images_notice_sent=datetime.now())

    def submit_recovered_images_notice_fr(self, request, obj):
        recipients = User.objects \
            .filter(userprofile__deleted=None, userprofile__language='fr',
                    userprofile__recovered_images_notice_sent=None,
                    image__recovered__isnull=False) \
            .distinct() \
            .values_list('email', flat=True)
        self.submit_email(request, obj, recipients)
        UserProfile.objects.filter(user__email__in=recipients).update(recovered_images_notice_sent=datetime.now())

    def submit_recovered_images_notice_it(self, request, obj):
        recipients = User.objects \
            .filter(userprofile__deleted=None, userprofile__language='it',
                    userprofile__recovered_images_notice_sent=None,
                    image__recovered__isnull=False) \
            .distinct() \
            .values_list('email', flat=True)
        self.submit_email(request, obj, recipients)
        UserProfile.objects.filter(user__email__in=recipients).update(recovered_images_notice_sent=datetime.now())

    def submit_recovered_images_notice_pt(self, request, obj):
        recipients = User.objects \
            .filter(userprofile__deleted=None, userprofile__language='pt',
                    userprofile__recovered_images_notice_sent=None,
                    image__recovered__isnull=False) \
            .distinct() \
            .values_list('email', flat=True)
        self.submit_email(request, obj, recipients)
        UserProfile.objects.filter(user__email__in=recipients).update(recovered_images_notice_sent=datetime.now())

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

    submit_inactive_email_reminder.short_description = 'Submit inactive account reminder'
    submit_inactive_email_reminder.allow_tags = True

    submit_recovered_images_notice_de.short_description = '[de] Submit recovered images notice'
    submit_recovered_images_notice_de.allow_tags = True

    submit_recovered_images_notice_en.short_description = '[en] Submit recovered images notice'
    submit_recovered_images_notice_en.allow_tags = True

    submit_recovered_images_notice_es.short_description = '[es] Submit recovered images notice'
    submit_recovered_images_notice_es.allow_tags = True

    submit_recovered_images_notice_fr.short_description = '[fr] Submit recovered images notice'
    submit_recovered_images_notice_fr.allow_tags = True

    submit_recovered_images_notice_it.short_description = '[it] Submit recovered images notice'
    submit_recovered_images_notice_it.allow_tags = True

    submit_recovered_images_notice_pt.short_description = '[pt] Submit recovered images notice'
    submit_recovered_images_notice_pt.allow_tags = True

    actions = [
        'submit_mass_email',
        'submit_superuser_email',
        'submit_important_communication',
        'submit_newsletter',
        'submit_marketing_and_commercial_material',
        'submit_premium_offer_discount',
        'submit_inactive_email_reminder',
        'submit_recovered_images_notice_de',
        'submit_recovered_images_notice_en',
        'submit_recovered_images_notice_es',
        'submit_recovered_images_notice_fr',
        'submit_recovered_images_notice_it',
        'submit_recovered_images_notice_pt',
    ]
    list_display = ("subject", "created")
    search_fields = ['subject', ]


admin.site.register(Gear, GearAdmin)
admin.site.register(GearUserInfo)
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
