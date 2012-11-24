from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic import *

from .views import *

import signal_handlers
signal_handlers.install()

urlpatterns = patterns('',
    url(r'^upload/$', login_required(RawImageCreateView.as_view()), name = 'rawdata.upload'),
    url(r'^(?P<username>[\w.@+-]+)/$', login_required(RawImageLibrary.as_view()), name = 'rawdata.library'),
)
