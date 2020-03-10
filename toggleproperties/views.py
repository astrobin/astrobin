from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from models import ToggleProperty

try:
    from django.utils import simplejson
except ImportError:
    import simplejson


@login_required
def ajax_add_toggleproperty(request):
    if request.method == "POST":
        object_id = request.POST.get("object_id")
        content_type = get_object_or_404(ContentType, pk=request.POST.get("content_type_id"))
        property_type = request.POST.get("property_type")
        obj = content_type.get_object_for_this_type(pk=object_id)
        response_dict = {}

        # check if it was created already
        if ToggleProperty.objects.filter(content_type=content_type, object_id=object_id, \
                                         property_type=property_type, user=request.user):
            # return conflict response code if already satisfied
            return HttpResponse(status=409)

        # if not create it
        tp = ToggleProperty.objects.create_toggleproperty(property_type, obj, request.user)
        if settings.TOGGLEPROPERTIES.get('show_count'):
            count = ToggleProperty.objects.toggleproperties_for_object(property_type, obj).count()
            response_dict['count'] = count

        return HttpResponse(simplejson.dumps(response_dict),
                            'application/javascript',
                            status=200)
    else:
        return HttpResponse(status=405)


@login_required
def ajax_remove_toggleproperty(request):
    if request.method == "POST":
        object_id = request.POST.get("object_id")
        content_type = get_object_or_404(ContentType,
                                         pk=request.POST.get("content_type_id"))
        property_type = request.POST.get("property_type")
        response_dict = {}

        tp = get_object_or_404(ToggleProperty, object_id=object_id,
                               content_type=content_type,
                               property_type=property_type,
                               user=request.user)
        tp.delete()
        obj = content_type.get_object_for_this_type(pk=object_id)
        if settings.TOGGLEPROPERTIES.get('show_count'):
            count = ToggleProperty.objects.toggleproperties_for_object(property_type, obj).count()
            response_dict['count'] = count

        return HttpResponse(simplejson.dumps(response_dict),
                            'application/javascript',
                            status=200)
    else:
        return HttpResponse(status=405)
