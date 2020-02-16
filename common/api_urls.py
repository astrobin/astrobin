from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from common.views import ContentTypeList, ContentTypeDetail, UserList, UserDetail, UserProfileList, UserProfileDetail, \
    CurrentUserProfileDetail, SubscriptionList, SubscriptionDetail, UserSubscriptionList, UserSubscriptionDetail

urlpatterns = (
    url(r'^contenttypes/$', ContentTypeList.as_view(), name='contenttype-list'),
    url(r'^contenttypes/(?P<pk>\d+)/$', ContentTypeDetail.as_view(), name='contenttype-detail'),

    url(r'^users/$', UserList.as_view(), name='user-list'),
    url(r'^users/(?P<pk>\d+)/$', UserDetail.as_view(), name='user-detail'),

    # TODO: move these to AstroBin.
    url(r'^userprofiles/$', UserProfileList.as_view(), name='userprofile-list'),
    url(r'^userprofiles/(?P<pk>\d+)/$', UserProfileDetail.as_view(), name='userprofile-detail'),
    url(r'^userprofiles/current/$', CurrentUserProfileDetail.as_view(), name='userprofile-detail-current'),

    url(r'^subscriptions/$', SubscriptionList.as_view(), name='subscription-list'),
    url(r'^subscriptions/(?P<pk>\d+)/$', SubscriptionDetail.as_view(), name='subscription-detail'),

    url(r'^usersubscriptions/$', UserSubscriptionList.as_view(), name='usersubscription-list'),
    url(r'^usersubscriptions/(?P<pk>\d+)/$', UserSubscriptionDetail.as_view(), name='usersubscription-detail'),
)

# Format suffixes
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
