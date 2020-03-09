from django.conf.urls import url
from toggleproperties.views import ajax_add_toggleproperty, ajax_remove_toggleproperty

urlpatterns = (
    url(r'^add$', ajax_add_toggleproperty, name="toggleproperty_ajax_add"),
    url(r'^remove$', ajax_remove_toggleproperty, name="toggleproperty_ajax_remove"),
)
