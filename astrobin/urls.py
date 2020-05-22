from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic import RedirectView
from django.views.static import serve
from rest_framework.authtoken.views import obtain_auth_token
from tastypie.api import Api
from threaded_messages.views import batch_update as messages_batch_update
from threaded_messages.views import compose as messages_compose
from threaded_messages.views import delete as messages_delete
from threaded_messages.views import inbox as messages_inbox
from threaded_messages.views import message_ajax_reply as messages_message_ajax_reply
from threaded_messages.views import recipient_search as messages_recipient_search
from threaded_messages.views import view as messages_view

from astrobin import lookups
from astrobin.api import (
    TopPickResource,
    ImageOfTheDayResource,
    ImageResource,
    ImageRevisionResource,
    LocationResource,
    CollectionResource,
    UserProfileResource)
from astrobin.search import AstroBinSearchView
from astrobin.views import (
    api as api_views,
    explore as explore_views,
    image as image_views,
    moderation as moderation_views,
    collections as collections_views,
    registration as registration_views,
    special as special_views,

    index,

    image_edit_acquisition,
    image_edit_acquisition_reset,
    image_edit_license,
    image_edit_platesolving_settings,
    image_restart_platesolving,
    image_edit_platesolving_advanced_settings,
    image_restart_advanced_platesolving,
    image_edit_make_final,
    image_edit_revision_make_final,
    image_edit_save_acquisition,
    image_edit_save_license,
    image_edit_save_watermark,
    image_edit_watermark,
    image_upload,
    image_upload_process,
    image_revision_upload_process,

    stats_get_image_views_ajax,
    me,
    user_page,
    user_page_api_keys,
    user_ban,
    user_page_bookmarks,
    user_page_liked,
    user_page_commercial_products,
    user_page_followers,
    user_page_following,
    user_page_plots,
    user_profile_stats_get_integration_hours_ajax,
    user_profile_stats_get_integration_hours_by_gear_ajax,
    user_profile_stats_get_uploaded_images_ajax,
    user_profile_stats_get_views_ajax,

    flickr_auth_callback,
    user_profile_delete,
    user_profile_edit_basic,
    user_profile_edit_commercial,
    user_profile_flickr_import,
    user_profile_edit_gear,
    user_profile_edit_gear_remove,
    user_profile_edit_license,
    user_profile_edit_locations,
    user_profile_edit_preferences,
    user_profile_edit_retailer,
    user_profile_save_basic,
    user_profile_save_gear,
    user_profile_save_license,
    user_profile_save_locations,
    user_profile_save_preferences,
    user_profile_seen_realname,
    user_profile_seen_email_permissions,

    commercial_products_claim,
    commercial_products_edit,
    commercial_products_merge,
    retailed_products_claim,
    retailed_products_edit,
    retailed_products_merge,
    retailed_products_unclaim,
    commercial_products_save,
    commercial_products_unclaim,

    gear_page,
    gear_by_ids,
    gear_by_image,
    gear_by_make,
    gear_fix,
    gear_fix_save,
    gear_fix_thanks,
    gear_review_save,
    gear_popover_ajax,
    get_makes_by_type,
    get_edit_gear_form,
    get_empty_edit_gear_form,
    get_gear_user_info_form,
    get_is_gear_complete,
    save_gear_details,
    save_gear_user_info,
    user_popover_ajax,

    stats_camera_types_trend_ajax,
    stats_telescope_types_trend_ajax,
    stats_subject_type_trend_ajax,
    stats_subject_images_monthly_ajax,
    stats_subject_camera_types_ajax,
    stats_subject_telescope_types_ajax,
    stats_subject_total_images_ajax,
    stats_subject_integration_monthly_ajax,

    api_help,
    trending_astrophotographers,
    stats,

    set_language
)
from astrobin.views.profile.download_data_view import DownloadDataView

admin.autodiscover()

# These are the old API, not djangorestframework
v1_api = Api(api_name='v1')
v1_api.register(LocationResource())
v1_api.register(ImageResource())
v1_api.register(ImageRevisionResource())
v1_api.register(TopPickResource())
v1_api.register(ImageOfTheDayResource())
v1_api.register(CollectionResource())
v1_api.register(UserProfileResource())

urlpatterns = []

if settings.DEBUG or settings.TESTING:
    import debug_toolbar

    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
    INTERNAL_IPS = ["*"]

urlpatterns += [
    ###########################################################################
    ### DJANGO VIEWS                                                        ###
    ###########################################################################

    url(r'^admin/', include(admin.site.urls)),

    ###########################################################################
    ### THIRD PARTY APPS VIEWS                                              ###
    ###########################################################################

    # override the default urls
    url(r'^accounts/password/change/$',
        auth_views.password_change,
        name='password_change'),
    url(r'^accounts/password/change/done/$',
        auth_views.password_change_done,
        name='password_change_done'),
    url(r'^accounts/password/reset/$',
        auth_views.password_reset,
        name='password_reset'),
    url(r'^accounts/password/reset/done/$',
        auth_views.password_reset_done,
        name='password_reset_done'),
    url(r'^accounts/password/reset/complete/$',
        auth_views.password_reset_complete,
        name='password_reset_complete'),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        auth_views.password_reset_confirm,
        name='password_reset_confirm'),
    # and now add the registration urls
    url(r'^accounts/register/$',
        registration_views.AstroBinRegistrationView.as_view(),
        name='registration_register'),
    url(r'^accounts/', include('registration.backends.hmac.urls')),
    url(r'^accounts/email/', include('change_email.urls')),

    url(r'^activity/', include('actstream.urls')),
    url(r'^avatar/', include('avatar.urls')),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^contact/', include("contact_form.urls", namespace="contact_form")),
    url(r'^forum/', include('pybb.urls', namespace='pybb')),
    url(r'hitcount/', include('hitcount.urls', namespace='hitcount')),
    url(r'^persistent_messages/', include('persistent_messages.urls')),
    url(r'^subscriptions/', include('subscription.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^bouncy/', include('django_bouncy.urls')),
    url(r'^paypal/', include('paypal.standard.ipn.urls')),
    url(r'^progressbarupload/', include('progressbarupload.urls')),

    ###########################################################################
    ### API VIEWS                                                           ###
    ###########################################################################

    url(r'^api/', include(v1_api.urls)),
    url(r'^api/request-key/$', api_views.AppApiKeyRequestView.as_view(), name='app_api_key_request'),
    url(r'^api/request-key/complete/$', api_views.AppApiKeyRequestCompleteView.as_view(),
        name='app_api_key_request_complete'),
    url(r'^api/v2/api-auth-token/', obtain_auth_token),
    url(r'^api/v2/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v2/common/', include('common.api_urls')),
    url(r'^api/v2/nestedcomments/', include('nested_comments.api_urls')),
    url(r'^api/v2/platesolving/', include('astrobin_apps_platesolving.api_urls')),
    url(r'^api/v2/notifications/', include('astrobin_apps_notifications.api.urls')),

    ###########################################################################
    ### OWN APPS VIEWS                                                      ###
    ###########################################################################

    url(r'^donations/', include('astrobin_apps_donations.urls')),
    url(r'^notifications/', include('astrobin_apps_notifications.urls')),
    url(r'^platesolving/', include('astrobin_apps_platesolving.urls')),
    url(r'^premium/', include('astrobin_apps_premium.urls')),
    url(r'^toggleproperties/', include('toggleproperties.urls')),
    url(r'^users_app/', include('astrobin_apps_users.urls')),
    url(r'^groups/', include('astrobin_apps_groups.urls')),
    url(r'^iotd/', include('astrobin_apps_iotd.urls')),

    ###########################################################################
    ### HOME VIEWS                                                          ###
    ###########################################################################

    url(r'^$', index, name='index'),

    ###########################################################################
    ### SPECIAL VIEWS                                                       ###
    ###########################################################################

    url(r'^ads.txt$', special_views.AdsTxtView.as_view(), name='ads_txt'),
    url(r'^favicon.ico$',
        RedirectView.as_view(url=staticfiles_storage.url('astrobin/favicon.ico'), permanent=False),
        name='favicon'),

    ###########################################################################
    ### SEARCH VIEWS                                                        ###
    ###########################################################################

    url(r'^search/', AstroBinSearchView.as_view(), name='haystack_search'),

    ###########################################################################
    ### EXPLORE VIEWS                                                       ###
    ###########################################################################

    url(r'^explore/top-picks/$', explore_views.TopPicksView.as_view(), name='top_picks'),

    ###########################################################################
    ### USER VIEWS                                                          ###
    ###########################################################################

    url(r'^(?P<id>\d+)/stats/views/(?P<period>\w+)/$', stats_get_image_views_ajax, name='stats_image_views'),
    url(r'^me/$', me, name='me'),
    url(r'^users/(?P<username>[\w.@+-]*)/$', user_page, name='user_page'),
    url(r'^users/(?P<username>[\w.@+-]*)/collections/$', collections_views.UserCollectionsList.as_view(),
        name='user_collections_list'),
    url(r'^users/(?P<username>[\w.@+-]*)/collections/create/$', collections_views.UserCollectionsCreate.as_view(),
        name='user_collections_create'),
    url(r'^users/(?P<username>[\w.@+-]*)/collections/(?P<collection_pk>\d+)/$',
        collections_views.UserCollectionsDetail.as_view(), name='user_collections_detail'),
    url(r'^users/(?P<username>[\w.@+-]*)/collections/(?P<collection_pk>\d+)/update/$',
        collections_views.UserCollectionsUpdate.as_view(), name='user_collections_update'),
    url(r'^users/(?P<username>[\w.@+-]*)/collections/(?P<collection_pk>\d+)/add-remove-images/$',
        collections_views.UserCollectionsAddRemoveImages.as_view(), name='user_collections_add_remove_images'),
    url(r'^users/(?P<username>[\w.@+-]*)/collections/(?P<collection_pk>\d+)/quick-edit/key-value-pairs$',
        collections_views.UserCollectionsQuickEditKeyValueTags.as_view(),
        name='user_collections_quick_edit_key_value_tags'),
    url(r'^users/(?P<username>[\w.@+-]*)/collections/(?P<collection_pk>\d+)/delete/$',
        collections_views.UserCollectionsDelete.as_view(), name='user_collections_delete'),
    url(r'^users/(?P<username>[\w.@+-]*)/apikeys/$', user_page_api_keys, name='user_page_api_keys'),
    url(r'^users/(?P<username>[\w.@+-]*)/ban/$', user_ban, name='user_ban'),
    url(r'^users/(?P<username>[\w.@+-]*)/bookmarks/$', user_page_bookmarks, name='user_page_bookmarks'),
    url(r'^users/(?P<username>[\w.@+-]*)/liked/$', user_page_liked, name='user_page_liked'),
    url(r'^users/(?P<username>[\w.@+-]*)/commercial/products/$', user_page_commercial_products,
        name='user_page_commercial_products'),
    url(r'^users/(?P<username>[\w.@+-]*)/followers/$', user_page_followers, name='user_page_followers'),
    url(r'^users/(?P<username>[\w.@+-]*)/following/$', user_page_following, name='user_page_following'),
    url(r'^users/(?P<username>[\w.@+-]*)/plots/$', user_page_plots, name='user_page_plots'),
    url(r'^users/(?P<username>[\w.@+-]*)/stats/integration_hours/(?P<period>\w+)/(?P<since>\d+)/$',
        user_profile_stats_get_integration_hours_ajax, name='stats_integration_hours'),
    url(r'^users/(?P<username>[\w.@+-]*)/stats/integration_hours_by_gear/(?P<period>\w+)/$',
        user_profile_stats_get_integration_hours_by_gear_ajax, name='stats_integration_hours_by_gear'),
    url(r'^users/(?P<username>[\w.@+-]*)/stats/uploaded_images/(?P<period>\w+)/$',
        user_profile_stats_get_uploaded_images_ajax, name='stats_uploaded_images'),
    url(r'^users/(?P<username>[\w.@+-]*)/stats/views/(?P<period>\w+)/$', user_profile_stats_get_views_ajax,
        name='stats_views'),

    ###########################################################################
    ### PROFILE VIEWS                                                       ###
    ###########################################################################

    url(r'^flickr_auth_callback/$', flickr_auth_callback, name='flickr_auth_callback'),
    url(r'^profile/delete/$', user_profile_delete, name='profile_delete'),
    url(r'^profile/edit/$', user_profile_edit_basic, name='profile_edit_basic'),
    url(r'^profile/edit/basic/$', user_profile_edit_basic, name='profile_edit_basic'),
    url(r'^profile/edit/commercial/$', user_profile_edit_commercial, name='profile_edit_commercial'),
    url(r'^profile/edit/flickr/$', user_profile_flickr_import, name='profile_flickr_import'),
    url(r'^profile/edit/gear/$', user_profile_edit_gear, name='profile_edit_gear'),
    url(r'^profile/edit/gear/remove/(?P<id>\d+)/$', user_profile_edit_gear_remove, name='profile_edit_gear_remove'),
    url(r'^profile/edit/license/$', user_profile_edit_license, name='profile_edit_license'),
    url(r'^profile/edit/locations/$', user_profile_edit_locations, name='profile_edit_locations'),
    url(r'^profile/edit/preferences/$', user_profile_edit_preferences, name='profile_edit_preferences'),
    url(r'^profile/download-data/$', DownloadDataView.as_view(), name='profile_download_data'),
    url(r'^profile/edit/retailer/$', user_profile_edit_retailer, name='profile_edit_retailer'),
    url(r'^profile/save/basic/$', user_profile_save_basic, name='profile_save_basic'),
    url(r'^profile/save/gear/$', user_profile_save_gear, name='profile_save_gear'),
    url(r'^profile/save/license/$', user_profile_save_license, name='profile_save_license'),
    url(r'^profile/save/locations/$', user_profile_save_locations, name='profile_save_locations'),
    url(r'^profile/save/preferences/$', user_profile_save_preferences, name='profile_save_preferences'),
    url(r'^profile/seen/realname/$', user_profile_seen_realname, name='profile_seen_realname'),
    url(r'^profile/seen/email-permissions/$', user_profile_seen_email_permissions,
        name='profile_seen_email_permissions'),

    ###########################################################################
    ### AUTOCOMPLETE VIEWS                                                 ###
    ###########################################################################

    url(r'^autocomplete/(?P<what>\w+)/$', lookups.autocomplete, name='autocomplete'),
    url(r'^autocomplete_user/(?P<what>\w+)/$', lookups.autocomplete_user, name='autocomplete_user'),
    url(r'^autocomplete_usernames/$', lookups.autocomplete_usernames, name='autocomplete_usernames'),

    ###########################################################################
    ### AFFILIATION PLATFORM VIEWS                                          ###
    ###########################################################################

    url(r'^commercial/products/claim/(?P<id>\d+)/$', commercial_products_claim, name='commercial_products_claim'),
    url(r'^commercial/products/edit/(?P<id>\d+)/$', commercial_products_edit, name='commercial_products_edit'),
    url(r'^commercial/products/merge/(?P<from_id>\d+)/(?P<to_id>\d+)/$', commercial_products_merge,
        name='commercial_products_merge'),
    url(r'^commercial/products/retailed/claim/(?P<id>\d+)/$', retailed_products_claim, name='retailed_products_claim'),
    url(r'^commercial/products/retailed/edit/(?P<id>\d+)/$', retailed_products_edit, name='retailed_products_edit'),
    url(r'^commercial/products/retailed/merge/(?P<from_id>\d+)/(?P<to_id>\d+)/$', retailed_products_merge,
        name='retailedgg_products_merge'),
    url(r'^commercial/products/retailed/unclaim/(?P<id>\d+)/$', retailed_products_unclaim,
        name='retailed_products_unclaim'),
    url(r'^commercial/products/save/(?P<id>\d+)/$', commercial_products_save, name='commercial_products_save'),
    url(r'^commercial/products/unclaim/(?P<id>\d+)/$', commercial_products_unclaim, name='commercial_products_unclaim'),

    ###########################################################################
    ### GEAR VIEWS                                                          ###
    ###########################################################################

    url(r'^gear/(?P<id>\d+)/(?:(?P<slug>[a-z0-9-_]+)/)?$', gear_page, name='gear_page'),
    url(r'^gear/by-ids/(?P<ids>([0-9]+,?)+)/$', gear_by_ids, name='gear_by_ids'),
    url(r'^gear/by-image/(?P<image_id>\d+)/$', gear_by_image, name='gear_by_image'),
    url(r'^gear/by-make/(?P<make>[(\w|\W).+-]*)/$', gear_by_make, name='gear_by_make'),
    url(r'^gear/fix/(?P<id>\d+)/$', gear_fix, name='gear_fix'),
    url(r'^gear/fix/save/$', gear_fix_save, name='gear_fix_save'),
    url(r'^gear/fix/thanks/$', gear_fix_thanks, name='gear_fix_thanks'),
    url(r'^gear/review/save/$', gear_review_save, name='gear_review_save'),
    url(r'^gear_popover_ajax/(?P<id>\d+)/$', gear_popover_ajax, name='gear_popover_ajax'),
    url(r'^get-makes-by-type/(?P<klass>\w+)/$', get_makes_by_type, name='get_makes_by_type'),
    url(r'^get_edit_gear_form/(?P<id>\d+)/$', get_edit_gear_form, name='get_edit_gear_form'),
    url(r'^get_empty_edit_gear_form/(?P<gear_type>\w+)/$', get_empty_edit_gear_form, name='get_empty_edit_gear_form'),
    url(r'^get_gear_user_info_form/(?P<id>\d+)/$', get_gear_user_info_form, name='get_gear_user_info_form'),
    url(r'^get_is_gear_complete/(?P<id>\d+)/$', get_is_gear_complete, name='get_is_gear_complete'),
    url(r'^save_gear_details/$', save_gear_details, name='save_gear_details'),
    url(r'^save_gear_user_info/$', save_gear_user_info, name='save_gear_user_info'),
    url(r'^user_popover_ajax/(?P<username>[\w.@+-]+)/$', user_popover_ajax, name='user_popover_ajax'),

    ###########################################################################
    ### STATS VIEWS                                                         ###
    ###########################################################################

    url(r'^stats/camera-types-trend/$', stats_camera_types_trend_ajax, name='stats_camera_types_trend'),
    url(r'^stats/subject-type-trend/$', stats_subject_type_trend_ajax, name='stats_subject_type_trend'),
    url(r'^stats/telescope-types-trend/$', stats_telescope_types_trend_ajax, name='stats_telescope_types_trend'),

    ###########################################################################
    ### SUBJECT VIEWS                                                       ###
    ###########################################################################

    url(r'^subject/stats/camera-types/(?P<id>\d+)/$', stats_subject_camera_types_ajax,
        name='stats_subject_camera_types'),
    url(r'^subject/stats/images-monthly/(?P<id>\d+)/$', stats_subject_images_monthly_ajax,
        name='stats_subject_images_monthly'),
    url(r'^subject/stats/integration-monthly/(?P<id>\d+)/$', stats_subject_integration_monthly_ajax,
        name='stats_subject_integration_monthly'),
    url(r'^subject/stats/telescope-types/(?P<id>\d+)/$', stats_subject_telescope_types_ajax,
        name='stats_subject_telescope_types'),
    url(r'^subject/stats/total-images/(?P<id>\d+)/$', stats_subject_total_images_ajax,
        name='stats_subject_total_images'),

    ###########################################################################
    ### MESSAGES VIEWS                                                      ###
    ###########################################################################

    url(r"^messages/recipient-search/$", messages_recipient_search, name="recipient_search"),
    url(r'^messages/batch-update/$', messages_batch_update, name='messages_batch_update'),
    url(r'^messages/compose/$', messages_compose, {'template_name': 'messages/compose.html'}, name='messages_compose'),
    url(r'^messages/compose/(?P<recipient>[\w.@+-]+)/$', messages_compose, {'template_name': 'messages/compose.html'},
        name='messages_compose_to'),
    url(r'^messages/delete/(?P<thread_id>[\d]+)/$', messages_delete, name='messages_delete'),
    url(r'^messages/inbox/$', messages_inbox, {'template_name': 'messages/inbox.html'}, name='messages_inbox'),
    url(r'^messages/message-reply/(?P<thread_id>[\d]+)/$', messages_message_ajax_reply,
        {'template_name': 'messages/message_list_view.html'}, name="message_reply"),
    url(r'^messages/view/(?P<thread_id>[\d]+)/$', messages_view, {'template_name': 'messages/view.html'},
        name='messages_detail'),

    ###########################################################################
    ### MODERATION VIEWS                                                    ###
    ###########################################################################

    url(r'^moderate/images/$', moderation_views.ImageModerationListView.as_view(),
        name='image_moderation'),
    url(r'^moderate/images/spam/$',
        moderation_views.ImageModerationSpamListView.as_view(),
        name='image_moderation_view_spam'),
    url(r'^moderate/images/mark-as-spam/$',
        moderation_views.ImageModerationMarkAsSpamView.as_view(),
        name='image_moderation_mark_as_spam'),
    url(r'^moderate/images/mark-as-ham/$',
        moderation_views.ImageModerationMarkAsHamView.as_view(),
        name='image_moderation_mark_as_ham'),
    url(r'^moderate/images/ban-all/$',
        moderation_views.ImageModerationBanAllView.as_view(),
        name='image_moderation_ban_all'),
    url(r'^moderate/forums/mark-as-spam/$',
        moderation_views.ForumModerationMarkAsSpamView.as_view(),
        name='forum_moderation_mark_as_spam'),

    ###########################################################################
    ### PAGES VIEWS                                                         ###
    ###########################################################################

    url(r'^help/api/$', api_help, name='api'),
    url(r'^trending-astrophotographers/',
        trending_astrophotographers,
        name='trending_astrophotographers'),
    url(r'^stats/', stats, name='stats'),

    ###########################################################################
    ### I18N VIEWS                                                          ###
    ###########################################################################

    url(r'^language/set/(?P<lang>[\w-]+)/$', set_language, name='set_language'),

    ###########################################################################
    ### IMAGE EDIT VIEWS                                                    ###
    ###########################################################################

    url(r'^delete/(?P<id>\w+)/$', image_views.ImageDeleteView.as_view(), name='image_delete'),
    url(r'^delete/original/(?P<id>\w+)/$', image_views.ImageDeleteOriginalView.as_view(), name='image_delete_original'),
    url(r'^delete/revision/(?P<id>\w+)/$', image_views.ImageRevisionDeleteView.as_view(), name='image_delete_revision'),
    url(r'^demote/(?P<id>\w+)/$', image_views.ImageDemoteView.as_view(), name='image_demote'),
    url(r'^edit/acquisition/(?P<id>\w+)/$', image_edit_acquisition, name='image_edit_acquisition'),
    url(r'^edit/acquisition/reset/(?P<id>\w+)/$', image_edit_acquisition_reset, name='image_edit_acquisition_reset'),
    url(r'^edit/basic/(?P<id>\w+)/$', image_views.ImageEditBasicView.as_view(), name='image_edit_basic'),
    url(r'^edit/gear/(?P<id>\w+)/$', image_views.ImageEditGearView.as_view(), name='image_edit_gear'),
    url(r'^edit/license/(?P<id>\w+)/$', image_edit_license, name='image_edit_license'),
    url(r'^edit/platesolving/(?P<id>\w+)/(?:(?P<revision_label>\w+)/)?$', image_edit_platesolving_settings,
        name='image_edit_platesolving_settings'),
    url(r'^edit/platesolving/(?P<id>\w+)/(?:(?P<revision_label>\w+)/)?restart$', image_restart_platesolving,
        name='image_restart_platesolving'),
    url(r'^edit/platesolving-advanced/(?P<id>\w+)/(?:(?P<revision_label>\w+)/)?$',
        image_edit_platesolving_advanced_settings, name='image_edit_platesolving_advanced_settings'),
    url(r'^edit/platesolving/(?P<id>\w+)/(?:(?P<revision_label>\w+)/)?restart-advanced$',
        image_restart_advanced_platesolving, name='image_restart_advanced_platesolving'),
    url(r'^edit/makefinal/(?P<id>\w+)/$', image_edit_make_final, name='image_edit_make_final'),
    url(r'^edit/revision/makefinal/(?P<id>\w+)/$', image_edit_revision_make_final,
        name='image_edit_revision_make_final'),
    url(r'^edit/save/acquisition/$', image_edit_save_acquisition, name='image_edit_save_acquisition'),
    url(r'^edit/save/license/$', image_edit_save_license, name='image_edit_save_license'),
    url(r'^edit/save/watermark/$', image_edit_save_watermark, name='image_edit_save_watermark'),
    url(r'^edit/watermark/(?P<id>\w+)/$', image_edit_watermark, name='image_edit_watermark'),
    url(r'^edit/thumbnails/(?P<id>\w+)/$', image_views.ImageEditThumbnailsView.as_view(), name='image_edit_thumbnails'),
    url(r'^edit/revision/(?P<id>\w+)/$', image_views.ImageEditRevisionView.as_view(), name='image_edit_revision'),
    url(r'^promote/(?P<id>\w+)/$', image_views.ImagePromoteView.as_view(), name='image_promote'),
    url(r'^upload/$', image_upload, name='image_upload'),
    url(r'^upload/process/$', image_upload_process, name='image_upload_process'),
    url(r'^upload/revision/process/$', image_revision_upload_process, name='image_revision_upload_process'),
    url(r'^upload-uncompressed-source/(?P<id>\w+)/$', image_views.ImageUploadUncompressedSource.as_view(),
        name='upload_uncompressed_source'),

    ###########################################################################
    ### IMAGE VIEWS                                                         ###
    ###########################################################################

    url(r'^full/(?P<id>\w+)/(?:(?P<r>\w+)/)?$', image_views.ImageFullView.as_view(), name='image_full'),
    url(r'^(?P<id>\w+)/flagthumbs/$', image_views.ImageFlagThumbsView.as_view(), name='image_flag_thumbs'),
    url(r'^(?P<id>\w+)/(?:(?P<r>\w+)/)?$', image_views.ImageDetailView.as_view(), name='image_detail'),
    url(r'^(?P<id>\w+)/(?:(?P<r>\w+)/)?rawthumb/(?P<alias>\w+)/(?:get.jpg)?$', image_views.ImageRawThumbView.as_view(),
        name='image_rawthumb'),
    url(r'^(?P<id>\w+)/(?:(?P<r>\w+)/)?thumb/(?P<alias>\w+)/$', image_views.ImageThumbView.as_view(),
        name='image_thumb'),

    ###########################################################################
    ### JSON API VIEWS                                                      ###
    ###########################################################################

    url(r'^json-api/', include('astrobin_apps_json_api.urls')),
]

urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]

if not settings.AWS_S3_ENABLED:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [url(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
        'show_indexes': True
    })]

if settings.LOCAL_STATIC_STORAGE:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [url(r'^static/(?P<path>.*)$', serve, {
        'document_root': settings.STATIC_ROOT,
        'show_indexes': True
    })]
