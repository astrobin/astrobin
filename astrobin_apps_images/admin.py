from django.contrib import admin

from astrobin_apps_platesolving.models import Solution


class SolutionAdmin(admin.ModelAdmin):
    list_display = (
        'get_image_title','get_image_author',
        'job_success', 'image_file')
    list_filter = ('job_success',)

    def get_image_title(self, obj):
        return obj.image.title

    def get_image_author(self, obj):
        return obj.image.user.userprofile

    get_image_title.short_description = 'Image'
    get_image_author.short_description = 'Author'


admin.site.register(Solution, SolutionAdmin)

