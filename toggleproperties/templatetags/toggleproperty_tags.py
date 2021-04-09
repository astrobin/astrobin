from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from toggleproperties.models import ToggleProperty

register = template.Library()


@register.filter
def is_toggled(property_type, target, user):
    if not user or not user.is_authenticated():
        return False
    return ToggleProperty.objects.toggleproperties_for_object(property_type, target, user).count() > 0


@register.simple_tag
def toggleproperties_for_object(property_type, target):
    return ToggleProperty.objects.toggleproperties_for_object(property_type, target).count()


@register.inclusion_tag("toggleproperties/toggleproperty_add_remove.html", takes_context=True)
def add_remove_toggleproperty(context, property_type, target, user, can_add=True, can_remove=True):
    toggle_property = None
    content_type = ContentType.objects.get_for_model(target)

    if user and user.is_authenticated():
        toggle_property = ToggleProperty.objects.toggleproperties_for_object(property_type, target, user=user)
        if toggle_property.exists():
            toggle_property = toggle_property[0]
        else:
            toggle_property = None

    count = ToggleProperty.objects.toggleproperties_for_object(property_type, target).count()

    settings_dict = settings.TOGGLEPROPERTIES[property_type]

    return {"object_id": target.pk,
            "content_type_id": content_type.pk,
            "property_type": property_type,
            "is_toggled": toggle_property is not None,
            "disabled": (toggle_property is None and not can_add) or (toggle_property is not None and not can_remove),
            "count": count,

            "property_tooltip_on": settings_dict.get('property_tooltip_on'),
            "property_tooltip_off": settings_dict.get('property_tooltip_off'),

            "property_label_on": settings_dict.get('property_label_on'),
            "property_label_off": settings_dict.get('property_label_off'),

            "property_icon": settings_dict.get('property_icon'),

            "request": context['request']}
