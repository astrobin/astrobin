from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView
from django.views.static import serve
from tastypie.api import Api
from threaded_messages.views import (
    batch_update as messages_batch_update, delete as messages_delete, inbox as messages_inbox,
    message_ajax_reply as messages_message_ajax_reply, outbox as messages_outbox, trash as messages_trash,
    undelete as messages_undelete, view as messages_view,
)
from two_factor.urls import urlpatterns as tf_urls

from astrobin import lookups
from astrobin.api import (
    CollectionResource, ImageOfTheDayResource, ImageResource, ImageRevisionResource, LocationResource,
    TopPickNominationResource, TopPickResource, UserProfileResource,
)
from astrobin.api2.views.custom_auth_token_view import CustomAuthTokenView
from astrobin.forms.password_reset_form import PasswordResetForm
from astrobin.search import AstroBinSearchView
from astrobin.views import (
    activity_stream_fragment, api as api_views, api_help, astrophotographers_list, collections as collections_views,
    contributors_list,
    explore as explore_views, flickr_auth_callback, gear_by_ids, gear_by_image, gear_by_make, gear_popover_ajax,
    get_edit_gear_form, get_empty_edit_gear_form, get_gear_user_info_form, get_is_gear_complete, get_makes_by_type,
    image as image_views, image_edit_acquisition, image_edit_acquisition_reset, image_edit_license,
    image_edit_make_final, image_edit_platesolving_advanced_settings, image_edit_platesolving_settings,
    image_edit_revision_make_final, image_edit_save_acquisition, image_edit_save_license, image_edit_save_watermark,
    image_edit_watermark, image_restart_advanced_platesolving, image_restart_platesolving,
    image_revision_upload_process, image_upload, image_upload_process, index, latest_from_forums_fragment, me,
    moderation as moderation_views,
    password_change, password_change_request_token, recent_images_fragment, registration as registration_views,
    save_gear_details,
    save_gear_user_info,
    serve_file_from_cdn, set_language,
    suspended_account,
    user_ban, user_marketplace_fragment, user_page, user_page_api_keys, user_page_bookmarks, user_page_followers,
    user_page_following,
    user_page_friends, user_page_liked, user_page_plots, user_popover_ajax, user_profile_delete,
    user_profile_edit_basic, user_profile_edit_gear, user_profile_edit_license, user_profile_edit_locations,
    user_profile_edit_preferences, user_profile_edit_privacy, user_profile_flickr_import,
    user_profile_remove_shadow_ban, user_profile_save_basic, user_profile_save_gear, user_profile_save_license,
    user_profile_save_locations, user_profile_save_preferences, user_profile_save_privacy,
    user_profile_seen_iotd_tp_is_explicit_submission, user_profile_seen_realname, user_profile_shadow_ban,
)
from astrobin.views.auth.login import LoginView
from astrobin.views.auth.logout import LogoutView
from astrobin.views.contact import ContactRedirectView
from astrobin.views.forums import LatestTopicsView
from astrobin.views.profile.download_data_view import DownloadDataView
from astrobin.views.threaded_messages import messages_compose
from astrobin_apps_forum.views import RedirectTopicView

admin.autodiscover()

# These are the old API, not djangorestframework
v1_api = Api(api_name='v1')
v1_api.register(LocationResource())
v1_api.register(ImageResource())
v1_api.register(ImageRevisionResource())
v1_api.register(TopPickNominationResource())
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

    url(r'^admin/', admin.site.urls),

    ###########################################################################
    ### ACCOUNTS VIEWS                                                      ###
    ###########################################################################

    url(
       r'^accounts/password/change/request-token/$',
       password_change_request_token,
       name='password_change_request_token'
    ),
    url(
        r'^accounts/password/change/$',
        password_change,
        name='password_change'
    ),
    url(
        r'^accounts/password/change/done/$',
        auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done'
    ),
    url(
        r'^accounts/password/reset/$',
        auth_views.PasswordResetView.as_view(form_class=PasswordResetForm),
        name='password_reset'
    ),
    url(
        r'^accounts/password/reset/done/$',
        auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'
    ),
    url(
        r'^accounts/password/reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'
    ),
    url(
        r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    # and now add the registration urls
    url(
        r'^accounts/register/$',
        never_cache(registration_views.AstroBinRegistrationView.as_view()),
        name='registration_register'
    ),
    url(
        r'^accounts/resend-activation/$',
        registration_views.resend_activation_email,
        name='resend_activation_email'
    ),
    url(r'^accounts/email/', include('change_email.urls')),
    url(
        r'^accounts/login/$',
        RedirectView.as_view(url='/account/login/', query_string=True, permanent=True),
        name='auth_login'
    ),
    url(
        r'^accounts/logout/$',
        LogoutView.as_view(
            template_name='registration/logout.html'
        ),
        name='auth_logout'
    ),
    # We override the activation URL to handle 'next' parameter
    url(
        r'^accounts/activate/(?P<activation_key>[-:\w]+)/$',
        registration_views.AstroBinActivationView.as_view(),
        name='registration_activate',
    ),
    # Include the rest of the registration URLs
    url(r'^accounts/', include('registration.backends.hmac.urls')),

    ###########################################################################
    ### TWO_FACTOR                                                          ###
    ###########################################################################

    url(
        r'^account/login/$',
        LoginView.as_view(),
        name='two_factor:login'
    ),
    url('', include(tf_urls)),

    ###########################################################################
    ### THIRD PARTY APPS VIEWS                                              ###
    ###########################################################################

    url(r'^activity/', include('actstream.urls')),
    url(r'^avatar/', include('avatar.urls')),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^contact/', ContactRedirectView.as_view(), name='contact'),
    # Override pybb's LatestTopicsView to omit topics from groups the user has not joined.
    url(r'^forum/topic/latest/$', LatestTopicsView.as_view(), name='topic_latest'),
    # Override pybb's topic views to redirect if the topic was moved
    url(
        r'^forum/c/(?P<category_slug>[\w-]+)/(?P<forum_slug>[\w-]+)/(?P<slug>[\w-]+)/$',
        RedirectTopicView.as_view(), name='redirect_topic'
    ),
    url(r'^forum/', include('pybb.urls', namespace='pybb')),
    url(r'hitcount/', include('hitcount.urls', namespace='hitcount')),
    url(r'^persistent_messages/', include('persistent_messages.urls')),
    url(r'^subscriptions/paypal/', include('paypal.standard.ipn.urls')),
    url(r'^subscriptions/', RedirectView.as_view(url="https://app.astrobin.com/subscriptions/options", permanent=True)),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^bouncy/', include('django_bouncy.urls')),
    url(r'^paypal/', include('paypal.standard.ipn.urls')),
    url(r'^cookies/', include('cookie_consent.urls')),

    ###########################################################################
    ### API VIEWS                                                           ###
    ###########################################################################

    url(r'^api/', include(v1_api.urls)),
    url(r'^api/request-key/$', never_cache(api_views.AppApiKeyRequestView.as_view()), name='app_api_key_request'),
    url(
        r'^api/request-key/complete/$', never_cache(api_views.AppApiKeyRequestCompleteView.as_view()),
        name='app_api_key_request_complete'
    ),

    url(r'^api/v2/api-auth-token/', CustomAuthTokenView.as_view()),
    url(r'^api/v2/api-auth/', include(('rest_framework.urls', 'rest_framework'))),
    url(r'^api/v2/common/', include('common.api_urls')),
    url(r'^api/v2/astrobin/', include('astrobin.api2.urls')),
    url(r'^api/v2/nestedcomments/', include(('nested_comments.api_urls', 'nested_comments'))),
    url(r'^api/v2/platesolving/', include('astrobin_apps_platesolving.api_urls')),
    url(r'^api/v2/notifications/', include('astrobin_apps_notifications.api.urls')),
    url(r'^api/v2/images/', include(('astrobin_apps_images.api.urls', 'astrobin_apps_images'))),
    url(r'^api/v2/payments/', include(('astrobin_apps_payments.api.urls', 'astrobin_apps_payments'))),
    url(r'^api/v2/iotd/', include(('astrobin_apps_iotd.api.urls', 'astrobin_apps_iotd'))),
    url(
        r'^api/v2/remote-source-affiliation/', include(
            ('astrobin_apps_remote_source_affiliation.api.urls', 'astrobin_apps_remote_source_affiliation')
        )
    ),
    url(r'^api/v2/groups/', include(('astrobin_apps_groups.api.urls', 'astrobin_apps_groups'))),
    url(r'^api/v2/users/', include(('astrobin_apps_users.api.urls', 'astrobin_apps_users'))),
    url(r'^api/v2/equipment/', include(('astrobin_apps_equipment.api.urls', 'astrobin_apps_equipment'))),
    url(r'^api/v2/forum/', include(('astrobin_apps_forum.api.urls', 'astrobin_apps_forum'))),

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
    url(r'^payments/', include('astrobin_apps_payments.urls')),
    url(r'^equipment/', include('astrobin_apps_equipment.urls', namespace='equipment')),

    ###########################################################################
    ### HOME VIEWS                                                          ###
    ###########################################################################

    url(r'^$', index, name='index'),
    url(r'^latest-from-forums-fragment/$', latest_from_forums_fragment, name='latest_from_forums_fragment'),
    url(r'^activity-steam-fragment/(?P<section>\w+)/$', activity_stream_fragment, name='activity_stream_fragment'),
    url(r'^recent-images-fragment/(?P<section>\w+)/$', recent_images_fragment, name='recent_images_fragment'),

    ###########################################################################
    ### SPECIAL VIEWS                                                       ###
    ###########################################################################

    url(
        r'^favicon.ico$',
        RedirectView.as_view(url=staticfiles_storage.url('astrobin/favicon.ico'), permanent=False),
        name='favicon'
    ),
    url(r'^robots\.txt', include('robots.urls')),
    url(
        r'^.well-known/apple-developer-merchantid-domain-association$',
        serve_file_from_cdn('downloads/apple-developer-merchantid-domain-association')
    ),

    ###########################################################################
    ### SEARCH VIEWS                                                        ###
    ###########################################################################

    url(r'^search/', never_cache(AstroBinSearchView.as_view()), name='haystack_search'),

    ###########################################################################
    ### EXPLORE VIEWS                                                       ###
    ###########################################################################

    url(r'^explore/top-picks/$', explore_views.TopPicksView.as_view(), name='top_picks'),
    url(
        r'^explore/top-pick-nominations/$', explore_views.TopPickNominationsView.as_view(),
        name='top_pick_nominations'
    ),

    ###########################################################################
    ### USER VIEWS                                                          ###
    ###########################################################################

    url(r'^me/$', me, name='me'),
    url(r'^suspended-account/$', suspended_account, name='suspended_account'),
    url(r'^users/(?P<username>[\w.@+-]*)/$', user_page, name='user_page'),
    url(
        r'^users/(?P<username>[\w.@+-]*)/collections/$', collections_views.UserCollectionsList.as_view(),
        name='user_collections_list'
    ),
    url(
        r'^users/(?P<username>[\w.@+-]*)/collections/no-collection/$',
        collections_views.UserCollectionsNoCollection.as_view(),
        name='user_collections_no_collection'
    ),
    url(
        r'^users/(?P<username>[\w.@+-]*)/collections/create/$', collections_views.UserCollectionsCreate.as_view(),
        name='user_collections_create'
    ),
    url(
        r'^users/(?P<username>[\w.@+-]*)/collections/(?P<collection_pk>\d+)/$',
        never_cache(collections_views.UserCollectionsDetail.as_view()), name='user_collections_detail'
    ),
    url(
        r'^users/(?P<username>[\w.@+-]*)/collections/(?P<collection_pk>\d+)/update/$',
        never_cache(collections_views.UserCollectionsUpdate.as_view()), name='user_collections_update'
    ),
    url(
        r'^users/(?P<username>[\w.@+-]*)/collections/(?P<collection_pk>\d+)/add-remove-images/$',
        never_cache(collections_views.UserCollectionsAddRemoveImages.as_view()),
        name='user_collections_add_remove_images'
    ),
    url(
        r'^users/(?P<username>[\w.@+-]*)/collections/(?P<collection_pk>\d+)/quick-edit/key-value-pairs$',
        never_cache(collections_views.UserCollectionsQuickEditKeyValueTags.as_view()),
        name='user_collections_quick_edit_key_value_tags'
    ),
    url(
        r'^users/(?P<username>[\w.@+-]*)/collections/(?P<collection_pk>\d+)/delete/$',
        never_cache(collections_views.UserCollectionsDelete.as_view()), name='user_collections_delete'
    ),
    url(r'^users/(?P<username>[\w.@+-]*)/apikeys/$', user_page_api_keys, name='user_page_api_keys'),
    url(r'^users/(?P<username>[\w.@+-]*)/ban/$', user_ban, name='user_ban'),
    url(r'^users/(?P<username>[\w.@+-]*)/bookmarks/$', user_page_bookmarks, name='user_page_bookmarks'),
    url(r'^users/(?P<username>[\w.@+-]*)/liked/$', user_page_liked, name='user_page_liked'),
    url(r'^users/(?P<username>[\w.@+-]*)/followers/$', user_page_followers, name='user_page_followers'),
    url(r'^users/(?P<username>[\w.@+-]*)/following/$', user_page_following, name='user_page_following'),
    url(r'^users/(?P<username>[\w.@+-]*)/friends/$', user_page_friends, name='user_page_friends'),
    url(r'^users/(?P<username>[\w.@+-]*)/plots/$', user_page_plots, name='user_page_plots'),
    url(
        r'^users/(?P<username>[\w.@+-]*)/marketplace-fragment/$',
        user_marketplace_fragment,
        name='user_marketplace_fragment'
    ),

    ###########################################################################
    ### PROFILE VIEWS                                                       ###
    ###########################################################################

    url(r'^flickr_auth_callback/$', flickr_auth_callback, name='flickr_auth_callback'),
    url(r'^profile/delete/$', user_profile_delete, name='profile_delete'),
    url(r'^profile/edit/$', user_profile_edit_basic, name='profile_edit_basic'),
    url(r'^profile/edit/basic/$', user_profile_edit_basic, name='profile_edit_basic'),
    url(r'^profile/edit/flickr/$', user_profile_flickr_import, name='profile_flickr_import'),
    url(r'^profile/edit/gear/$', user_profile_edit_gear, name='profile_edit_gear'),
    url(r'^profile/edit/license/$', user_profile_edit_license, name='profile_edit_license'),
    url(r'^profile/edit/locations/$', user_profile_edit_locations, name='profile_edit_locations'),
    url(r'^profile/edit/preferences/$', user_profile_edit_preferences, name='profile_edit_preferences'),
    url(r'^profile/edit/privacy/$', user_profile_edit_privacy, name='profile_edit_privacy'),
    url(r'^profile/download-data/$', never_cache(DownloadDataView.as_view()), name='profile_download_data'),
    url(r'^profile/save/basic/$', user_profile_save_basic, name='profile_save_basic'),
    url(r'^profile/save/gear/$', user_profile_save_gear, name='profile_save_gear'),
    url(r'^profile/save/license/$', user_profile_save_license, name='profile_save_license'),
    url(r'^profile/save/locations/$', user_profile_save_locations, name='profile_save_locations'),
    url(r'^profile/save/preferences/$', user_profile_save_preferences, name='profile_save_preferences'),
    url(r'^profile/save/privacy/$', user_profile_save_privacy, name='profile_save_privacy'),
    url(r'^profile/seen/realname/$', user_profile_seen_realname, name='profile_seen_realname'),
    url(
        r'^profile/seen/iotd-tp-is-explicit-submission/$', user_profile_seen_iotd_tp_is_explicit_submission,
        name='profile_seen_iotd_tp_is_explicit_submission'
    ),
    url(r'^profile/shadow-ban/', user_profile_shadow_ban, name='profile_shadow_ban'),
    url(r'^profile/remove-shadow-ban/', user_profile_remove_shadow_ban, name='profile_remove_shadow_ban'),

    ###########################################################################
    ### AUTOCOMPLETE VIEWS                                                 ###
    ###########################################################################

    url(
        r'^autocomplete-private-message-recipients/$', lookups.autocomplete_private_message_recipients,
        name='autocomplete_private_message_recipients'
    ),
    url(r'^autocomplete_usernames/$', lookups.autocomplete_usernames, name='autocomplete_usernames'),
    url(r'^autocomplete_images/$', lookups.autocomplete_images, name='autocomplete_images'),

    ###########################################################################
    ### GEAR VIEWS                                                          ###
    ###########################################################################

    url(r'^gear/by-ids/(?P<ids>([0-9]+,?)+)/$', gear_by_ids, name='gear_by_ids'),
    url(r'^gear/by-image/(?P<image_id>\d+)/$', gear_by_image, name='gear_by_image'),
    url(r'^gear/by-make/(?P<make>[(\w|\W).+-]*)/$', gear_by_make, name='gear_by_make'),
    url(r'^gear_popover_ajax/(?P<id>\d+)/(?P<image_id>\d+)/$', gear_popover_ajax, name='gear_popover_ajax'),
    url(r'^get-makes-by-type/(?P<klass>\w+)/$', get_makes_by_type, name='get_makes_by_type'),
    url(r'^get_edit_gear_form/(?P<id>\d+)/$', get_edit_gear_form, name='get_edit_gear_form'),
    url(r'^get_empty_edit_gear_form/(?P<gear_type>\w+)/$', get_empty_edit_gear_form, name='get_empty_edit_gear_form'),
    url(r'^get_gear_user_info_form/(?P<id>\d+)/$', get_gear_user_info_form, name='get_gear_user_info_form'),
    url(r'^get_is_gear_complete/(?P<id>\d+)/$', get_is_gear_complete, name='get_is_gear_complete'),
    url(r'^save_gear_details/$', save_gear_details, name='save_gear_details'),
    url(r'^save_gear_user_info/$', save_gear_user_info, name='save_gear_user_info'),
    url(r'^user_popover_ajax/(?P<username>[\w.@+-]+)/$', user_popover_ajax, name='user_popover_ajax'),

    ###########################################################################
    ### MESSAGES VIEWS                                                      ###
    ###########################################################################

    url(r'^messages/batch-update/$', messages_batch_update, name='messages_batch_update'),
    url(r'^messages/compose/$', messages_compose, {'template_name': 'messages/compose.html'}, name='messages_compose'),
    url(
        r'^messages/compose/(?P<recipient>[\w.@+-]+)/$', messages_compose, {'template_name': 'messages/compose.html'},
        name='messages_compose_to'
    ),
    url(r'^messages/delete/(?P<thread_id>[\d]+)/$', messages_delete, name='messages_delete'),
    url(r'^messages/undelete/(?P<thread_id>[\d]+)/$', messages_undelete, name='messages_undelete'),
    url(r'^messages/inbox/$', messages_inbox, {'template_name': 'messages/inbox.html'}, name='messages_inbox'),
    url(r'^messages/outbox/$', messages_outbox, {'template_name': 'messages/outbox.html'}, name='messages_outbox'),
    url(r'^messages/trash/$', messages_trash, {'template_name': 'messages/trash.html'}, name='messages_trash'),
    url(
        r'^messages/message-reply/(?P<thread_id>[\d]+)/$', messages_message_ajax_reply,
        {'template_name': 'messages/message_list_view.html'}, name="message_reply"
    ),
    url(
        r'^messages/view/(?P<thread_id>[\d]+)/$', messages_view, {'template_name': 'messages/view.html'},
        name='messages_detail'
    ),

    ###########################################################################
    ### MODERATION VIEWS                                                    ###
    ###########################################################################

    url(
        r'^moderate/images/$', never_cache(moderation_views.ImageModerationListView.as_view()),
        name='image_moderation'
    ),
    url(
        r'^moderate/images/spam/$',
        never_cache(moderation_views.ImageModerationSpamListView.as_view()),
        name='image_moderation_view_spam'
    ),
    url(
        r'^moderate/images/mark-as-spam/$',
        never_cache(moderation_views.ImageModerationMarkAsSpamView.as_view()),
        name='image_moderation_mark_as_spam'
    ),
    url(
        r'^moderate/images/mark-as-ham/$',
        never_cache(moderation_views.ImageModerationMarkAsHamView.as_view()),
        name='image_moderation_mark_as_ham'
    ),
    url(
        r'^moderate/images/ban-all/$',
        never_cache(moderation_views.ImageModerationBanAllView.as_view()),
        name='image_moderation_ban_all'
    ),
    url(
        r'^moderate/forums/mark-as-spam/$',
        never_cache(moderation_views.ForumModerationMarkAsSpamView.as_view()),
        name='forum_moderation_mark_as_spam'
    ),

    ###########################################################################
    ### PAGES VIEWS                                                         ###
    ###########################################################################

    url(r'^help/api/$', api_help, name='api'),
    url(
        r'^astrophotographers-list/',
        astrophotographers_list,
        name='astrophotographers_list'
    ),
    url(
        r'^contributors-list/',
        contributors_list,
        name='contributors_list'
    ),

    ###########################################################################
    ### I18N VIEWS                                                          ###
    ###########################################################################

    url(r'^language/set/(?P<language_code>[\w-]+)/$', set_language, name='set_language'),

    ###########################################################################
    ### IMAGE EDIT VIEWS                                                    ###
    ###########################################################################

    url(r'^delete/(?P<id>\w+)/$', never_cache(image_views.ImageDeleteView.as_view()), name='image_delete'),
    url(
        r'^delete/original/(?P<id>\w+)/$',
        never_cache(image_views.ImageDeleteOriginalView.as_view()), name='image_delete_original'
    ),
    url(
        r'^delete/revision/(?P<id>\w+)/$',
        never_cache(image_views.ImageRevisionDeleteView.as_view()), name='image_delete_revision'
    ),
    url(
        r'^delete/other-versions/(?P<id>\w+)/$', never_cache(image_views.ImageDeleteOtherVersionsView.as_view()),
        name='image_delete_other_versions'
    ),
    url(r'^demote/(?P<id>\w+)/$', never_cache(image_views.ImageDemoteView.as_view()), name='image_demote'),
    url(r'^edit/acquisition/(?P<id>\w+)/$', image_edit_acquisition, name='image_edit_acquisition'),
    url(r'^edit/acquisition/reset/(?P<id>\w+)/$', image_edit_acquisition_reset, name='image_edit_acquisition_reset'),
    url(r'^edit/basic/(?P<id>\w+)/$', never_cache(image_views.ImageEditBasicView.as_view()), name='image_edit_basic'),
    url(r'^edit/gear/(?P<id>\w+)/$', never_cache(image_views.ImageEditGearView.as_view()), name='image_edit_gear'),
    url(r'^edit/license/(?P<id>\w+)/$', image_edit_license, name='image_edit_license'),
    url(
        r'^edit/platesolving/(?P<image_id>\w+)/(?:(?P<revision_label>\w+)/)?$', image_edit_platesolving_settings,
        name='image_edit_platesolving_settings'
    ),
    url(
        r'^edit/platesolving/(?P<id>\w+)/(?:(?P<revision_label>\w+)/)?restart$', image_restart_platesolving,
        name='image_restart_platesolving'
    ),
    url(
        r'^edit/platesolving-advanced/(?P<image_id>\w+)/(?:(?P<revision_label>\w+)/)?$',
        image_edit_platesolving_advanced_settings, name='image_edit_platesolving_advanced_settings'
    ),
    url(
        r'^edit/platesolving/(?P<id>\w+)/(?:(?P<revision_label>\w+)/)?restart-advanced$',
        image_restart_advanced_platesolving, name='image_restart_advanced_platesolving'
    ),
    url(r'^edit/makefinal/(?P<image_id>\w+)/$', image_edit_make_final, name='image_edit_make_final'),
    url(
        r'^edit/revision/makefinal/(?P<revision_id>\w+)/$', image_edit_revision_make_final,
        name='image_edit_revision_make_final'
    ),
    url(r'^edit/save/acquisition/$', image_edit_save_acquisition, name='image_edit_save_acquisition'),
    url(r'^edit/save/license/$', image_edit_save_license, name='image_edit_save_license'),
    url(r'^edit/save/watermark/$', image_edit_save_watermark, name='image_edit_save_watermark'),
    url(r'^edit/watermark/(?P<id>\w+)/$', image_edit_watermark, name='image_edit_watermark'),
    url(
        r'^edit/thumbnails/(?P<id>\w+)/$',
        never_cache(image_views.ImageEditThumbnailsView.as_view()), name='image_edit_thumbnails'
    ),
    # DEPRECATED
    url(
        r'^edit/revision/(?P<id>\w+)/$',
        never_cache(image_views.ImageEditRevisionView.as_view()), name='image_edit_revision'
    ),
    url(r'^promote/(?P<id>\w+)/$', never_cache(image_views.ImagePromoteView.as_view()), name='image_promote'),
    url(
        r'^download/(?P<id>\w+)/(?P<revision_label>\w+)/(?P<version>\w+)/$',
        never_cache(image_views.ImageDownloadView.as_view()), name='image_download'
    ),
    url(r'^upload/$', image_upload, name='image_upload'),
    url(r'^upload/process/$', image_upload_process, name='image_upload_process'),
    url(r'^upload/revision/process/$', image_revision_upload_process, name='image_revision_upload_process'),
    url(
        r'^upload-uncompressed-source/(?P<id>\w+)/$', never_cache(image_views.ImageUploadUncompressedSource.as_view()),
        name='upload_uncompressed_source'
    ),

    ###########################################################################
    ### IMAGE VIEWS                                                         ###
    ###########################################################################

    url(r'^full/(?P<id>\w+)/(?:(?P<r>\w+)/)?$', image_views.ImageFullView.as_view(), name='image_full'),
    url(r'^(?P<id>\w+)/flagthumbs/$', never_cache(image_views.ImageFlagThumbsView.as_view()), name='image_flag_thumbs'),
    url(
        r'^(?P<id>\w+)/remove-as-collaborator/$',
        never_cache(image_views.ImageRemoveAsCollaboratorView.as_view()),
        name='image_remove_as_collaborator'
    ),
    url(
        r'^(?P<id>\w+)/submit-to-iotd-tp/$', never_cache(image_views.ImageSubmitToIotdTpProcessView.as_view()),
        name='image_submit_to_iotd_tp'
    ),
    url(
        r'^(?P<id>\w+)/(?:(?P<r>\w+)/)?equipment-fragment/$',
        image_views.ImageEquipmentFragment.as_view(),
        name='image_equipment_fragment',
    ),
    url(
        r'^(?P<id>\w+)/(?:(?P<r>\w+)/)?acquisition-fragment/$',
        image_views.ImageAcquisitionFragment.as_view(),
        name='image_acquisition_fragment',
    ),
    url(
        r'^(?P<id>\w+)/(?:(?P<r>\w+)/)?marketplace-fragment/$',
        image_views.ImageMarketplaceFragment.as_view(),
        name='image_marketplace_fragment',
    ),
    url(r'^(?P<id>\w+)/(?:(?P<r>\w+)/)?$', image_views.ImageDetailView.as_view(), name='image_detail'),
    url(
        r'^(?P<id>\w+)/(?:(?P<r>\w+)/)?rawthumb/(?P<alias>\w+)/(?:get.jpg)?$', image_views.ImageRawThumbView.as_view(),
        name='image_rawthumb'
    ),
    url(
        r'^(?P<id>\w+)/(?:(?P<r>\w+)/)?thumb/(?P<alias>\w+)/$', image_views.ImageThumbView.as_view(),
        name='image_thumb'
    ),
    url(
        r'^(?P<id>\w+)/collaborator-request-accept/$', image_views.ImageCollaboratorRequestAccept.as_view(),
        name='image_collaborator_request_accept'
    ),
    url(
        r'^(?P<id>\w+)/collaborator-request-deny/$', image_views.ImageCollaboratorRequestDeny.as_view(),
        name='image_collaborator_request_deny'
    ),

    ###########################################################################
    ### JSON API VIEWS                                                      ###
    ###########################################################################

    url(r'^json-api/', include('astrobin_apps_json_api.urls')),
]

if not settings.AWS_S3_ENABLED:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        url(
            r'^media/(?P<path>.*)$', serve, {
                'document_root': settings.MEDIA_ROOT,
                'show_indexes': True
            }
        )
    ]

if settings.LOCAL_STATIC_STORAGE:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [
        url(
            r'^static/(?P<path>.*)$', serve, {
                'document_root': settings.STATIC_ROOT,
                'show_indexes': True
            }
        ),
        url(
            r'^media/static/(?P<path>.*)$', serve, {
                'document_root': settings.STATIC_ROOT,
                'show_indexes': True
            }
        )
    ]
