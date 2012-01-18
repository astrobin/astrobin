from django.conf import settings
from django.db.models import Q
from notification import models as notifications
from astrobin.models import Request


def privatebeta_enabled(request):
    return {'privatebeta_enabled': settings.PRIVATEBETA_ENABLE_BETA}


def notices_count(request):
    response = {}
    if request.user.is_authenticated():
        response['notifications_count'] = notifications.Notice.objects.filter(Q(user = request.user) & Q(unseen = True)).count()
        response['requests_count'] = Request.objects.filter(Q(to_user = request.user) & Q(fulfilled = False)).count()

    return response

