from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from toggleproperties.models import ToggleProperty

register = template.Library()


@register.filter
def is_toggled(property_type, object, user):
    if not user or not user.is_authenticated():
        return False
    return ToggleProperty.objects.toggleproperties_for_object(propery_name, object, user).count() > 0


@register.inclusion_tag("toggleproperties/toggleproperty_add_remove.html", takes_context=True)
def add_remove_toggleproperty(context, property_type, object, user):
    tp = None
    content_type = ContentType.objects.get_for_model(object)
    if user and user.is_authenticated():
        tp = ToggleProperty.objects.toggleproperties_for_object(property_type, object, user=user)
        if tp:
            tp = tp[0]
        else:
            tp = None
    count = ToggleProperty.objects.toggleproperties_for_object(property_type, object).count()

    settings_dict = settings.TOGGLEPROPERTIES[property_type]

    return {"object_id": object.pk,
            "content_type_id": content_type.pk,
            "property_type": property_type,
            "is_toggled": tp,
            "count": count,

            "property_tooltip_on": settings_dict.get('property_tooltip_on'),
            "property_tooltip_off": settings_dict.get('property_tooltip_off'),
            "has_tooltip": settings_dict.get('property_tooltip_as_bootstrap'),

            "property_label_on": settings_dict.get('property_label_on'),
            "property_label_off": settings_dict.get('property_label_off'),

            "property_icon": settings_dict.get('property_icon'),

            "request": context['request']}
