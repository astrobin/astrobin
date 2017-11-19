# Django
from django.contrib import admin

# This app
from .models import NestedComment


class NestedCommentAdmin(admin.ModelAdmin):
    list_display = (
        'content_object',
        'author',
        'text',
        'created',
        'updated',
        'deleted',
    )

    search_fields = (
        'author',
    )

admin.site.register(NestedComment, NestedCommentAdmin)
