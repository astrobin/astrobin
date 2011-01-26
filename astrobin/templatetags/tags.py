from django.template import Library
from django.conf import settings
from notification import models as notifications

register = Library() 

@register.simple_tag
def current(request, pattern):
    import re
    if re.search(pattern, request.path):
        return 'current'
    return ''


@register.inclusion_tag('inclusion_tags/image_list.html')
def image_list(objects_list):
    return {'image_list': [i.object for i in objects_list],
            'thumbnail_size':settings.THUMBNAIL_SIZE,
            's3_thumbnails_bucket':settings.S3_THUMBNAILS_BUCKET,
            's3_abpod_bucket':settings.S3_ABPOD_BUCKET,
            's3_url':settings.S3_URL,
           }

@register.inclusion_tag('inclusion_tags/notification_list.html')
def notification_list(request):
    return {
        'notifications':notifications.Notice.objects.filter(user=request.user)[:10]}

@register.simple_tag
def notifications_icon(request):
    if notifications.Notice.objects.filter(user=request.user).filter(unseen=True):
        return '/static/icons/iconic/orange/new_notifications.png'
    else:
        return '/static/icons/iconic/orange/notifications.png'

