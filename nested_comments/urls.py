# Django
from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

# This app
from .views import *


urlpatterns = patterns('',
    url(r'^create/(?P<content_type_id>\d+)/(?P<object_id>\d+)/$', login_required(NestedCommentCreateView.as_view()), name = 'nested_comments.create'),
)

