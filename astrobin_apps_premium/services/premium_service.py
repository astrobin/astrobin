import functools
import sys
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from subscription.models import UserSubscription

from astrobin.models import UserProfile

SUBSCRIPTION_NAMES = (
    'AstroBin Lite',
    'AstroBin Premium',

    'AstroBin Lite 2020+',
    'AstroBin Premium 2020+',
    'AstroBin Ultimate 2020+',

    'AstroBin Lite (autorenew)',
    'AstroBin Premium (autorenew)',

    'AstroBin Premium 20% discount',
    'AstroBin Premium 30% discount',
    'AstroBin Premium 40% discount',
    'AstroBin Premium 50% discount',
)


def _compareValidity(a, b):
    return a.valid() - b.valid()


def _compareNames(a, b):
    """
    This function is used to determine the "weight" of each Premium subscription. When a user has multiple, only the
    heaviest one gets considered throughout the website.
    :param a: left operand.
    :param b: right operand.
    :return: a negative number if the left operand is heavier than thee left, 0 if equal, a positive number otherwise.
    """
    key = {
        "AstroBin Lite (autorenew)": 0,
        "AstroBin Lite": 1,
        "AstroBin Lite 2020+": 2,
        "AstroBin Premium (autorenew)": 3,
        "AstroBin Premium": 4,
        'AstroBin Premium 20% discount': 5,
        'AstroBin Premium 30% discount': 6,
        'AstroBin Premium 40% discount': 7,
        'AstroBin Premium 50% discount': 8,
        "AstroBin Premium 2020+": 9,
        "AstroBin Ultimate 2020+": 10
    }

    return key[b.subscription.name] - key[a.subscription.name]


class PremiumService:
    user: User
    
    def __init__(self, user: User):
        self.user = user
        
    def clear_subscription_status_cache_keys(self):
        pk: int = self.user.pk
        
        for key in (
            'has_expired_paid_subscription',
            'has_paid_subscription_near_expiration',
            'astrobin_is_donor',
            'astrobin_valid_usersubscription'
        ):
            cache.delete(f'{key}_{pk}')

    def get_valid_usersubscription(self):
        if self.user is None or self.user.pk is None:
            return None

        cache_key = "astrobin_valid_usersubscription_%d" % self.user.pk

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        us = [obj for obj in UserSubscription.objects.filter(
            user__username=self.user.username,
            subscription__name__in=SUBSCRIPTION_NAMES,
            expires__gte=datetime.today()
        )]

        if len(us) == 0:
            result = None
        elif len(us) == 1:
            result = us[0]
        else:
            sortedByName = sorted(us, key=functools.cmp_to_key(_compareNames))
            sortedByValidity = sorted(sortedByName, key=functools.cmp_to_key(_compareValidity))
            result = sortedByValidity[0]

        cache.set(cache_key, result, 300)

        return result


    @staticmethod
    def get_image_quota_usage_percentage(user_profile: UserProfile, user_subscription: UserSubscription):
        counter = user_profile.premium_counter
        percent = 100
    
        if user_subscription is None:
            # User is on Free, or their subscription is inactive, or expired.
            percent = counter / float(settings.PREMIUM_MAX_IMAGES_FREE) * 100
    
        elif user_subscription.subscription.group.name == "astrobin_lite":
            percent = counter / float(settings.PREMIUM_MAX_IMAGES_LITE) * 100
    
        elif user_subscription.subscription.group.name == "astrobin_premium":
            # Premium gets unlimited uploads.
            percent = -1
    
        elif user_subscription.subscription.group.name == "astrobin_lite_2020":
            percent = counter / float(settings.PREMIUM_MAX_IMAGES_LITE_2020) * 100
    
        elif user_subscription.subscription.group.name == "astrobin_premium_2020":
            percent = -1
    
        elif user_subscription.subscription.group.name == "astrobin_ultimate_2020":
            # Ultimate 2020 gets unlimited uploads.
            percent = -1
    
        if percent > 100:
            percent = 100
    
        return percent
    
    
    def get_image_quota_usage_class(p: int):
        if p < 90: return 'progress-success'
        if p > 97: return 'progress-danger'
        return 'progress-warning'
    

    @staticmethod
    def get_max_allowed_image_size(user_subscription: UserSubscription):
        if user_subscription is None:
            return settings.PREMIUM_MAX_IMAGE_SIZE_FREE_2020

        group: str = user_subscription.subscription.group.name
    
        if group == "astrobin_lite":
            return sys.maxsize
    
        if group == "astrobin_premium":
            return sys.maxsize
    
        if group == "astrobin_lite_2020":
            return settings.PREMIUM_MAX_IMAGE_SIZE_LITE_2020
    
        if group == "astrobin_premium_2020":
            return settings.PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020
    
        if group == "astrobin_ultimate_2020":
            return sys.maxsize
    
        return 0
    
    
    def get_max_allowed_revisions(user_subscription: UserSubscription):
        if user_subscription is None:
            return settings.PREMIUM_MAX_REVISIONS_FREE_2020

        group: str = user_subscription.subscription.group.name

        if group == "astrobin_lite":
            return sys.maxsize
    
        if group == "astrobin_premium":
            return sys.maxsize
    
        if group == "astrobin_lite_2020":
            return settings.PREMIUM_MAX_REVISIONS_LITE_2020
    
        if group == "astrobin_premium_2020":
            return settings.PREMIUM_MAX_REVISIONS_PREMIUM_2020
    
        if group == "astrobin_ultimate_2020":
            return sys.maxsize
    
        return 0
