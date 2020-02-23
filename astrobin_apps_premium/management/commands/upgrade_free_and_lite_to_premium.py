from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from subscription.models import UserSubscription, Subscription

from astrobin.models import UserProfile


class Command(BaseCommand):
    help = "Upgrade Free and Lite/Lite Autorenew accounts to Premium for 1 year."

    def upgrade(self, user):
        # type: (User) -> None
        premium = Subscription.objects.get(name="AstroBin Premium")
        user_subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            subscription=premium)
        user_subscription.active = True
        user_subscription.expires = date.today() + relativedelta(years=1)
        user_subscription.save()
        user_subscription.subscribe()

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Does not actually upgrade accounts, only prints totals',
        )

    def handle(self, *args, **options):
        user_profiles = UserProfile.objects.filter(user__date_joined__lte=date(2020, 2, 15))
        count = 0
        for user_profile in user_profiles:
            if user_profile.user.image_set.count() == 0:
                continue

            user_subscriptions = UserSubscription.objects.filter(user=user_profile.user)
            has_active_premium = False

            for user_subscription in user_subscriptions:
                if "Premium" in user_subscription.subscription.name and \
                        user_subscription.valid() and \
                        user_subscription.active:
                    has_active_premium = True

            if not has_active_premium:
                if not options.get('dry_run'):
                    self.upgrade(user_profile.user)
                count += 1

        if options.get('dry_run'):
            print "Would have upgraded %d accounts." % count
        else:
            print "Upgraded %d accounts." % count
