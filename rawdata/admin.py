from django.contrib import admin

from rawdata.models import RawImage, PublicDataPool, TemporaryArchive, PrivateSharedFolder


class RawImageAdmin(admin.ModelAdmin):
    list_display = (
        'original_filename',
        'user',
        'size',
        'uploaded',
        'indexed',
        'active',
    )

    list_filter = (
        'indexed',
        'active',
    )

    def queryset(self, request):
        # Default: qs = self.model._default_manager.get_queryset()
        qs = self.model._default_manager.all_with_inactive()
        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = self.ordering or ()  # otherwise we might try to *None, which is bad ;)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs


admin.site.register(RawImage, RawImageAdmin)
admin.site.register(PublicDataPool)
admin.site.register(PrivateSharedFolder)
admin.site.register(TemporaryArchive)
