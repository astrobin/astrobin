from django.template import Library
from django.conf import settings
from notification import models as notifications
from persistent_messages import models as messages
from astrobin.models import Request

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
def notification_list(request, show_footer = True):
    return {
        'notifications':notifications.Notice.objects.filter(user=request.user)[:10],
        'show_footer':show_footer}


@register.inclusion_tag('inclusion_tags/message_list.html')
def message_list(request, show_footer = True):
    return {
        'messages':messages.Message.objects.filter(user=request.user).order_by('-created')[:10],
        'show_footer':show_footer}


@register.inclusion_tag('inclusion_tags/request_list.html')
def request_list(request, show_footer = True):
    return {
        'requests':Request.objects.filter(to_user=request.user).order_by('-created')[:10],
        'show_footer':show_footer}


@register.simple_tag
def notifications_icon(request):
    basepath = '/static/icons/iconic/orange/'
    if notifications.Notice.objects.filter(user=request.user).filter(unseen=True):
        return basepath + 'new_notifications.png'
    else:
        return basepath + 'notifications.png'


@register.simple_tag
def messages_icon(request):
    basepath = '/static/icons/iconic/orange/'
    if messages.Message.objects.filter(user=request.user).filter(read=False):
        return basepath + 'new_messages.png'
    else:
        return basepath + 'messages.png'


@register.simple_tag
def requests_icon(request):
    basepath = '/static/icons/iconic/orange/'
    if Request.objects.filter(to_user=request.user).filter(fulfilled=False):
        return basepath + 'new_requests.png'
    else:
        return basepath + 'requests.png'


@register.filter
def append_slash(value):
    return value.replace('\n', '\\\n')

