from bin.models import *
from django.contrib import admin
from ajax_select import make_ajax_form
from ajax_select.admin import AjaxSelectAdmin
from ajax_select.fields import autoselect_fields_check_can_add

admin.site.register(Gear)
admin.site.register(Telescope)
admin.site.register(Mount)
admin.site.register(Camera)
admin.site.register(FocalReducer)
admin.site.register(Subject)
admin.site.register(Image)
admin.site.register(ABPOD)

class UserProfileAdmin(AjaxSelectAdmin):
    form = make_ajax_form(UserProfile, dict(telescopes='telescope'))

    def get_form(self, request, obj=None, **kwargs):
        form = super(AjaxSelectAdmin, self).get_form(request, obj, **kwargs) 
        autoselect_fields_check_can_add(form, self.model, request.user)
        return form
        
admin.site.register(UserProfile, UserProfileAdmin)
