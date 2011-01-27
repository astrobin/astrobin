from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from djangoratings.views import AddRatingFromModel

admin.autodiscover()

from astrobin import views
from astrobin import lookups
from astrobin.models import Image
from astrobin.search import ImageSearchView

urlpatterns = patterns('',
    (r'^$', views.index),
    (r'^no_javascript', views.no_javascript),
    (r'^(?P<id>\d+)/$', views.image_detail),
    (r'^upload/$', views.image_upload),
    (r'^upload/process$', views.image_upload_process),
    (r'^edit/basic/(?P<id>\d+)/$', views.image_edit_basic),
    (r'^edit/gear/(?P<id>\d+)/$', views.image_edit_gear),
    (r'^edit/acquisition/(?P<id>\d+)/$', views.image_edit_acquisition),
    (r'^edit/save/basic/$', views.image_edit_save_basic),
    (r'^edit/save/gear/$', views.image_edit_save_gear),
    (r'^edit/save/acquisition/$', views.image_edit_save_acquisition),
    (r'^delete/(?P<id>\d+)/$', views.image_delete),
    (r'^search/', ImageSearchView()),

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
    (r'rate/(?P<object_id>\d+)/(?P<score>\d+)/', AddRatingFromModel(), {
        'app_label': 'astrobin',
        'model': 'image',
        'field_name': 'rating',
    }),
    (r'get_rating/(?P<image_id>\d+)/', views.image_get_rating),

    (r'^misc/request-progress/$', views.request_progress),
    (r'^users/(?P<username>\w+)/$', views.user_page),
    (r'^follow/(?P<username>\w+)/$', views.follow),
    (r'^unfollow/(?P<username>\w+)/$', views.unfollow),
    (r'^notices/', include('notification.urls')),
    (r'^push_notification/$', views.push_notification),
    (r'^notifications/seen/$', views.mark_notifications_seen),
    (r'^notifications/$', views.notifications),
    (r'^messages/', include('persistent_messages.urls')),
)
