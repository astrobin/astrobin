from django.contrib import admin
from django.utils.html import format_html

from .models import CkEditorFile


class CkEditorFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'user', 'uploaded', 'filesize', 'thumbnail_preview')
    list_filter = ('uploaded',)
    search_fields = ('filename', 'user__username')

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.thumbnail.url)
        return "No Thumbnail"
    thumbnail_preview.short_description = "Thumbnail Preview"


admin.site.register(CkEditorFile, CkEditorFileAdmin)
