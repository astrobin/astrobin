import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "astrobin.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

if os.environ.get("DEBUG", "true") == "true":
    from wdb.ext import WdbMiddleware
    application = WdbMiddleware(application)
