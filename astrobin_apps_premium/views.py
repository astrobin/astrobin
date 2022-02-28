import logging
from datetime import date, timedelta

from annoying.functions import get_object_or_None
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic.edit import FormView, CreateView
from subscription.models import Transaction, Subscription, UserSubscription

import astrobin_apps_premium.services.premium_service
from . import utils as premium_utils
from astrobin_apps_donations import utils as donation_utils
from .forms import MigrateDonationsForm

log = logging.getLogger('apps')


class MigrateDonationsView(FormView):
    template_name = "astrobin_apps_premium/migrate_donations.html"
    form_class = MigrateDonationsForm

    def get_premium_sub(self):
        try:
            return Subscription.objects.get(name="AstroBin Premium")
        except Subscription.DoesNotExist:
            return None

    def get_success_url(self):
        return reverse("astrobin_apps_premium.migrate_donations_success")

    def get_migration_data(self):
        amount = 0
        first_payment = None
        days_paid = 0
        expiration = None
        migration_impossible = False
        migration_impossible_reason = None

        premium_sub = self.get_premium_sub()
        if premium_sub is None:
            migration_impossible = True
            migration_impossible_reason = "MISSING_SUBSCRIPTION"
        else:
            try:
                us = UserSubscription.objects.get(
                    user=self.request.user,
                    subscription__name__in=astrobin_apps_premium.services.premium_service.SUBSCRIPTION_NAMES
                )
            except UserSubscription.DoesNotExist:
                us = None

            transactions = Transaction.objects.filter(
                user=self.request.user,
                subscription__name__in=list(donation_utils.SUBSCRIPTION_NAMES) + ['AstroBin Donor'],
                event__in=["subscription payment", "incorrect payment"],
                timestamp__gte="2015-01-01 00:00").order_by('-timestamp')

            for t in transactions:
                first_payment = t.timestamp
                amount += t.amount

            if amount > 0:
                days_paid = int(float(amount) / float(premium_sub.price) * 365.2425)
                expiration = (first_payment + timedelta(days_paid)).date()

            if us is not None and us.active and us.expires >= date.today():
                migration_impossible = True
                migration_impossible_reason = "ALREADY_PREMIUM"
            elif transactions.count() == 0:
                migration_impossible = True
                migration_impossible_reason = "NO_PAYMENTS"
            elif expiration < date.today():
                migration_impossible = True
                migration_impossible_reason = "PAST_EXPIRATION"

        return {
            "migration_impossible": migration_impossible,
            "migration_impossible_reason": migration_impossible_reason,
            "transactions": transactions,
            "amount_donated": amount,
            "first_payment": first_payment,
            "price": premium_sub.price,
            "days_paid": days_paid,
            "expiration": expiration,
        }

    def get_context_data(self, **kwargs):
        context = super(MigrateDonationsView, self).get_context_data(**kwargs)
        context["migration_data"] = self.get_migration_data()
        return context

    def form_valid(self, form):
        migration_data = self.get_migration_data()
        if migration_data["migration_impossible"]:
            return HttpResponseForbidden()

        premium_sub = self.get_premium_sub()
        if premium_sub is None:
            return HttpResponseForbidden()

        us, created = UserSubscription.objects.get_or_create(
            user=self.request.user,
            subscription=premium_sub)
        us.active = True
        us.expires = migration_data["expiration"]
        us.cancelled = True
        us.save()
        us.fix()

        return super(MigrateDonationsView, self).form_valid(form)
