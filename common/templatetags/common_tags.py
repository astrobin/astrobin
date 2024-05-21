import datetime
import re
import unicodedata
from typing import List, Optional, Union

import bleach
import six
from babel.numbers import format_currency
from bs4 import BeautifulSoup
from dateutil import parser
from django import template
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.template import Library, Node
from django.template.defaultfilters import urlencode
from django.utils.encoding import force_text
from django.utils.functional import keep_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from lxml import etree, html

from astrobin.enums import ImageEditorStep
from astrobin.models import Image
from astrobin_apps_json_api.models import CkEditorFile
from astrobin_apps_users.services import UserService
from common.services import AppRedirectionService, DateTimeService
from common.services.highlighting_service import HighlightingService
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
        raise template.TemplateSyntaxError("%r tag requires two arguments" % token.contents.split()[0])
    if not (add_string[0] == add_string[-1] and add_string[0] in ('"', "'")) or not (
            remove_string[0] == remove_string[-1] and remove_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError("%r tag's argument should be in quotes" % tag_name)

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

        result = get_query_string(p_list, p_dict, self.add, self.remove, context)

        if result == '?':
            return ''

        return result


def get_query_string(p_list, p_dict, new_params, remove, context):
    """
    Add and remove query parameters. From `django.contrib.admin`.
    """
    for r in remove:
        p_list = [[x[0], x[1]] for x in p_list if not x[0].startswith(r)]
    for k, v in list(new_params.items()):
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
            p_list[i][1] = mark_safe('&amp;'.join(['%s=%s' % (p_list[i][0], k) for k in p_list[i][1]]))
            p_list[i][0] = ''

        protected_keys = ['q', 'subject', 'telescope', 'camera']
        protected_values = ['block']
        if p_list[i][0] not in protected_keys and p_list[i][1] not in protected_values:
            try:
                p_list[i][1] = template.Variable(p_list[i][1]).resolve(context)
            except:
                pass

    return mark_safe('?' + '&amp;'.join([k[1] if k[0] == '' else '%s=%s' % (k[0], urlencode(k[1])) for k in p_list if
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


@register.filter(is_safe=True)
def truncatechars(value, arg):
    """
    Truncates a string after a certain number of characters, but respects word boundaries.

    Argument: Number of characters to truncate after.
    """

    def do_truncatechars(s, num):
        s = force_text(s)
        length = int(num)
        if len(s) > length:
            length = length - 3
            s = s[:length].strip()
            s += '...'
        return s

    try:
        length = int(arg)
    except ValueError:  # If the argument is not a valid integer.
        return value  # Fail silently.
    return do_truncatechars(value, length)


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
def app_redirection_service(path):
    return AppRedirectionService.redirect(path)


@register.simple_tag
def image_editor_redirection_service(image: Image, user: User, step: ImageEditorStep) -> str:
    return AppRedirectionService.redirect(
        f'/i/{image.get_id()}/edit#'
        f'{AppRedirectionService.image_editor_step_number(user, step)}'
    )

@register.filter
def is_future(dt):
    return dt > DateTimeService.now()

@register.filter
def is_after_datetime(dt, after_string):
    return dt > parser.parse(after_string)

@register.simple_tag
def timestamp(dt):
    return mark_safe('<abbr class="timestamp" data-epoch="%s">...</abbr>' % DateTimeService.epoch(dt))


@register.filter
def strip_html(value: str, allowed_tags=settings.SANITIZER_ALLOWED_TAGS) -> str:
    if isinstance(value, str):
        try:
            # Attempt to parse as HTML fragment
            document = html.fragment_fromstring(value, create_parent=False)
            document = html.tostring(document, encoding='unicode', with_tail=True)
        except etree.ParserError:
            # If parsing fails, treat as plain text
            document = value

        # Sanitize with bleach
        cleaned_html = bleach.clean(
            document,
            tags=allowed_tags,
            attributes=settings.SANITIZER_ALLOWED_ATTRIBUTES,
            styles=[],
            strip=True
        )

        # Mark the sanitized HTML as safe for rendering
        return mark_safe(cleaned_html)

    return value

@register.filter
def ensure_url_protocol(url: str) -> str:
    if '://' in url:
        return url

    return f'http://{url}'


class HighlightTextNode(template.Node):
    def __init__(
        self, text, terms, as_var=None, html_tag=None, css_class=None, max_length=None, dialect=None, allow_lists=True
    ):
        self.text = template.Variable(text)
        self.terms = template.Variable(terms)
        self.as_var = as_var
        self.html_tag = html_tag
        self.css_class = css_class
        self.max_length = max_length
        self.dialect = dialect
        self.allow_lists = allow_lists

        if html_tag is not None:
            self.html_tag = template.Variable(html_tag)

        if css_class is not None:
            self.css_class = template.Variable(css_class)

        if max_length is not None:
            self.max_length = template.Variable(max_length)

        if dialect is not None:
            self.dialect = template.Variable(dialect)

        if isinstance(allow_lists, str):
            self.allow_lists = template.Variable(allow_lists)
        else:
            # Direct value (bool or otherwise)
            self.allow_lists = allow_lists

    def render(self, context) -> str:
        text = self.text.resolve(context)
        terms = str(self.terms.resolve(context))
        kwargs = {}

        if self.html_tag is not None:
            kwargs['html_tag'] = self.html_tag.resolve(context)

        if self.css_class is not None:
            kwargs['css_class'] = self.css_class.resolve(context)

        if self.max_length is not None:
            kwargs['max_length'] = self.max_length.resolve(context)

        if self.dialect is not None:
            kwargs['dialect'] = self.dialect.resolve(context)

        if self.allow_lists is not None:
            if isinstance(self.allow_lists, template.Variable):
                kwargs['allow_lists'] = self.allow_lists.resolve(context)
            else:
                # Directly use the value
                kwargs['allow_lists'] = self.allow_lists

        rendered_html = HighlightingService(text, terms, **kwargs).render_html()

        if self.as_var:
            context[self.as_var] = rendered_html
            return ''
        else:
            return rendered_html

@register.tag
def highlight_text(parser, token):
    bits = token.split_contents()
    tag_name = bits[0]

    if not len(bits) % 2 == 0:
        raise template.TemplateSyntaxError(
            "'%s' tag requires valid pairings arguments." % tag_name
        )

    if len(bits) < 4:
        raise template.TemplateSyntaxError(
            "'%s' tag requires an object and a query provided by 'with'." % tag_name
        )

    if bits[2] != "with":
        raise template.TemplateSyntaxError(
            "'%s' tag's second argument should be 'with'." % tag_name
        )

    as_var = None
    if len(bits) > 2 and bits[-2] == 'as':
        as_var = bits[-1]
        bits = bits[:-2]

    text = bits[1]
    query = bits[3]

    arg_bits = iter(bits[4:])
    kwargs = {}

    for bit in arg_bits:
        if bit == 'css_class':
            kwargs['css_class'] = next(arg_bits)

        if bit == 'html_tag':
            kwargs['html_tag'] = next(arg_bits)

        if bit == 'max_length':
            kwargs['max_length'] = next(arg_bits)

        if bit == 'dialect':
            kwargs['dialect'] = next(arg_bits)

        if bit == 'allow_lists':
            kwargs['allow_lists'] = next(arg_bits)

    return HighlightTextNode(text, query, as_var, **kwargs)


@register.simple_tag
def get_verbose_field_name(instance, field_name):
    return instance._meta.get_field(field_name).verbose_name.title()


@register.filter
def add_days(value, days):
    return value + datetime.timedelta(days=days)


@register.filter
def asciify(value):
    try:
        return unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
    except:
        return value


@register.filter
def is_in_group(user: User, group_name: Union[str, List[str]]) -> bool:
    return UserService(user).is_in_group(group_name)


@register.filter
def is_in_astrobin_group(user: User, group_name: Union[str, List[str]]) -> bool:
    return UserService(user).is_in_astrobin_group(group_name)


@register.simple_tag(takes_context=True)
def pop_session_value(context, session_key):
    request = context['request']
    value = request.session.pop(session_key, None)
    return value


@register.filter
def percentage(x: float, y: float) -> float:
    if y == 0:
        return 0

    return (x / y) * 100


@register.filter
def get_mime_type(filename: str) -> Optional[str]:
    extension = filename.split('.')[-1]

    if extension == 'mp4':
        return 'video/mp4'
    elif extension == 'webm':
        return 'video/webm'
    elif extension in ['ogg', 'ogv']:
        return 'video/ogg'
    elif extension == 'mov':
        return 'video/quicktime'
    elif extension == 'avi':
        return 'video/x-msvideo'
    elif extension == 'wmv':
        return 'video/x-ms-wmv'
    elif extension == 'flv':
        return 'video/x-flv'
    elif extension == 'mkv':
        return 'video/x-matroska'
    elif extension == '3gp':
        return 'video/3gpp'
    elif extension == 'm4v':
        return 'video/x-m4v'

    return None


@register.filter
def html_image_thumbnails(html_text: str, gallery_rel: str) -> str:
    def create_fancybox_html(ckeditor_file) -> str:
        return f'<a href="{ckeditor_file.upload.url}" data-fancybox="{gallery_rel}" class="fancybox">' \
               f'<img src="{ckeditor_file.thumbnail.url}" alt="{ckeditor_file.filename}" />' \
               f'</a>'

    soup = BeautifulSoup(html_text, 'html.parser')

    for img in soup.find_all('img'):
        if img.parent.name != 'a':
            src = img.get('src')
            if src:
                try:
                    ckeditor_file = CkEditorFile.objects.get(upload=src.replace(settings.MEDIA_URL, ''))
                    if ckeditor_file.thumbnail:
                        fancybox_html = create_fancybox_html(ckeditor_file)
                        img.replace_with(BeautifulSoup(fancybox_html, 'html.parser'))
                except CkEditorFile.DoesNotExist:
                    continue

    return str(soup)


@register.tag
def removelinebreaks(parser, token):
    nodelist = parser.parse(('endremovelinebreaks',))
    parser.delete_first_token()
    return RemoveLinebreakNode(nodelist)


class RemoveLinebreakNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        strip_line_breaks = keep_lazy(six.text_type)(lambda x: x.replace('\n', ' '))
        return strip_line_breaks(self.nodelist.render(context).strip())

@register.tag
def removemultiplespaces(parser, token):
    nodelist = parser.parse(('endremovemultiplespaces',))
    parser.delete_first_token()
    return RemoveMultipleSpacesNode(nodelist)


class RemoveMultipleSpacesNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        strip_multiple_spaces = keep_lazy(six.text_type)(lambda x: re.sub(r'\s+', ' ', x))
        return strip_multiple_spaces(self.nodelist.render(context).strip())


@register.filter
def contains(value, arg):
    return arg in value


@register.filter
def currency(value: int, currency_code: str):
    try:
        locale = get_language()  # Get the current language code
        if not locale:
            locale = 'en_US'  # Default to 'en_US' if no language code is found
        return format_currency(value, currency_code, locale=locale)
    except Exception:
        return value  # In case of any error, return the value as is
