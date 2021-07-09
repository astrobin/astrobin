from django.contrib.contenttypes.models import ContentType
from django.template import Library

from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.services import SolutionService
from astrobin_apps_platesolving.solver import SolverBase

register = Library()


@register.inclusion_tag(
    'astrobin_apps_platesolving/inclusion_tags/platesolving_machinery.html',
    takes_context=True)
def platesolving_machinery(context, target):
    content_type = ContentType.objects.get_for_model(target)

    user = None

    if content_type.name == 'image':
        user = target.user
    elif content_type.model == 'imagerevision':
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


@register.filter
def get_search_query_around(solution, degrees):
    # type: (Solution, int) -> str
    return SolutionService(solution).get_search_query_around(degrees)


@register.filter
def supports_search_around(solution):
    # type: (Solution) -> bool
    return (solution.advanced_ra or solution.ra) and (solution.advanced_dec or solution.dec)
