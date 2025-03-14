from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from common.views import (
    ContentTypeList, ContentTypeDetail, UserEmptyTrash, UserList, UserDetail, UserProfileChangeGalleryHeader,
    UserProfileFollowers, UserProfileFollowing, UserProfileList, UserProfileDetail,
    CurrentUserProfileDetail, SubscriptionList, SubscriptionDetail, UserProfileMutualFollowers,
    UserProfileRemoveShadowBanView, UserProfileShadowBanView, UserProfileStats,
    UserSubscriptionList, UserSubscriptionDetail,
    TogglePropertyList, TogglePropertyDetail, PaymentList, UserProfilePartialUpdate, 
    UserAvatarAdd, UserAvatarDelete,
)

urlpatterns = (
    url(r'^contenttypes/$', ContentTypeList.as_view(), name='contenttype-list'),
    url(r'^contenttypes/(?P<pk>\d+)/$', ContentTypeDetail.as_view(), name='contenttype-detail'),

    url(r'^users/$', UserList.as_view(), name='user-list'),
    url(r'^users/(?P<pk>\d+)/$', UserDetail.as_view(), name='user-detail'),
    url(r'^users/(?P<pk>\d+)/empty-trash/$', UserEmptyTrash.as_view(), name='user-empty-trash'),
    url(r'^users/avatar/add/$', UserAvatarAdd.as_view(), name='user-avatar-add'),
    url(r'^users/avatar/delete/$', UserAvatarDelete.as_view(), name='user-avatar-delete'),

    url(r'^toggleproperties/$', TogglePropertyList.as_view(), name='toggleproperty-list'),
    url(r'^toggleproperties/(?P<pk>\d+)/$', TogglePropertyDetail.as_view(), name='toggleproperty-detail'),

    # TODO: move these to AstroBin.
    url(r'^userprofiles/$', UserProfileList.as_view(), name='userprofile-list'),
    url(r'^userprofiles/(?P<pk>\d+)/$', UserProfileDetail.as_view(), name='userprofile-detail'),
    url(r'^userprofiles/(?P<pk>\d+)/stats/$', UserProfileStats.as_view(), name='userprofile-stats'),
    url(r'^userprofiles/(?P<pk>\d+)/followers/$', UserProfileFollowers.as_view(), name='userprofile-followers'),
    url(r'^userprofiles/(?P<pk>\d+)/following/$', UserProfileFollowing.as_view(), name='userprofile-following'),
    url(
        r'^userprofiles/(?P<pk>\d+)/mutual-followers/$',
        UserProfileMutualFollowers.as_view(),
        name='userprofile-mutual-followers'
    ),
    url(
        r'^userprofiles/(?P<pk>\d+)/change-gallery-header-image/(?P<image_id>\w+)/$',
        UserProfileChangeGalleryHeader.as_view(),
        name='userprofile-change-gallery-header'
    ),
    url(r'^userprofiles/current/$', CurrentUserProfileDetail.as_view(), name='userprofile-detail-current'),
    url(r'^userprofiles/(?P<pk>\d+)/partial/$', UserProfilePartialUpdate.as_view(), name='userprofile-partial-update'),
    url(
        r'^userprofiles/(?P<pk>\d+)/shadow-ban/$',
        UserProfileShadowBanView.as_view(),
        name='userprofile-shadow-ban'
    ),
    url(
        r'^userprofiles/(?P<pk>\d+)/remove-shadow-ban/$',
        UserProfileRemoveShadowBanView.as_view(),
        name='userprofile-remove-shadow-ban'
    ),
    url(r'^subscriptions/$', SubscriptionList.as_view(), name='subscription-list'),
    url(r'^subscriptions/(?P<pk>\d+)/$', SubscriptionDetail.as_view(), name='subscription-detail'),

    url(r'^usersubscriptions/$', UserSubscriptionList.as_view(), name='usersubscription-list'),
    url(r'^usersubscriptions/(?P<pk>\d+)/$', UserSubscriptionDetail.as_view(), name='usersubscription-detail'),

    url(r'^payments/$', PaymentList.as_view(), name='payment-list'),
)

# Format suffixes
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
