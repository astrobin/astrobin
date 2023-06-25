from django.core.management.base import BaseCommand

from paypal.standard.ipn import models
from subscription.models import UserSubscription

from astrobin_apps_premium.services.premium_service import SubscriptionName


class Command(BaseCommand):
    def handle(self, *args, **options):
        for us in UserSubscription.objects.filter(subscription__name=SubscriptionName.LITE_CLASSIC.value):
            profile = us.user.userprofile
            print("Processing user: %s" % profile)
            profile.premium_counter = 0
            profile.save(keep_deleted=True)
