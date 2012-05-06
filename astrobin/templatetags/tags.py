from datetime import datetime
import random
import string

from django.template.defaultfilters import timesince
from django.utils.translation import ugettext as _
from django import template
from django.template import Library, Node
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.safestring import mark_safe
from django.db.models import Q

from django.utils.encoding import force_unicode
from django.utils.functional import allow_lazy
from django.template.defaultfilters import stringfilter

from notification import models as notifications
from persistent_messages import models as messages
from celery.result import AsyncResult

from astrobin.models import Request

register = Library() 

@register.simple_tag
def current(request, pattern):
    import re
    if re.search(pattern, request.path):
        return 'active'
    return ''

@register.simple_tag
def in_gallery(request):
    import re
    if re.search('/users/[\w.@+-]+/$', request.path):
        return 'visible'
    return 'hidden'

@register.inclusion_tag('inclusion_tags/related_images.html')
def related_images(request, object_list, type):
    paginator = Paginator(object_list, 12)

    page = request.GET.get('p')
    try:
        images = paginator.page(page)
    except (TypeError, PageNotAnInteger):
        images = paginator.page(1)
    except EmptyPage:
        images = paginator.page(paginator.num_pages)

    return {
            'request': request,
            'images': images,
            'small_thumbnail_size':settings.SMALL_THUMBNAIL_SIZE,
            's3_url':settings.S3_URL,
            'related_type': type,
           }


@register.inclusion_tag('inclusion_tags/notification_list.html')
def notification_list(request, show_footer = True, limit = 0):
    unseen = notifications.Notice.objects.filter(user = request.user, unseen = True)
    seen = notifications.Notice.objects.filter(user = request.user, unseen = False)
    if limit > 0:
        seen = seen[:limit]
    return {
        'unseen': unseen,
        'seen': seen,
        'show_footer': show_footer}


@register.inclusion_tag('inclusion_tags/request_list.html')
def request_list(request, show_footer = True):
    return {
        'requests':Request.objects.filter(to_user=request.user).order_by('-created').select_subclasses()[:10],
        'show_footer':show_footer}


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
        if span == "0 " + _("minutes"):
            return _("seconds ago")
        return _("%s ago") % span 
    return datetime.date(date_time)  


@register.tag
def query_string(parser, token):
    """
    Allows you too manipulate the query string of a page by adding and removing keywords.
    If a given value is a context variable it will resolve it.
    Based on similiar snippet by user "dnordberg".
    
    requires you to add:
    
    TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    )
    
    to your django settings. 
    
    Usage:
    http://www.url.com/{% query_string "param_to_add=value, param_to_add=value" "param_to_remove, params_to_remove" %}
    
    Example:
    http://www.url.com/{% query_string "" "filter" %}filter={{new_filter}}
    http://www.url.com/{% query_string "page=page_obj.number" "sort" %} 
    
    """
    try:
        tag_name, add_string,remove_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires two arguments" % token.contents.split()[0]
    if not (add_string[0] == add_string[-1] and add_string[0] in ('"', "'")) or not (remove_string[0] == remove_string[-1] and remove_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name
    
    add = string_to_dict(add_string[1:-1])
    remove = string_to_list(remove_string[1:-1])
    
    return QueryStringNode(add,remove)

class QueryStringNode(Node):
    def __init__(self, add,remove):
        self.add = add
        self.remove = remove
        
    def render(self, context):
        p_list = []
        p_dict = {}
        query = context["request"].GET
        for k in query:
            p_list.append([k, query.getlist(k)])
            p_dict[k] = query.getlist(k)

        return get_query_string(p_list,p_dict,self.add,self.remove,context)

def get_query_string(p_list, p_dict, new_params, remove, context):
    """
    Add and remove query parameters. From `django.contrib.admin`.
    """
    for r in remove:
        p_list = [[x[0], x[1]] for x in p_list if not x[0].startswith(r)]
    for k, v in new_params.items():
        if k in p_dict and v is None:
            p_list = [[x[0], x[1]] for x in p_list if not x[0] == k]
        elif k in p_dict and v is not None:
            for i in range(0, len(p_list)):
                if p_list[i][0] == k:
                    p_list[i][1] = [v]

        elif v is not None:
            p_list.append([k, [v]])

    for i in range(0, len(p_list)):
        if len(p_list[i][1]) == 1:
            p_list[i][1] = p_list[i][1][0]
        else:
            p_list[i][1] = mark_safe('&amp;'.join([u'%s=%s' % (p_list[i][0], k) for k in p_list[i][1]]))
            p_list[i][0] = ''
        try:
            p_list[i][1] = template.Variable(p_list[i][1]).resolve(context)
        except:
            pass

    return mark_safe('?' + '&amp;'.join([k[1] if k[0] == '' else u'%s=%s' % (k[0], k[1]) for k in p_list]).replace(' ', '%20'))

# Taken from lib/utils.py   
def string_to_dict(string):
    kwargs = {}
    
    if string:
        string = str(string)
        if ',' not in string:
            # ensure at least one ','
            string += ','
        for arg in string.split(','):
            arg = arg.strip()
            if arg == '': continue
            kw, val = arg.split('=', 1)
            kwargs[kw] = val
    return kwargs

def string_to_list(string):
    args = []
    if string:
        string = str(string)
        if ',' not in string:
            # ensure at least one ','
            string += ','
        for arg in string.split(','):
            arg = arg.strip()
            if arg == '': continue
            args.append(arg)
    return args


@register.filter
def string_to_date(date):
    try:
        return datetime.strptime(date, "%Y-%m-%d")
    except:
        return datetime.now()
        

def truncate_chars(s, num):
    """
    Template filter to truncate a string to at most num characters respecting word
    boundaries.
    """
    s = force_unicode(s)
    length = int(num)
    if len(s) > length:
        length = length - 4
        if s[length-1] == ' ' or s[length] == ' ':
            s = s[:length].strip()
        else:
            words = s[:length].split()
            if len(words) > 1:
                del words[-1]
            s = u' '.join(words)
        s += ' ...'
    return s
truncate_chars = allow_lazy(truncate_chars, unicode)

@register.filter
def truncatechars(value, arg):
    """
    Truncates a string after a certain number of characters, but respects word boundaries.
    
    Argument: Number of characters to truncate after.
    """
    try:
        length = int(arg)
    except ValueError: # If the argument is not a valid integer.
        return value # Fail silently.
    return truncate_chars(value, length)
truncatechars.is_safe = True
truncatechars = stringfilter(truncatechars)


def image_list(context, request, object_list, paginate = True, size = settings.THUMBNAIL_SIZE):
    ret = {}

    try:
        paginator = context['paginator']
        page = int(context['page'])
        pages = int(context['pages'])
        page_obj = context['page_obj']
        next = context['next']
        previous = context['previous']
        has_next = context['has_next']
        has_previous = context['has_previous']

        paging = True
        adjacent_pages = 3
    except KeyError:
        paging = False

    image_list = object_list

    if paging:
        startPage = max(page - adjacent_pages, 1)
        if startPage <= 3: startPage = 1
        endPage = page + adjacent_pages + 1
        if endPage >= pages - 1: endPage = pages + 1
        page_numbers = [n for n in range(startPage, endPage) \
                if n > 0 and n <= pages]

        ret = {
            'page_obj': page_obj,
            'paginator': paginator,
            'page': page,
            'pages': pages,
            'page_numbers': page_numbers,
            'next': next,
            'previous': previous,
            'has_next': has_next,
            'has_previous': has_previous,
            'show_first': 1 not in page_numbers,
            'show_last': pages not in page_numbers,
        }

    ret = dict(ret.items() + {
        'image_list': image_list,
        'paginate': paginate,
        'thumbnail_size': size,
        's3_url':settings.S3_URL,
        'request': request,
        'sort': request.GET.get('sort'),
    }.items())

    return ret
register.inclusion_tag('inclusion_tags/image_list.html', takes_context=True)(image_list)


def messier_list(context, request, object_list, paginate = True):
    adjacent_pages = 3

    paginator = context['paginator']
    page = int(context['page'])
    pages = int(context['pages'])
    page_obj = context['page_obj']
    next = context['next']
    previous = context['previous']
    has_next = context['has_next']
    has_previous = context['has_previous']

    startPage = max(page - adjacent_pages, 1)
    if startPage <= 3: startPage = 1
    endPage = page + adjacent_pages + 1
    if endPage >= pages - 1: endPage = pages + 1
    page_numbers = [n for n in range(startPage, endPage) \
            if n > 0 and n <= pages]

    return {
        'page_obj': page_obj,
        'paginator': paginator,
        'page': page,
        'pages': pages,
        'page_numbers': page_numbers,
        'next': next,
        'previous': previous,
        'has_next': has_next,
        'has_previous': has_previous,
        'show_first': 1 not in page_numbers,
        'show_last': pages not in page_numbers,
        'object_list': object_list,
        'paginate': paginate,
        'thumbnail_size':settings.THUMBNAIL_SIZE,
        's3_url':settings.S3_URL,
        'request': request,
        'sort': request.GET.get('sort'),
    }
register.inclusion_tag('inclusion_tags/messier_list.html', takes_context=True)(messier_list)


def search_image_list(context, request, object_list, paginate = True):
    adjacent_pages = 3

    try:
        paginator = context['paginator']
        page = int(context['page'])
        pages = int(context['pages'])
        page_obj = context['page_obj']
        next = context['next']
        previous = context['previous']
        has_next = context['has_next']
        has_previous = context['has_previous']
    except:
        paginator = context['paginator']
        page_obj = context['page']
        page = page_obj.number
        pages = paginator.num_pages
        next = page_obj.next_page_number
        previous = page_obj.previous_page_number
        has_next = page_obj.has_next
        has_previous = page_obj.has_previous

    image_list = object_list

    startPage = max(page - adjacent_pages, 1)
    if startPage <= 3: startPage = 1
    endPage = page + adjacent_pages + 1
    if endPage >= pages - 1: endPage = pages + 1
    page_numbers = [n for n in range(startPage, endPage) \
            if n > 0 and n <= pages]

    return {
        'page_obj': page_obj,
        'paginator': paginator,
        'page': page,
        'pages': pages,
        'page_numbers': page_numbers,
        'next': next,
        'previous': previous,
        'has_next': has_next,
        'has_previous': has_previous,
        'paginate': paginate,
        'show_first': 1 not in page_numbers,
        'show_last': pages not in page_numbers,
        'image_list': image_list,
        'thumbnail_size':settings.THUMBNAIL_SIZE,
        's3_url':settings.S3_URL,
        'request': request,
        'sort': request.GET.get('sort'),
    }
register.inclusion_tag('inclusion_tags/search_image_list.html', takes_context=True)(search_image_list)

@register.filter
def seconds_to_hours(value):
    try:
        value = int(value)
    except ValueError:
        return "0"

    return "%.1f" % (int(value) / 3600.0)


@register.simple_tag(takes_context = True)
def random_id(context, size = 8, chars = string.ascii_uppercase + string.digits):
    id = ''.join(random.choice(chars) for x in range(size))
    context['randomid'] = id
    return ''


@register.filter
def cut_decimals(value, places):
    try:
        value = float(value)
    except ValueError:
        return value

    return '{0:.{1}f}'.format(value, places)


@register.filter
def is_checkbox(value):
    from django.forms.fields import CheckboxInput
    return isinstance(value, CheckboxInput)


@register.simple_tag
def search_form_query():
    query = ''

    for i in range(0, 7):
        query += '&amp;license=%d' % i

    query += '&amp;telescope_type=any'
    for i in range(0, 23):
        query += '&amp;telescope_type=%d' % i

    query += '&amp;camera_type=any'
    for i in range(0, 6):
        query += '&amp;camera_type=%d' % i

    return query
