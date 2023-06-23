import functools
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q, QuerySet
from django.utils import timezone
from subscription.models import UserSubscription

from astrobin.enums.full_size_display_limitation import FullSizeDisplayLimitation
from astrobin.models import Image, UserProfile
from common.services import DateTimeService


class SubscriptionName(Enum):
    LITE_CLASSIC = 'AstroBin Lite'
    LITE_CLASSIC_AUTORENEW = 'AstroBin Lite (autorenew)'
    PREMIUM_CLASSIC = 'AstroBin Premium'
    PREMIUM_CLASSIC_AUTORENEW = 'AstroBin Premium (autorenew)'

    LITE_2020 = 'AstroBin Lite 2020+'
    LITE_2020_AUTORENEW_YEARLY = 'AstroBin Lite 2020+ (autorenew/yearly)'
    LITE_2020_AUTORENEW_MONTHLY = 'AstroBin Lite 2020+ (autorenew/monthly)'
    PREMIUM_2020 = 'AstroBin Premium 2020+'
    PREMIUM_2020_AUTORENEW_YEARLY = 'AstroBin Premium 2020+ (autorenew/yearly)'
    PREMIUM_2020_AUTORENEW_MONTHLY = 'AstroBin Premium 2020+ (autorenew/monthly)'
    ULTIMATE_2020 = 'AstroBin Ultimate 2020+'
    ULTIMATE_2020_AUTORENEW_YEARLY = 'AstroBin Ultimate 2020+ (autorenew/yearly)'
    ULTIMATE_2020_AUTORENEW_MONTHLY = 'AstroBin Ultimate 2020+ (autorenew/monthly)'

    # Deprecated since discounts happen via Stripe coupons
    PREMIUM_CLASSIC_20_PERCENT_DISCOUNT = 'AstroBin Premium 20% discount'
    PREMIUM_CLASSIC_30_PERCENT_DISCOUNT = 'AstroBin Premium 30% discount'
    PREMIUM_CLASSIC_40_PERCENT_DISCOUNT = 'AstroBin Premium 40% discount'
    PREMIUM_CLASSIC_50_PERCENT_DISCOUNT = 'AstroBin Premium 50% discount'


class SubscriptionDisplayName(Enum):
    LITE = 'Lite'
    PREMIUM = 'Premium'
    ULTIMATE = 'Ultimate'

    @classmethod
    def from_string(cls, value_str):
        for member in cls:
            if member.name.lower() == value_str.lower():
                return member
        raise ValueError(f"Invalid enum value: {value_str}")


def _compareValidity(a, b):
    return b.valid() - a.valid()


def _compareNames(a, b):
    """
    This function is used to determine the "weight" of each Premium subscription. When a user has multiple, only the
    heaviest one gets considered throughout the website.
    :param a: left operand.
    :param b: right operand.
    :return: a negative number if the left operand is heavier than thee left, 0 if equal, a positive number otherwise.
    """
    key = {
        SubscriptionName.LITE_CLASSIC_AUTORENEW.value: 1,
        SubscriptionName.LITE_CLASSIC.value: 1.1,
        SubscriptionName.LITE_2020.value: 1.2,
        SubscriptionName.LITE_2020_AUTORENEW_MONTHLY.value: 1.3,
        SubscriptionName.LITE_2020_AUTORENEW_YEARLY.value: 1.4,
        SubscriptionName.PREMIUM_CLASSIC_AUTORENEW.value: 2,
        SubscriptionName.PREMIUM_CLASSIC.value: 2.1,
        SubscriptionName.PREMIUM_CLASSIC_20_PERCENT_DISCOUNT.value: 2.2,
        SubscriptionName.PREMIUM_CLASSIC_30_PERCENT_DISCOUNT.value: 2.3,
        SubscriptionName.PREMIUM_CLASSIC_40_PERCENT_DISCOUNT.value: 2.4,
        SubscriptionName.PREMIUM_CLASSIC_50_PERCENT_DISCOUNT.value: 2.5,
        SubscriptionName.PREMIUM_2020.value: 2.6,
        SubscriptionName.PREMIUM_2020_AUTORENEW_MONTHLY.value: 2.7,
        SubscriptionName.PREMIUM_2020_AUTORENEW_YEARLY.value: 2.8,
        SubscriptionName.ULTIMATE_2020.value: 3,
        SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY.value: 3.1,
        SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY.value: 3.2,
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

        UserProfile.objects.filter(user=self.user).update(updated=timezone.now())

    def get_valid_usersubscription(self):
        if self.user is None or self.user.pk is None or not self.user.is_authenticated:
            return None

        cache_key = "astrobin_valid_usersubscription_%d" % self.user.pk

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        us = [obj for obj in UserSubscription.objects.filter(
            user__username=self.user.username,
            subscription__name__in=[x.value for x in SubscriptionName],
            expires__gte=datetime.today(),
            active=True,
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
    def allow_full_retailer_integration(
            viewer_user_subscription: Optional[UserSubscription],
            owner_user_subscription: Optional[UserSubscription]
    ) -> bool:
        if not settings.ADS_ENABLED:
            return False

        viewer_allows = \
            viewer_user_subscription is None or \
            PremiumService.is_free(viewer_user_subscription) or \
            PremiumService.is_lite_2020(viewer_user_subscription) or \
            (
                    (
                            PremiumService.is_lite(viewer_user_subscription) or
                            PremiumService.is_any_premium(viewer_user_subscription) or
                            PremiumService.is_any_ultimate(viewer_user_subscription)
                    ) and viewer_user_subscription.user.userprofile.allow_retailer_integration
            )

        owner_allows = \
            owner_user_subscription is None or \
            not PremiumService.is_any_ultimate(owner_user_subscription) or \
            (
                    PremiumService.is_any_ultimate(owner_user_subscription) and \
                    owner_user_subscription.user.userprofile.allow_retailer_integration
            )

        if not owner_allows:
            return False

        return viewer_allows

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
    
    def get_max_allowed_revisions(user_subscription: UserSubscription) -> int:
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

    @staticmethod
    def is_any_ultimate(user_subscription: UserSubscription) -> bool:
        return PremiumService.is_ultimate_2020(user_subscription)

    @staticmethod
    def is_ultimate_2020(user_subscription: UserSubscription) -> bool:
        if user_subscription:
            return user_subscription.subscription.group.name == "astrobin_ultimate_2020"
        return False

    @staticmethod
    def is_any_premium(user_subscription: UserSubscription) -> bool:
        return PremiumService.is_premium(user_subscription) | PremiumService.is_premium_2020(user_subscription)

    @staticmethod
    def is_premium_2020(user_subscription: UserSubscription) -> bool:
        if user_subscription:
            return user_subscription.subscription.group.name == "astrobin_premium_2020"
        return False

    @staticmethod
    def is_premium(user_subscription: UserSubscription) -> bool:
        if user_subscription:
            return user_subscription.subscription.group.name == "astrobin_premium"
        return False

    @staticmethod
    def is_any_lite(user_subscription: UserSubscription) -> bool:
        return PremiumService.is_lite(user_subscription) | PremiumService.is_lite_2020(user_subscription)

    @staticmethod
    def is_lite_2020(user_subscription: UserSubscription) -> bool:
        if user_subscription:
            return user_subscription.subscription.group.name == "astrobin_lite_2020"
        return False

    @staticmethod
    def is_lite(user_subscription: UserSubscription) -> bool:
        if user_subscription:
            return user_subscription.subscription.group.name == "astrobin_lite"
        return False

    @staticmethod
    def is_free(user_subscription: UserSubscription) -> bool:
        return not PremiumService.is_any_paid_subscription(user_subscription)

    @staticmethod
    def is_any_paid_subscription(user_subscription: UserSubscription) -> bool:
        return \
            PremiumService.is_lite(user_subscription) or \
            PremiumService.is_premium(user_subscription) or \
            PremiumService.is_lite_2020(user_subscription) or \
            PremiumService.is_premium_2020(user_subscription) or \
            PremiumService.is_ultimate_2020(user_subscription)

    @staticmethod
    def has_expired_paid_subscription(user: User) -> bool:
        cache_key = "has_an_expired_premium_subscription_%d" % user.pk

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        if PremiumService.is_any_paid_subscription(valid_subscription):
            result = False
        else:
            result = UserSubscription.objects.filter(
                user=user,
                expires__lt=DateTimeService.today(),
                subscription__category__contains="premium"
            ).exists()

        cache.set(cache_key, result, 300)

        return result

    @staticmethod
    def has_paid_subscription_near_expiration(user, days):
        cache_key = "has_premium_subscription_near_expiration_%d" % user.pk

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        if PremiumService.has_expired_paid_subscription(PremiumService(user).get_valid_usersubscription()):
            result = False
        else:
            result = UserSubscription.objects.filter(
                Q(user=user) &
                Q(active=True) &
                Q(expires__lt=DateTimeService.today() + timedelta(days)) &
                Q(expires__gt=DateTimeService.today()) &
                Q(subscription__category__contains="premium")
            ).exists()

        cache.set(cache_key, result, 300)
        return result

    @staticmethod
    def can_view_full_technical_card(user: User) -> bool:
        return True

    @staticmethod
    def can_view_technical_card_item(user: User, item) -> bool:
        if not item[1]:
            return False

        if isinstance(item[1], QuerySet):
            return len(item[1]) > 0

        return True

    @staticmethod
    def can_access_advanced_search(user_subscription: UserSubscription) -> bool:
        return not PremiumService.is_free(user_subscription)

    @staticmethod
    def can_access_full_search(user_subscription: UserSubscription) -> bool:
        # Pre 2020 Lite and Premium for continuity reasons
        return (
                PremiumService.is_lite(user_subscription) or
                PremiumService.is_premium(user_subscription) or
                PremiumService.is_any_ultimate(user_subscription)
        )

    @staticmethod
    def can_perform_basic_platesolving(user_subscription: UserSubscription) -> bool:
        return not PremiumService.is_free(user_subscription)

    @staticmethod
    def can_perform_advanced_platesolving(user_subscription: UserSubscription) -> bool:
        return PremiumService.is_any_ultimate(user_subscription)

    @staticmethod
    def can_see_real_resolution(user: User, image: Image) -> bool:
        if image.full_size_display_limitation == FullSizeDisplayLimitation.EVERYBODY:
            return True

        if image.full_size_display_limitation == FullSizeDisplayLimitation.PAYING_MEMBERS_ONLY:
            return not PremiumService.is_free(PremiumService(user).get_valid_usersubscription()) or user == image.user

        if image.full_size_display_limitation == FullSizeDisplayLimitation.MEMBERS_ONLY:
            return user.is_authenticated

        if image.full_size_display_limitation == FullSizeDisplayLimitation.ME_ONLY:
            return user == image.user

        return False

    @staticmethod
    def can_restore_from_trash(user_subscription: UserSubscription) -> bool:
        return PremiumService.is_any_ultimate(user_subscription)

    @staticmethod
    def can_remove_ads(user_subscription: UserSubscription) -> bool:
        if not settings.ADS_ENABLED:
            return False

        return (
                PremiumService.is_lite(user_subscription) or
                PremiumService.is_any_premium(user_subscription) or
                PremiumService.is_any_ultimate(user_subscription)
        )

    @staticmethod
    def can_remove_retailer_integration(user_subscription: UserSubscription) -> bool:
        return (
                PremiumService.is_lite(user_subscription) or
                PremiumService.is_any_premium(user_subscription) or
                PremiumService.is_any_ultimate(user_subscription)
        )

    @staticmethod
    def can_upload_uncompressed_source(user_subscription: UserSubscription) -> bool:
        return PremiumService.is_any_ultimate(user_subscription)

    @staticmethod
    def can_download_data(user_subscription: UserSubscription) -> bool:
        # This refers to bulk data export.
        return PremiumService.is_any_premium(user_subscription) or PremiumService.is_any_ultimate(user_subscription)
