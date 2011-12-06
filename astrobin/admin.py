from astrobin.models import *
from django.contrib import admin

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


admin.site.register(Gear)
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
