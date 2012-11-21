from .groups import is_premium, byte_limit
from .models import RawImage

def user_used_bytes(user):
    sizes = RawImage.objects\
        .filter(user = user)\
        .values_list('size', flat = True)
    return sum(sizes)


def user_used_percent(user):
    b = user_used_bytes(user)
    limit = byte_limit(user)
    return b * 100 / limit


def user_progress_class(user):
    p = user_used_percent(user)
    if p < 90: return 'progress-success'
    if p > 97: return 'progress-danger'
    return 'progress-warning'


def user_is_over_limit(user):
    return user_used_percent(user) >= 100
