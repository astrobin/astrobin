from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

from bin import views

urlpatterns = patterns('',
    (r'^bin/$', views.index),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/(.*)', admin.site.root),
)
