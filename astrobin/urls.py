from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from djangoratings.views import AddRatingFromModel

admin.autodiscover()

from astrobin import views
from astrobin import lookups
from astrobin.models import Image
from astrobin.search import ImageSearchView
from astrobin.forms import AdvancedSearchForm

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^(?P<id>\d+)/$', views.image_detail, name='image_detail'),
    url(r'^full/(?P<id>\d+)/$', views.image_full, name='image_full'),
    url(r'^upload/$', views.image_upload, name='image_upload'),
    url(r'^upload/process$', views.image_upload_process, name='image_upload_process'),
    url(r'^upload/revision/process/$', views.image_revision_upload_process, name='image_revision_upload_process'),
    url(r'^edit/presolve/(?P<id>\d+)/$', views.image_edit_presolve, name='image_edit_presolve'),
    url(r'^edit/basic/(?P<id>\d+)/$', views.image_edit_basic, name='image_edit_basic'),
    url(r'^edit/gear/(?P<id>\d+)/$', views.image_edit_gear, name='image_edit_gear'),
    url(r'^edit/acquisition/(?P<id>\d+)/$', views.image_edit_acquisition, name='image_edit_acquisition'),
    url(r'^edit/makefinal/(?P<id>\d+)/$', views.image_edit_make_final, name='image_edit_make_final'),
    url(r'^edit/revision/makefinal/(?P<id>\d+)/$', views.image_edit_revision_make_final, name='image_edit_revision_make_final'),
    url(r'^edit/license/(?P<id>\d+)/$', views.image_edit_license, name='image_edit_license'),
    url(r'^edit/acquisition/reset/(?P<id>\d+)/$', views.image_edit_acquisition_reset, name='image_edit_acquisition_reset'),
    url(r'^edit/save/presolve/$', views.image_edit_save_presolve, name='image_edit_save_presolve'),
    url(r'^edit/save/basic/$', views.image_edit_save_basic, name='image_edit_save_basic'),
    url(r'^edit/save/gear/$', views.image_edit_save_gear, name='image_edit_save_gear'),
    url(r'^edit/save/acquisition/$', views.image_edit_save_acquisition, name='image_edit_save_acquisition'),
    url(r'^edit/save/license/$', views.image_edit_save_license, name='image_edit_save_license'),
    url(r'^delete/(?P<id>\d+)/$', views.image_delete, name='image_delete'),

    url(r'^search/', ImageSearchView(form_class=AdvancedSearchForm), name='haystack_search'),

       (r'^accounts/', include('registration.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
       (r'^admin/', include(admin.site.urls)),

       (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    url(r'^profile/edit/$', views.user_profile_edit_basic, name='profile_edit_basic'),
    url(r'^profile/edit/basic/$', views.user_profile_edit_basic, name='profile_edit_basic'),
    url(r'^profile/save/basic/$', views.user_profile_save_basic, name='profile_save_basic'),
    url(r'^profile/edit/gear/$', views.user_profile_edit_gear, name='profile_edit_gear'),
    url(r'^profile/save/gear/$', views.user_profile_save_gear, name='profile_save_gear'),
    url(r'^profile/edit/license/$', views.user_profile_edit_license, name='profile_edit_license'),
    url(r'^profile/save/license/$', views.user_profile_save_license, name='profile_save_license'),
    url(r'^profile/edit/flickr/$', views.user_profile_flickr_import, name='profile_flickr_import'),
    url(r'^flickr_auth_callback/$', views.flickr_auth_callback, name='flickr_auth_callback'),
    url(r'^autocomplete/(?P<what>\w+)/$', lookups.autocomplete, name='autocomplete'),
    url(r'^autocomplete_user/(?P<what>\w+)/$', lookups.autocomplete_user, name='autocomplete_user'),
    url(r'^autocomplete_usernames/$', lookups.autocomplete_usernames, name='autocomplete_usernames'),
    url(r'rate/(?P<object_id>\d+)/(?P<score>\d+)/', AddRatingFromModel(), {
            'app_label': 'astrobin',
            'model': 'image',
            'field_name': 'rating',}, name='image_rate'),
    url(r'get_rating/(?P<image_id>\d+)/', views.image_get_rating, name='image_get_rating'),
    url(r'^me/$', views.me, name='me'),
    url(r'^users/(?P<username>\w+)/$', views.user_page, name='user_page'),
    url(r'^follow/(?P<username>\w+)/$', views.follow, name='follow'),
    url(r'^unfollow/(?P<username>\w+)/$', views.unfollow, name='unfollow'),
       (r'^notices/', include('notification.urls')),
    url(r'^push_notification/$', views.push_notification, name='push_notification'),
    url(r'^notifications/seen/$', views.mark_notifications_seen, name='mark_notification_seen'),
    url(r'^notifications/$', views.notifications, name='notifications'),
    url(r'^messages/new/(?P<username>\w+)/$', views.messages_new, name="messages_new"),
    url(r'^messages/save/$', views.messages_save, name="messages_save"),
    url(r'^messages/all/$', views.messages_all, name='messages_all'),
    url(r'^messages/detail/(?P<id>\d+)/$', views.message_detail, name='message_detail'),
       (r'^messages/', include('persistent_messages.urls')),
    url(r'^send_private_message/$', views.send_private_message, name='send_private_message'),
    url(r'^bring_to_attention/$', views.bring_to_attention, name='bring_to_attention'),
    url(r'^requests/$', views.requests, name='requests'),
    url(r'^request/image/additional_information/(?P<image_id>\d+)/$', views.image_request_additional_information, name='image_request_additional_information'),
    url(r'^request/image/fits/(?P<image_id>\d+)/$', views.image_request_fits, name='image_request_fits'),

    url(r'^help/', views.help, name='help'),
    url(r'^faq/', views.faq, name='faq'),
    url(r'^tos/', views.tos, name='tos'),
    url(r'^locations/edit/(?P<id>\d+)/$', views.location_edit, name='location_edit'),
    url(r'^locations/save/$', views.location_save, name='location_save'),
    url(r'^language/set/(?P<lang>\w+)/$', views.set_language, name='set_language'),
)
