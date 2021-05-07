import datetime

from django import template
from django.contrib.contenttypes.models import ContentType
from django.template import Library, Node
from django.template.defaultfilters import stringfilter, urlencode
from django.utils.encoding import force_unicode
from django.utils.functional import allow_lazy
from django.utils.safestring import mark_safe

from common.services import AppRedirectionService, DateTimeService
from common.services.pagination_service import PaginationService

register = Library()


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
        tag_name, add_string, remove_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires two arguments" % token.contents.split()[0]
    if not (add_string[0] == add_string[-1] and add_string[0] in ('"', "'")) or not (
            remove_string[0] == remove_string[-1] and remove_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name

    add = string_to_dict(add_string[1:-1])
    remove = string_to_list(remove_string[1:-1])

    return QueryStringNode(add, remove)


class QueryStringNode(Node):
    def __init__(self, add, remove):
        self.add = add
        self.remove = remove

    def render(self, context):
        p_list = []
        p_dict = {}
        query = context["request"].GET
        for k in query:
            p_list.append([k, query.getlist(k)])
            p_dict[k] = query.getlist(k)

        return get_query_string(p_list, p_dict, self.add, self.remove, context)


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

        protected_keywords = ['block']
        if p_list[i][1] not in protected_keywords:
            try:
                p_list[i][1] = template.Variable(p_list[i][1]).resolve(context)
            except:
                pass

    return mark_safe('?' + '&amp;'.join([k[1] if k[0] == '' else u'%s=%s' % (k[0], urlencode(k[1])) for k in p_list if
                                         k[1] is not None and k[1] != 'None']).replace(' ', '%20'))


@register.simple_tag
def setvar(val):
    return val


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


def truncate_chars(s, num):
    s = force_unicode(s)
    length = int(num)
    if len(s) > length:
        length = length - 3
        s = s[:length].strip()
        s += '...'
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
    except ValueError:  # If the argument is not a valid integer.
        return value  # Fail silently.
    return truncate_chars(value, length)


truncatechars.is_safe = True
truncatechars = stringfilter(truncatechars)


@register.filter(name='get_class')
def get_class(value):
    return value.__class__.__name__


@register.simple_tag
def button_loading_class():
    return "ld-ext-right"


@register.simple_tag
def button_loading_indicator():
    return mark_safe('<div class="ld ld-ring ld-spin"></div>')


@register.filter
def more_recent_than(t, seconds):
    now = datetime.datetime.now()
    delta = datetime.timedelta(seconds=seconds)
    return t > now - delta


@register.filter
def get_pks(qs):
    # type: (QuerySet) -> list[int]
    return [x.pk for x in qs]


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def content_type(obj):
    if not obj:
        return None
    return ContentType.objects.get_for_model(obj)


@register.simple_tag
def page_counter(counter, page_number, items_per_page):
    # type: (int, int, int) -> int
    return PaginationService.page_counter(counter, page_number, items_per_page)


@register.simple_tag
def app_redirection_service(request, path):
    return AppRedirectionService.redirect(request, path)


@register.filter
def is_future(dt):
    return dt > DateTimeService.now()


@register.simple_tag
def timestamp(dt):
    return mark_safe('<abbr class="timestamp" data-epoch="%s">...</abbr>' % DateTimeService.epoch(dt))
