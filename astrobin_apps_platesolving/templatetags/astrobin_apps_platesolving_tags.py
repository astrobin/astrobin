# Django
from django.template import Library, Node

# This app
from astrobin_apps_platesolving.solver import Solver


register = Library()


def platesolving_status(context, solution, image_field):
    return {}


register.inclusion_tag(
    'astrobin_apps_platesolving/inclusion_tags/platesolving_status.html',
    takes_context = True)(platesolving_status)

