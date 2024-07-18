import os

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'multidb.middleware.PinningRouterMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'astrobin.middleware.SentryMiddleware',
    'astrobin.middleware.HttpMethodOverrideMiddleware',
    'astrobin.middleware.LoginAttemptMiddleware',  # Keep before LastSeenMiddleware
    'astrobin.middleware.LastSeenMiddleware',
    'astrobin.middleware.BlockNonPayingUsersFromRussiaMiddleware',
    'astrobin.middleware.BlockSuspendedUserMiddleware',
    'astrobin.middleware.GoneMiddleware',
    'astrobin.middleware.LogoutDeletedUserMiddleware',
    'astrobin.middleware.MarkNotificationAsReadMiddleware',
    'astrobin.middleware.PreviousTopicReadMarkerMiddleware',
    'astrobin.middleware.RestFrameworkTokenCookieMiddleware',
    'astrobin.middleware.SlowRequestLoggingMiddleware',
    'astrobin.middleware.HoneypotRequestLoggingMiddleware',
    'astrobin.middleware.ThreadLocalsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

if not TESTING:
    MIDDLEWARE += [
        'django.middleware.locale.LocaleMiddleware',
        'astrobin.middleware.LocaleMiddleware',
    ]

if not DEBUG:
    MIDDLEWARE += [
        'django.middleware.gzip.GZipMiddleware',
        'pipeline.middleware.MinifyHTMLMiddleware',
    ]

if os.environ.get('LOG_HTTP_REQUESTS', 'false').strip() == 'true':
    MIDDLEWARE += [
        'astrobin.middleware.RequestLoggingMiddleware',
    ]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
