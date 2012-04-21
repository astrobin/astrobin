from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.views.generic.simple import redirect_to

from djangoratings.views import AddRatingFromModel
from hitcount.views import update_hit_count_ajax

from threaded_messages.views import search as messages_search
from threaded_messages.views import inbox as messages_inbox
from threaded_messages.views import outbox as messages_outbox
from threaded_messages.views import compose as messages_compose
from threaded_messages.views import view as messages_view
from threaded_messages.views import delete as messages_delete
from threaded_messages.views import undelete as messages_undelete
from threaded_messages.views import batch_update as messages_batch_update
from threaded_messages.views import trash as messages_trash
from threaded_messages.views import recipient_search as messages_recipient_search
from threaded_messages.views import message_ajax_reply as messages_message_ajax_reply

from threaded_messages.forms import ComposeForm as MessagesComposeForm

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
    url(r'^edit/watermark/(?P<id>\d+)/$', views.image_edit_watermark, name='image_edit_watermark'),
    url(r'^edit/gear/(?P<id>\d+)/$', views.image_edit_gear, name='image_edit_gear'),
    url(r'^edit/acquisition/(?P<id>\d+)/$', views.image_edit_acquisition, name='image_edit_acquisition'),
    url(r'^edit/makefinal/(?P<id>\d+)/$', views.image_edit_make_final, name='image_edit_make_final'),
    url(r'^edit/revision/makefinal/(?P<id>\d+)/$', views.image_edit_revision_make_final, name='image_edit_revision_make_final'),
    url(r'^edit/license/(?P<id>\d+)/$', views.image_edit_license, name='image_edit_license'),
    url(r'^edit/acquisition/reset/(?P<id>\d+)/$', views.image_edit_acquisition_reset, name='image_edit_acquisition_reset'),
    url(r'^edit/save/presolve/$', views.image_edit_save_presolve, name='image_edit_save_presolve'),
    url(r'^edit/save/basic/$', views.image_edit_save_basic, name='image_edit_save_basic'),
    url(r'^edit/save/watermark/$', views.image_edit_save_watermark, name='image_edit_save_watermark'),
    url(r'^edit/save/gear/$', views.image_edit_save_gear, name='image_edit_save_gear'),
    url(r'^edit/save/acquisition/$', views.image_edit_save_acquisition, name='image_edit_save_acquisition'),
    url(r'^edit/save/license/$', views.image_edit_save_license, name='image_edit_save_license'),
    url(r'^delete/(?P<id>\d+)/$', views.image_delete, name='image_delete'),
    url(r'^delete/revision/(?P<id>\d+)/$', views.image_delete_revision, name='image_delete_revision'),
    url(r'^delete/original/(?P<id>\d+)/$', views.image_delete_original, name='image_delete_original'),
    url(r'^promote/(?P<id>\d+)/$', views.image_promote, name='image_promote'),
    url(r'^demote/(?P<id>\d+)/$', views.image_demote, name='image_demote'),

    url(r'^search/', ImageSearchView(form_class=AdvancedSearchForm), name='haystack_search'),

       (r'^accounts/', include('registration.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
       (r'^admin/', include(admin.site.urls)),
       (r'^sitestatic/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    url(r'^profile/edit/$', views.user_profile_edit_basic, name='profile_edit_basic'),
    url(r'^profile/edit/basic/$', views.user_profile_edit_basic, name='profile_edit_basic'),
    url(r'^profile/save/basic/$', views.user_profile_save_basic, name='profile_save_basic'),
    url(r'^profile/edit/gear/$', views.user_profile_edit_gear, name='profile_edit_gear'),
    url(r'^profile/save/gear/$', views.user_profile_save_gear, name='profile_save_gear'),
    url(r'^profile/edit/locations/$', views.user_profile_edit_locations, name='profile_edit_locations'),
    url(r'^profile/save/locations/$', views.user_profile_save_locations, name='profile_save_locations'),
    url(r'^profile/edit/license/$', views.user_profile_edit_license, name='profile_edit_license'),
    url(r'^profile/save/license/$', views.user_profile_save_license, name='profile_save_license'),
    url(r'^profile/edit/flickr/$', views.user_profile_flickr_import, name='profile_flickr_import'),
    url(r'^flickr_auth_callback/$', views.flickr_auth_callback, name='flickr_auth_callback'),
    url(r'^profile/edit/preferences/$', views.user_profile_edit_preferences, name='profile_edit_preferences'),
    url(r'^profile/save/preferences/$', views.user_profile_save_preferences, name='profile_save_preferences'),
    url(r'^autocomplete/(?P<what>\w+)/$', lookups.autocomplete, name='autocomplete'),
    url(r'^autocomplete_user/(?P<what>\w+)/$', lookups.autocomplete_user, name='autocomplete_user'),
    url(r'^autocomplete_usernames/$', lookups.autocomplete_usernames, name='autocomplete_usernames'),
    url(r'rate/(?P<object_id>\d+)/(?P<score>\d+)/', AddRatingFromModel(), {
            'app_label': 'astrobin',
            'model': 'image',
            'field_name': 'rating',}, name='image_rate'),
    url(r'get_rating/(?P<image_id>\d+)/', views.image_get_rating, name='image_get_rating'),

    url(r'^me/$', views.me, name='me'),
    url(r'^users/(?P<username>[\w.@+-]+)/$', views.user_page, name='user_page'),
    url(r'^users/(?P<username>[\w.@+-]+)/favorites/$', views.user_page_favorites, name='user_page_favorites'),
    url(r'^users/(?P<username>[\w.@+-]+)/card/$', views.user_page_card, name='user_page_card'),
    url(r'^users/(?P<username>[\w.@+-]+)/plots/$', views.user_page_plots, name='user_page_plots'),
    url(r'^users/(?P<username>[\w.@+-]+)/stats/integration_hours/(?P<period>\w+)/(?P<since>\d+)/$',
        views.user_profile_stats_get_integration_hours_ajax,
        name = 'stats_integration_hours'),
    url(r'^users/(?P<username>[\w.@+-]+)/stats/integration_hours_by_gear/(?P<period>\w+)/$',
        views.user_profile_stats_get_integration_hours_by_gear_ajax,
        name = 'stats_integration_hours_by_gear'),
    url(r'^users/(?P<username>[\w.@+-]+)/stats/uploaded_images/(?P<period>\w+)/$',
        views.user_profile_stats_get_uploaded_images_ajax,
        name = 'stats_uploaded_images'),
    url(r'^users/(?P<username>[\w.@+-]+)/stats/views/(?P<period>\w+)/$',
        views.user_profile_stats_get_views_ajax,
        name = 'stats_views'),
    url(r'^(?P<id>\d+)/stats/views/(?P<period>\w+)/$',
        views.stats_get_image_views_ajax,
        name = 'stats_image_views'),

     url(r'^stats/camera-types-trend/$',
        views.stats_camera_types_trend_ajax,
        name = 'stats_camera_types_trend'),
     url(r'^stats/telescope-types-trend/$',
        views.stats_telescope_types_trend_ajax,
        name = 'stats_telescope_types_trend'),
 
    url(r'^subject/stats/images-monthly/(?P<id>\d+)/$',
        views.stats_subject_images_monthly_ajax,
        name = 'stats_subject_images_monthly'),
     url(r'^subject/stats/integration-monthly/(?P<id>\d+)/$',
        views.stats_subject_integration_monthly_ajax,
        name = 'stats_subject_integration_monthly'),
     url(r'^subject/stats/total-images/(?P<id>\d+)/$',
        views.stats_subject_total_images_ajax,
        name = 'stats_subject_total_images'),
     url(r'^subject/stats/camera-types/(?P<id>\d+)/$',
        views.stats_subject_camera_types_ajax,
        name = 'stats_subject_camera_types'),
     url(r'^subject/stats/telescope-types/(?P<id>\d+)/$',
        views.stats_subject_telescope_types_ajax,
        name = 'stats_subject_telescope_types'),
  
    url(r'^follow/(?P<username>[\w.@+-]+)/$', views.follow, name='follow'),
    url(r'^unfollow/(?P<username>[\w.@+-]+)/$', views.unfollow, name='unfollow'),
    url(r'^follow_gear/(?P<id>\d+)/$', views.follow_gear, name='follow_gear'),
    url(r'^unfollow_gear/(?P<id>\d+)/$', views.unfollow_gear, name='unfollow_gear'),
    url(r'^follow_subject/(?P<id>\d+)/$', views.follow_subject, name='follow_subject'),
    url(r'^unfollow_subject/(?P<id>\d+)/$', views.unfollow_subject, name='unfollow_subject'),

       (r'^notices/', include('notification.urls')),
    url(r'^push_notification/$', views.push_notification, name='push_notification'),
    url(r'^notifications/seen/$', views.mark_notifications_seen, name='mark_notification_seen'),
    url(r'^notifications/$', views.notifications, name='notifications'),

    url(r'^messages/inbox/$', messages_inbox, {'template_name': 'messages/inbox.html'}, name='messages_inbox'),
    url(r'^messages/compose/$', messages_compose, {'template_name': 'messages/compose.html'}, name='messages_compose'),
    url(r'^messages/compose/(?P<recipient>[\w.@+-]+)/$', messages_compose, {'template_name': 'messages/compose.html'}, name='messages_compose_to'),
    url(r'^messages/view/(?P<thread_id>[\d]+)/$', messages_view, {'template_name': 'messages/view.html'}, name='messages_detail'),
    url(r'^messages/delete/(?P<thread_id>[\d]+)/$', messages_delete, name='messages_delete'),
    url(r'^messages/batch-update/$', messages_batch_update, name='messages_batch_update'),
    url(r"^messages/recipient-search/$", messages_recipient_search, name="recipient_search"),
    url(r'^messages/message-reply/(?P<thread_id>[\d]+)/$', messages_message_ajax_reply, {'template_name': 'messages/message_list_view.html'}, name="message_reply"),
    # modal composing 
    url(r'^messages/modal-compose/(?P<recipient>[\w.@+-]+)/$', messages_compose, {
                            "template_name":"messages/modal_compose.html",
                            "form_class": MessagesComposeForm
                        }, name='modal_messages_compose_to'),
    url(r'^messages/modal-compose/$', messages_compose, {
                            "template_name":"messages/modal_compose.html",
                            "form_class": MessagesComposeForm
                        }, name='modal_messages_compose'),

    url(r'^send_private_message/$', views.send_private_message, name='send_private_message'),

    url(r'^(?P<id>\d+)/bring-to-attention/$', views.bring_to_attention, name='bring_to_attention'),
    url(r'^bring-to-attention/process/$', views.bring_to_attention_process, name='bring_to_attention_process'),
    url(r'^(?P<id>\d+)/bring-to-attention/complete/$', views.bring_to_attention_complete, name='bring_to_attention_complete'),

    url(r'^requests/$', views.requests, name='requests'),

    url(r'^request/image/additional-information/(?P<image_id>\d+)/$', views.image_request_additional_information, name='image_request_additional_information'),
    url(r'^request/image/additional-information/process/(?P<image_id>\d+)/$', views.image_request_additional_information_process, name='image_request_additional_information_process'),
    url(r'^request/image/additional-information/complete/(?P<image_id>\d+)/$', views.image_request_additional_information_complete, name='image_request_additional_information_complete'),

    url(r'^request/image/fits/(?P<image_id>\d+)/$', views.image_request_fits, name='image_request_fits'),
    url(r'^request/image/fits/process/(?P<image_id>\d+)/$', views.image_request_fits_process, name='image_request_fits_process'),
    url(r'^request/image/fits/complete/(?P<image_id>\d+)/$', views.image_request_fits_complete, name='image_request_fits_complete'),

    url(r'^request/mark/fulfilled/(?P<request_id>\d+)/$', views.request_mark_fulfilled, name='request_mark_fulfilled'),

    url(r'^stats/', views.stats, name='stats'),
    url(r'^leaderboard/', views.leaderboard, name='leaderboard'),
    url(r'^help/', views.help, name='help'),
    url(r'^faq/', views.faq, name='faq'),
    url(r'^tos/', views.tos, name='tos'),
    url(r'^guidelines/', views.guidelines, name='guidelines'),
    url(r'^language/set/(?P<lang>\w+)/$', views.set_language, name='set_language'),

    url(r'^blog/', include('zinnia.urls')),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^tinymce/', include('tinymce.urls')),

    url(r'^explore/choose/$', views.expore_choose, name='explore_choose'),
    url(r'^explore/wall/$', views.wall, name='wall'),
    url(r'^explore/popular/$', views.popular, name='popular'),
    url(r'^explore/nightly/$', views.nightly, name='nightly'),
    url(r'^explore/messier/$', views.messier, name='messier'),
    url(r'^explore/messier/nominate/(?P<id>\d+)/$', views.messier_nomination, name='messier_nomination'),
    url(r'^explore/messier/nominate/process/$', views.messier_nomination_process, name='messier_nomination_process'),
    url(r'^explore/fits/$', views.fits, name='fits'),

    url(r'^hitcount/$', update_hit_count_ajax, name='hitcount_update_ajax'),

    url(r'^image_comments/save/$', views.image_comment_save, name='image_comment_save'),
    url(r'^image_comments/delete/(?P<id>\d+)/$', views.image_comment_delete, name='image_comment_delete'),
    url(r'^image_comments/get/(?P<id>\d+)/$', views.image_comment_get, name='image_comment_get'),
    url(r'^image_comments/edit/$', views.image_comment_edit, name='image_comment_edit'),

    url(r'^get_edit_gear_form/(?P<id>\d+)/$', views.get_edit_gear_form, name='get_edit_gear_form'),
    url(r'^save_gear_details/$', views.save_gear_details, name='save_gear_details'),
    url(r'^get_is_gear_complete/(?P<id>\d+)/$', views.get_is_gear_complete, name='get_is_gear_complete'),

    url(r'^favorite_ajax/(?P<id>\d+)/$', views.favorite_ajax, name='favorite_ajax'),

    url(r'^gear_popover_ajax/(?P<id>\d+)/$', views.gear_popover_ajax, name='gear_popover_ajax'),
    url(r'^subject_popover_ajax/(?P<id>\d+)/$', views.subject_popover_ajax, name='subject_popover_ajax'),

    url(r'^subject/(?P<id>\d+)/$', views.subject_page, name='subject_page'),

    url(r'^contact/', include("contact_form.urls", namespace="contact_form")),
    url(r'^avatar/', include('avatar.urls')),

    url(r'^get-gear-ajax/(?P<image_id>\d+)/$', views.get_gear_ajax, name='get_gear_ajax'),
)

