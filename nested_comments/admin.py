# Django
from django.contrib import admin

# This app
from .models import NestedComment


admin.site.register(NestedComment)
