# Django
from django.contrib.contenttypes.models import ContentType
from django.template import Library, Node

# This app
from astrobin_apps_platesolving.solver import Solver


register = Library()


@register.inclusion_tag(
    'astrobin_apps_platesolving/inclusion_tags/platesolving_machinery.html',
    takes_context = True)
def platesolving_machinery(context, target):
    content_type = ContentType.objects.get_for_model(target)
    return {
        'object_id': target.pk,
        'content_type_id': content_type.pk,
        'solution_id': target.solution.pk if target.solution else 0,
    }

