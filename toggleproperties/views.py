from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from astrobin_apps_images.services import ImageService
from .models import ToggleProperty

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

        if hasattr(obj, 'deleted') and obj.deleted is not None and obj.deleted is not False:
            return HttpResponse(_('Sorry, this object was already deleted.'), status=404)

        if content_type.model == 'user' and obj.userprofile.shadow_bans.filter(pk=request.user.userprofile.pk).exists():
            return HttpResponse(_('Sorry, you cannot follow this user.'), status=403)

        response_dict = {}

        if ToggleProperty.objects.filter(
                content_type=content_type,
                object_id=object_id,
                property_type=property_type,
                user=request.user
        ):
            return HttpResponse(
                f'User {request.user.username} already toggled the property {property_type} for object '
                f'{object_id}/{content_type.pk}.',
                status=409
            )

        if content_type.model == 'imagerevision':
            obj = obj.image

        if property_type == 'like' and (content_type.model == 'image' and request.user == obj.user):
            return HttpResponse(
                'Sorry, but you cannot like your own image.',
                status=400
            )

        try:
            ToggleProperty.objects.create_toggleproperty(property_type, obj, request.user)
        except ValueError as e:
            return HttpResponse(str(e), status=400)

        if content_type.model == 'image':
            ImageService(obj).record_hit(request)

        if settings.TOGGLEPROPERTIES.get('show_count'):
            count = ToggleProperty.objects.toggleproperties_for_object(property_type, obj).count()
            response_dict['count'] = count

        return HttpResponse(
            simplejson.dumps(response_dict),
            'application/javascript',
            status=200
        )
    else:
        return HttpResponse(status=405)


@login_required
def ajax_remove_toggleproperty(request):
    if request.method == "POST":
        object_id = request.POST.get("object_id")
        content_type = get_object_or_404(
            ContentType,
            pk=request.POST.get("content_type_id")
        )
        property_type = request.POST.get("property_type")
        response_dict = {}

        tp = get_object_or_404(
            ToggleProperty, object_id=object_id,
            content_type=content_type,
            property_type=property_type,
            user=request.user
        )
        tp.delete()
        obj = content_type.get_object_for_this_type(pk=object_id)
        if settings.TOGGLEPROPERTIES.get('show_count'):
            count = ToggleProperty.objects.toggleproperties_for_object(property_type, obj).count()
            response_dict['count'] = count

        return HttpResponse(
            simplejson.dumps(response_dict),
            'application/javascript',
            status=200
        )
    else:
        return HttpResponse(status=405)
