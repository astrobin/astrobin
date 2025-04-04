from datetime import timedelta, datetime

from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from astrobin.models import (
    Gear, GearUserInfo, ImageEquipmentLog, PopupMessage, PopupMessageUserStatus, SavedSearch, Telescope,
    Mount, Camera, FocalReducer, Software, Filter, Accessory, DeepSky_Acquisition, SolarSystem_Acquisition, Image,
    ImageRevision, Request, ImageRequest, UserProfile, Location, AppApiKeyRequest, App, ImageOfTheDay,
    ImageOfTheDayCandidate, Collection, BroadcastEmail, CameraRenameProposal, GearRenameRecord, GearMigrationStrategy,
)
from astrobin.services.gear_service import GearService
from astrobin.tasks import send_broadcast_email
from astrobin.utils import inactive_accounts
from astrobin_apps_premium.services.premium_service import PremiumService


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


class ImageEquipmentLogAdmin(admin.ModelAdmin):
    list_display = ('image', 'equipment_item', 'verb', 'date')
    list_filter = ('verb', 'date')
    search_fields = ('image__title', 'equipment_item_content_type__model')
    readonly_fields = (
        'image',
        'equipment_item_content_type',
        'equipment_item_object_id',
        'equipment_item',
        'date',
        'verb'
    )

    def has_add_permission(self, request, obj=None):
        # Disable adding new logs via admin as they should be generated programmatically
        return False

    def has_delete_permission(self, request, obj=None):
        # Disable deletion if logs should be immutable
        return False


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
    actions = ('reset_migration_fields',)

    def reset_migration_fields(selfmodeladmin, request, queryset):
        GearService.reset_migration_fields(queryset)

    reset_migration_fields.short_description = 'Reset migration fields'


class GearMigrationStrategyAdmin(admin.ModelAdmin):
    list_display = ('gear', 'user', 'migration_flag',)


class CameraRenameProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'old_make', 'old_name', 'new_make', 'new_name', 'modified', 'status', 'reject_reason',)
    list_editable = ('new_make', 'new_name', 'modified', 'status',)
    search_fields = ('old_name',)
    list_filter = ('status',)


class GearRenameRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'gear', 'old_make', 'old_name', 'new_make', 'new_name',)
    search_fields = ('old_name',)


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
    actions = ['approve', 'reject']

    def approve(modeladmin, request, queryset):
        for api_request in queryset:
            api_request.approve()

    approve.short_description = 'Approve'
    
    def reject(modeladmin, request, queryset):
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        for api_request in queryset:
            # Create a message with request details
            message = f"""Thanks for your interest in AstroBin's API. After reviewing your request, we've determined that this use case isn't aligned with AstroBin's current strategic direction and policies regarding API access.

We appreciate your understanding and wish you success with your project. We apologize for any inconvenience this may cause.

For your reference, here are the details of your request:

Username: {api_request.registrar.username}
Name: {api_request.name}
Description: {api_request.description}

If you have any questions or would like further clarification, please visit https://welcome.astrobin.com/contact to get in touch. Please do not reply to this email. If you decide to contact us, please include the username, name, and description of your request as shown above.

Best regards,
The AstroBin Team"""

            # Create email with CC
            email = EmailMessage(
                subject='AstroBin API Request Decision',
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[api_request.registrar.email],
                cc=[settings.DEFAULT_FROM_EMAIL],
            )
            
            # Send email
            email_sent = email.send()
            
            # Only delete the request if the email was sent successfully
            if email_sent:
                api_request.delete()
                modeladmin.message_user(
                    request,
                    f"Request from {api_request.registrar.username} has been rejected and deleted."
                )
            else:
                modeladmin.message_user(
                    request,
                    f"Failed to send email to {api_request.registrar.username}. Request not deleted.",
                    level=messages.ERROR
                )
    
    reject.short_description = 'Reject'


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
                messages.ERROR
            )
        elif recipients.count() > 0:
            send_broadcast_email.delay(obj[0].id, list(recipients))
            self.message_user(
                request,
                "Email enqueued to be sent to %d users" % len(recipients)
            )

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

        profiles = [x for x in profiles if PremiumService(x.user).get_valid_usersubscription() is None]

        recipients = UserProfile.objects.filter(pk__in=[x.pk for x in profiles])
        self.submit_email(request, obj, recipients.values_list("user__email", flat=True))
        recipients.update(premium_offer_sent=datetime.now())

    def submit_inactive_email_reminder(self, request, obj):
        recipients = inactive_accounts()
        self.submit_email(request, obj, recipients.values_list('user__email', flat=True))
        recipients.update(inactive_account_reminder_sent=timezone.now())

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

    actions = [
        'submit_mass_email',
        'submit_superuser_email',
        'submit_important_communication',
        'submit_newsletter',
        'submit_marketing_and_commercial_material',
        'submit_premium_offer_discount',
        'submit_inactive_email_reminder',
    ]
    list_display = ("subject", "created")
    search_fields = ['subject', ]


@admin.register(PopupMessage)
class PopupMessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created', 'updated', 'active')
    list_filter = ('active', 'created', 'updated')
    search_fields = ('title', 'body')
    readonly_fields = ('created', 'updated')


@admin.register(PopupMessageUserStatus)
class PopupMessageUserStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'popup_message', 'popup_message_active', 'seen')
    list_filter = ('popup_message',)
    search_fields = ('user__username', 'popup_message__title')
    autocomplete_fields = ('user', 'popup_message')

    def popup_message_active(self, obj):
        return obj.popup_message.active
    popup_message_active.short_description = 'Popup Message Active'
    popup_message_active.boolean = True


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created', 'updated', 'params')
    search_fields = ('user__username', 'name')


admin.site.register(Gear, GearAdmin)
admin.site.register(GearMigrationStrategy, GearMigrationStrategyAdmin)
admin.site.register(GearUserInfo)
admin.site.register(GearRenameRecord, GearRenameRecordAdmin)
admin.site.register(Telescope)
admin.site.register(Mount, MountAdmin)
admin.site.register(Camera)
admin.site.register(CameraRenameProposal, CameraRenameProposalAdmin)
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
admin.site.register(BroadcastEmail, BroadcastEmailAdmin)
admin.site.register(ImageEquipmentLog, ImageEquipmentLogAdmin)
