def privatebeta_enabled(request):
    from django.conf import settings
    return {'privatebeta_enabled': settings.PRIVATEBETA_ENABLE_BETA}

