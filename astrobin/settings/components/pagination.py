from django.contrib.staticfiles.templatetags.staticfiles import static


EL_PAGINATION_PER_PAGE = 35
EL_PAGINATION_LOADING =\
    '<img src="%s" alt="..." />' % static('common/images/ajax-loader-bar.gif')

