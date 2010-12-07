from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

from bin import views

urlpatterns = patterns('',
    (r'^$', views.index),
    (r'^show/(?P<id>\d+)/$', views.image_detail),
    (r'^upload/$', views.image_upload),
    (r'^upload/process$', views.image_upload_process),
    (r'^upload/process_image_details$', views.image_upload_process_details),
    (r'^accounts/', include('registration.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^ajax_select/', include('ajax_select.urls')),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^(?P<username>\w+)/$', views.user_page),
    (r'^profile/edit/$', views.user_profile_edit_basic),
    (r'^profile/edit/basic$', views.user_profile_edit_basic),
    (r'^profile/save/basic$', views.user_profile_save_basic),
    (r'^profile/edit/gear$', views.user_profile_edit_gear),
)
