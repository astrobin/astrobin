NOTIFICATION_LANGUAGE_MODULE = "astrobin.UserProfile"
NOTIFICATION_BACKENDS = (
    ("on-site", "astrobin_apps_notifications.backends.PersistentMessagesBackend"),
    ("email", "astrobin_apps_notifications.backends.EmailBackend"),
)
