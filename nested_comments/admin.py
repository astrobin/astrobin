import logging

from django.contrib import admin

from astrobin.models import UserProfile
from .models import NestedComment
from .services.comment_notifications_service import CommentNotificationsService

logger = logging.getLogger('apps')


class NestedCommentAdmin(admin.ModelAdmin):
    list_display = (
        'content_object',
        'author',
        'text',
        'created',
        'deleted',
        'pending_moderation',
    )

    search_fields = (
        'author__username',
    )

    list_filter = (
        'pending_moderation',
    )

    actions = (
        'approve',
        'delete_and_ban_user',
        'set_pending_moderation',
    )

    def approve(self, request, queryset):
        queryset.update(pending_moderation=None)
        queryset.update(moderator=request.user)

        for comment in queryset:
            CommentNotificationsService(comment).send_notifications()

    approve.short_description = 'Approve'

    def delete_and_ban_user(self, request, queryset):
        queryset.update(deleted=True)
        queryset.update(moderator=request.user)

        for comment in queryset:
            user = comment.author
            if user.userprofile.deleted is None:
                user.userprofile.deleted_reason = UserProfile.DELETE_REASON_BANNED
                user.userprofile.save(keep_deleted=True)
                user.userprofile.delete()
                logger.info("User (%d) was banned" % user.pk)

    delete_and_ban_user.short_description = 'Delete and ban user'

    def set_pending_moderation(self, request, queryset):
        queryset.update(pending_moderation=True)

    set_pending_moderation.short_description = 'Set pending moderation'

admin.site.register(NestedComment, NestedCommentAdmin)
