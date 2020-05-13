from django.core.management.base import BaseCommand

from datetime import date, timedelta

from paypal.standard.ipn import models
from subscription.models import Subscription, UserSubscription, Transaction


class Command(BaseCommand):
    def __init__(self):
        self.premium_subscription = Subscription.objects.get(name = 'AstroBin Premium')

    def process_user(self, user, amount, first_payment):
        price = 36.0
        days_paid = int(float(amount)/price * 365.25)
        expires = (first_payment + timedelta(days_paid)).date()

        if expires > date.today():
            us, created = UserSubscription.objects.get_or_create(
                user = user,
                subscription = self.premium_subscription,
                expires = expires,
                cancelled = False)
            us.fix()

            print "%.2f \t %d \t %s \t %s \t\t %s <%s>" % (
                amount,
                days_paid,
                first_payment.strftime('%b, %d'),
                expires.strftime('%b, %d %Y'),
                user,
                user.email)

    def handle(self, *args, **options):
        SUBSCRIPTION_NAMES = (
            'AstroBin Donor',
            'AstroBin Donor Coffee Monthly',
            'AstroBin Donor Snack Monthly',
            'AstroBin Donor Pizza Monthly',
            'AstroBin Donor Movie Monthly',
            'AstroBin Donor Dinner Monthly',

            'AstroBin Donor Coffee Yearly',
            'AstroBin Donor Snack Yearly',
            'AstroBin Donor Pizza Yearly',
            'AstroBin Donor Movie Yearly',
            'AstroBin Donor Dinner Yearly',
        )

        """
        {
            <user>: {
                amount: 100,
                first_payment: 1234567890.0
            }
        }
        """
        data = dict()
        for transaction in Transaction.objects.filter(
                subscription__name__in = SUBSCRIPTION_NAMES,
                event = "subscription payment",
                timestamp__year = date.today().year).order_by('timestamp'):

            if transaction.user not in data:
                data[transaction.user] = {
                    "amount": transaction.amount,
                    "first_payment": transaction.timestamp
                }
            else:
                data[transaction.user]["amount"] += transaction.amount

        for user, values in data.iteritems():
            amount = values["amount"]
            first_payment = values["first_payment"]
            self.process_user(user, amount, first_payment)
