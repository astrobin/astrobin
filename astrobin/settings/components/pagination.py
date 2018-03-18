from django.contrib.staticfiles import storage
EL_PAGINATION_PER_PAGE = 35
EL_PAGINATION_LOADING = '<img src="%s" alt="..." />' % storage.ConfiguredStorage().url('common/images/ajax-loader-bar.gif')

