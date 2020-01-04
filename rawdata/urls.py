# Django
from django.conf.urls import url

# This app
import signal_handlers
from .views.atom import *
from .views.privatesharedfolders import *
from .views.publicdatapools import *
from .views.rawimage import *
from .views.temporaryarchive import *

signal_handlers.install()

urlpatterns = (
    url(r'^$', login_required(RawImageLibrary.as_view()), name='rawdata.library'),
    url(r'^(?P<pk>\d+)/$', login_required(RawImageDetailView.as_view()), name='rawdata.rawimage_detail'),
    url(r'^download/(?:(?P<ids>[\d+,?]+)/)?$', login_required(RawImageDownloadView.as_view()), name='rawdata.download'),
    url(r'^delete/(?:(?P<ids>[\d+,?]+)/)?$', login_required(RawImageDeleteView.as_view()), name='rawdata.delete'),
    url(r'^archive/(?P<pk>\d+)/$', login_required(TemporaryArchiveDetailView.as_view()),
        name='rawdata.temporary_archive_detail'),
    url(r'^restricted/$', TemplateView.as_view(template_name='rawdata/restricted.html'), name='rawdata.restricted'),

    url(r'^publicdatapools/$', PublicDataPoolListView.as_view(), name='rawdata.publicdatapool_list'),
    url(r'^publicdatapools/(?P<pk>\d+)/$', PublicDataPoolDetailView.as_view(), name='rawdata.publicdatapool_detail'),
    url(r'^publicdatapools/(?P<pk>\d+)/add-data/$', login_required(PublicDataPoolAddDataView.as_view()),
        name='rawdata.publicdatapool_add_data'),
    url(r'^publicdatapools/(?P<pk>\d+)/remove-data/(?P<rawimage_pk>\d+)/$',
        login_required(PublicDataPoolRemoveDataView.as_view()), name='rawdata.publicdatapool_remove_data'),
    url(r'^publicdatapools/(?P<pk>\d+)/add-image/$', login_required(PublicDataPoolAddImageView.as_view()),
        name='rawdata.publicdatapool_add_image'),
    url(r'^publicdatapools/(?P<pk>\d+)/download/$', login_required(PublicDataPoolDownloadView.as_view()),
        name='rawdata.publicdatapool_download'),
    url(r'^publicdatapools/share/(?:(?P<ids>[\d+,?]+)/)?$', login_required(PublicDataPoolCreateView.as_view()),
        name='rawdata.publicdatapool_create'),
    url(r'^publicdatapools/(?P<pk>\d+)/update/$', login_required(PublicDataPoolUpdateView.as_view()),
        name='rawdata.publicdatapool_update'),

    url(r'^privatesharedfolders/$', login_required(PrivateSharedFolderListView.as_view()),
        name='rawdata.privatesharedfolder_list'),
    url(r'^privatesharedfolders/(?P<pk>\d+)/$', login_required(PrivateSharedFolderDetailView.as_view()),
        name='rawdata.privatesharedfolder_detail'),
    url(r'^privatesharedfolders/(?P<pk>\d+)/add-data/$', login_required(PrivateSharedFolderAddDataView.as_view()),
        name='rawdata.privatesharedfolder_add_data'),
    url(r'^privatesharedfolders/(?P<pk>\d+)/remove-data/(?P<rawimage_pk>\d+)/$',
        login_required(PrivateSharedFolderRemoveDataView.as_view()), name='rawdata.privatesharedfolder_remove_data'),
    url(r'^privatesharedfolders/(?P<pk>\d+)/add-image/$', login_required(PrivateSharedFolderAddImageView.as_view()),
        name='rawdata.privatesharedfolder_add_image'),
    url(r'^privatesharedfolders/(?P<pk>\d+)/add-users/$', login_required(PrivateSharedFolderAddUsersView.as_view()),
        name='rawdata.privatesharedfolder_add_users'),
    url(r'^privatesharedfolders/(?P<pk>\d+)/remove-user/(?P<user_id>\d+)/$',
        login_required(PrivateSharedFolderRemoveUserView.as_view()), name='rawdata.privatesharedfolder_remove_user'),
    url(r'^privatesharedfolders/(?P<pk>\d+)/download/$', login_required(PrivateSharedFolderDownloadView.as_view()),
        name='rawdata.privatesharedfolder_download'),
    url(r'^privatesharedfolders/share/(?:(?P<ids>[\d+,?]+)/)?$',
        login_required(PrivateSharedFolderCreateView.as_view()), name='rawdata.privatesharedfolder_create'),
    url(r'^privatesharedfolders/(?P<pk>\d+)/delete/$', login_required(PrivateSharedFolderDeleteView.as_view()),
        name='rawdata.privatesharedfolder_delete'),
    url(r'^privatesharedfolders/(?P<pk>\d+)/update/$', login_required(PrivateSharedFolderUpdateView.as_view()),
        name='rawdata.privatesharedfolder_update'),

    url(r'^atom/activate/$', atom_activate, name="rawdata.atom_activate"),
    url(r'^atom/deactivate/$', atom_deactivate, name="rawdata.atom_deactivate"),
)
