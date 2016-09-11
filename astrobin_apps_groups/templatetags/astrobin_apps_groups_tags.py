# Django
from django.template import Library


register = Library()


@register.filter
def count_images_in_group(user, group):
    return group.images.filter(user = user).count()

@register.filter
def count_forum_posts_in_group(user, group):
    return group.forum.posts.filter(user = user).count()
