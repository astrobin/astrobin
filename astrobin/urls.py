from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

from astrobin import views
from astrobin import lookups

urlpatterns = patterns('',
    (r'^$', views.index),
    (r'^show/(?P<id>\d+)/$', views.image_detail),
    (r'^upload/$', views.image_upload),
    (r'^upload/process$', views.image_upload_process),
    (r'^edit/basic/(?P<id>\d+)/$', views.image_edit_basic),
    (r'^edit/gear/(?P<id>\d+)/$', views.image_edit_gear),
    (r'^edit/acquisition/(?P<id>\d+)/$', views.image_edit_acquisition),
    (r'^edit/save/basic/$', views.image_edit_save_basic),
    (r'^edit/save/gear/$', views.image_edit_save_gear),
    (r'^edit/save/acquisition/$', views.image_edit_save_acquisition),

    (r'^accounts/', include('registration.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^profile/edit/$', views.user_profile_edit_basic),
    (r'^profile/edit/basic/$', views.user_profile_edit_basic),
    (r'^profile/save/basic/$', views.user_profile_save_basic),
    (r'^profile/edit/gear/$', views.user_profile_edit_gear),
    (r'^profile/save/gear/$', views.user_profile_save_gear),
    (r'^profile/edit/flickr/$', views.user_profile_flickr_import),
    (r'^flickr_auth_callback/$', views.flickr_auth_callback),
    (r'^autocomplete/(?P<what>\w+)/$', lookups.autocomplete),
    (r'^autocomplete_user/(?P<what>\w+)/$', lookups.autocomplete_user),

    (r'^misc/request-progress/$', views.request_progress),
    (r'^(?P<username>\w+)/$', views.user_page),
)
