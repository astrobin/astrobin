from typing import List

from django.template import Library
from pybb.models import Category

register = Library()


@register.filter
def exclude_category(categories: List[Category], category_name: str) -> List[Category]:
    return [x for x in categories if x.name != category_name]
