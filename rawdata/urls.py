# Django
from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic import *

# This app
import signal_handlers
from .views import *

signal_handlers.install()

urlpatterns = patterns('',
    url(r'^$', login_required(RawImageLibrary.as_view()), name = 'rawdata.library'),
    url(r'^upload/$', login_required(RawImageCreateView.as_view()), name = 'rawdata.upload'),
    url(r'^download/(?:(?P<ids>[\d+,?]+)/)?$', login_required(RawImageDownloadView.as_view()), name = 'rawdata.download'),
    url(r'^delete/(?:(?P<ids>[\d+,?]+)/)?$', login_required(RawImageDeleteView.as_view()), name = 'rawdata.delete'),
    url(r'^archive/(?P<pk>\d+)/$', login_required(TemporaryArchiveDetailView.as_view()), name = 'rawdata.temporary_archive_detail'),

    url(r'^publicdatapools/(?P<pk>\d+)/$', PublicDataPoolDetailView.as_view(), name = 'rawdata.publicdatapool_detail'),
    url(r'^publicdatapools/(?P<pk>\d+)/add-data/$', login_required(PublicDataPoolAddDataView.as_view()), name = 'rawdata.publicdatapool_add_data'),
    url(r'^publicdatapools/(?P<pk>\d+)/download/$', login_required(PublicDataPoolDownloadView.as_view()), name = 'rawdata.publicdatapool_download'),
    url(r'^publicdatapools/share/(?:(?P<ids>[\d+,?]+)/)?$', login_required(PublicDataPoolCreateView.as_view()), name = 'rawdata.public_data_pool_create'),
)
