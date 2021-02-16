from django.core.cache import cache


class PremiumService:
    @staticmethod
    def clear_subscription_status_cache_keys(user_pk):
        cache.delete("has_an_expired_premium_subscription_%d" % user_pk)
        cache.delete("has_premium_subscription_near_expiration_%d" % user_pk)
        cache.delete("astrobin_is_donor_%d" % user_pk)
        cache.delete("astrobin_valid_usersubscription_%d" % user_pk)
