MIDDLEWARE_CLASSES = [
    'corsheaders.middleware.CorsMiddleware',
    'multidb.middleware.PinningRouterMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'silk.middleware.SilkyMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'astrobin.middleware.LastSeenMiddleware',
    'astrobin.middleware.LogoutDeletedUserMiddleware',
    'astrobin.middleware.MarkNotificationAsReadMiddleware',
    'astrobin.middleware.PreviousTopicReadMarkerMiddleware',
    'astrobin.middleware.RestFrameworkTokenCookieMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
    'gadjo.requestprovider.middleware.RequestProvider',
]

if not TESTING:
    MIDDLEWARE_CLASSES += [
        'django.middleware.locale.LocaleMiddleware',
    ]

if not DEBUG:
    MIDDLEWARE_CLASSES += [
        'django.middleware.gzip.GZipMiddleware',
        'pipeline.middleware.MinifyHTMLMiddleware',
    ]

MIDDLEWARE_CLASSES += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
