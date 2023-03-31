MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'multidb.middleware.PinningRouterMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'silk.middleware.SilkyMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'astrobin.middleware.EnforceOtpVerificationMiddleware',  # Keep before LastSeenMiddleware
    'astrobin.middleware.LastSeenMiddleware',
    'astrobin.middleware.BlockNonPayingUsersFromRussiaMiddleware',
    'astrobin.middleware.BlockSuspendedUserMiddleware',
    'astrobin.middleware.LogoutDeletedUserMiddleware',
    'astrobin.middleware.MarkNotificationAsReadMiddleware',
    'astrobin.middleware.PreviousTopicReadMarkerMiddleware',
    'astrobin.middleware.RestFrameworkTokenCookieMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
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

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
