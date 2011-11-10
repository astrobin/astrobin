from datetime import datetime

from django.template.defaultfilters import timesince
from django.utils.translation import ugettext as _
from django.template import  Library
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from notification import models as notifications
from persistent_messages import models as messages
from celery.result import AsyncResult

from astrobin.models import Request

register = Library() 

@register.simple_tag
def current(request, pattern):
    import re
    if re.search(pattern, request.path):
        return 'current'
    return ''


@register.inclusion_tag('inclusion_tags/image_list.html')
def image_list(request, object_list):
    paginator = Paginator(object_list, 10)

    page = request.GET.get('p')
    try:
        images = paginator.page(page)
    except (TypeError, PageNotAnInteger):
        images = paginator.page(1)
    except EmptyPage:
        images = paginator.page(paginator.num_pages)

    return {'images': images,
            'thumbnail_size':settings.THUMBNAIL_SIZE,
            's3_url':settings.S3_URL,
            'query':request.GET.get('q'),
           }

@register.inclusion_tag('inclusion_tags/notification_list.html')
def notification_list(request, show_footer = True, limit = 0):
    ret = notifications.Notice.objects.filter(user=request.user)
    if limit > 0:
        ret = ret[:limit]
    return {
        'notifications':ret,
        'show_footer':show_footer}


@register.inclusion_tag('inclusion_tags/message_list.html')
def message_list(request, show_footer = True):
    return {
        'messages':messages.Message.objects.filter(user=request.user).order_by('-created')[:10],
        'show_footer':show_footer}


@register.inclusion_tag('inclusion_tags/request_list.html')
def request_list(request, show_footer = True):
    return {
        'requests':Request.objects.filter(to_user=request.user).order_by('-created').select_subclasses()[:10],
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


@register.simple_tag
def image_is_ready(image):
    return AsyncResult(image.store_task_id).ready()


@register.inclusion_tag('inclusion_tags/form_saved.html')
def form_saved(request):
    return {'saved': 'saved' in request.GET}


@register.filter
def ago(date_time):
    date_time = date_time.replace(tzinfo = None)
    diff = abs(date_time - datetime.today())
    if diff.days <= 0:
        span = timesince(date_time)
        span = span.split(",")[0] # just the most significant digit
        if span == "0 minutes":
            return _("seconds ago")
        return _("%s ago") % span 
    return date(date_time)  

