from django.contrib.contenttypes.models import ContentType
from django.template import Library

from nested_comments.models import NestedComment

register = Library()


@register.simple_tag
def nestedcomments_content_type_id():
    return ContentType.objects.get_for_model(NestedComment).pk
