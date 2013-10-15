# Django
from django.template import Library, Node

# This app
from astrobin_apps_platesolving.solver import Solver


register = Library()


def platesolving_machinery(context, image):
    return {
        'image_id': image.id,
        'solution_id': image.solution.id if image.solution else 0,
    }


register.inclusion_tag(
    'astrobin_apps_platesolving/inclusion_tags/platesolving_machinery.html',
    takes_context = True)(platesolving_machinery)

