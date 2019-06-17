from django.core.management.base import BaseCommand

from subscription.models import UserSubscription


class Command(BaseCommand):
    def handle(self, *args, **options):
        for us in UserSubscription.objects.filter(subscription__name='AstroBin Lite'):
            profile = us.user.userprofile
            print "Processing user: %s" % profile
            profile.premium_counter = 0
            profile.save()
