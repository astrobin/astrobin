from django.contrib.contenttypes.models import ContentType
from django.template import Library

from astrobin_apps_platesolving.solver import SolverBase

register = Library()


@register.inclusion_tag(
    'astrobin_apps_platesolving/inclusion_tags/platesolving_machinery.html',
    takes_context=True)
def platesolving_machinery(context, target):
    content_type = ContentType.objects.get_for_model(target)

    user = None

    if content_type.name == u'image':
        user = target.user
    elif content_type.model == u'imagerevision':
        user = target.image.user

    return {
        'user': user,
        'object_id': target.pk,
        'content_type_id': content_type.pk,
        'solution_id': target.solution.pk if target.solution else 0,
        'solution_status': target.solution.status if target.solution else 0,
    }


@register.filter
def is_advanced_success_status(solution):
    return solution is not None and solution.status == SolverBase.ADVANCED_SUCCESS


@register.filter
def is_advanced_failed_status(solution):
    return solution is not None and solution.status == SolverBase.ADVANCED_FAILED


@register.filter
def has_started_advanced_platesolving(solution):
    return solution is not None and solution.status >= SolverBase.ADVANCED_PENDING
