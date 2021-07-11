import django

if django.VERSION < (1, 10):  # pragma: no cover
    MiddlewareParentClass = object
else:  # pragma: no cover
    from django.utils.deprecation import MiddlewareMixin

    MiddlewareParentClass = MiddlewareMixin
