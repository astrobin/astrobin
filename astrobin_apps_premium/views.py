import logging
from datetime import date, timedelta

from annoying.functions import get_object_or_None
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic.edit import FormView, CreateView
from subscription.models import Transaction, Subscription, UserSubscription

import utils as premium_utils
from astrobin_apps_donations import utils as donation_utils
from astrobin_apps_premium.models import DataLossCompensationRequest
from forms import MigrateDonationsForm, DataLossCompensationRequestForm

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
                    subscription__name__in=premium_utils.SUBSCRIPTION_NAMES)
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
                days_paid = int(float(amount) / float(premium_sub.price) * 365.25)
                expiration = (first_payment + timedelta(days_paid)).date()

            if us is not None and us.valid():
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


class DataLossCompensationRequestView(CreateView):
    template_name = 'astrobin_apps_premium/data_loss_compensation_request.html'
    form_class = DataLossCompensationRequestForm

    def get_ultimate_subscription(self):
        # type: () -> Optional(Subscription)
        try:
            return Subscription.objects.get(name='AstroBin Ultimate 2020+')
        except Subscription.DoesNotExist:
            return None


    def get_success_url(self):
        # type: () -> str
        return reverse('astrobin_apps_premium.data_loss_compensation_request_success')

    def dispatch(self, request, *args, **kwargs):
        compensation_request = get_object_or_None(DataLossCompensationRequest, user=request.user)

        if compensation_request is not None:
            log.debug("User %d attempted data loss compensation request again" % self.request.user.pk)
            return redirect(reverse('astrobin_apps_premium.data_loss_compensation_request_already_done'))

        usersubscription = get_object_or_None(
            UserSubscription,
            user__pk=request.user.pk,
            subscription__name__in=('AstroBin Premium', 'AstroBin Premium (autorenew)'),
            expires__gte=date(2020, 2, 15)
        )

        if usersubscription is None or usersubscription.expires == date(2021, 2, 20):
            log.debug("User %d attempted data loss compensation but is not eligible" % self.request.user.pk)
            return redirect(reverse('astrobin_apps_premium.data_loss_compensation_request_not_eligible'))

        return super(DataLossCompensationRequestView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        requested_compensation = form.cleaned_data['requested_compensation']

        log.debug("User %d requested data loss compensation: %s" % (self.request.user.pk, requested_compensation))

        if requested_compensation not in ('NOT_AFFECTED', 'NOT_REQUIRED'):
            ultimate_subscription = self.get_ultimate_subscription()

            premium_user_subscriptions = UserSubscription.objects.filter(
                user__pk=self.request.user.pk,
                subscription__name__in=('AstroBin Premium', 'AstroBin Premium (autorenew)'),
                active=True)

            ultimate_user_subscription, created = UserSubscription.objects.get_or_create(
                user=self.request.user,
                subscription=ultimate_subscription)

            expires = date.today()

            if created:
                log.debug("UserSubscription %d created" % ultimate_user_subscription.pk)

                for premium_user_subscription in premium_user_subscriptions:
                    premium_user_subscription.active = False
                    premium_user_subscription.unsubscribe()
                    premium_user_subscription.save()
            else:
                log.debug("UserSubscription %d already exists" % ultimate_user_subscription.pk)

                expires = ultimate_user_subscription.expires

            if requested_compensation == '1_MO_ULTIMATE':
                expires += timedelta(days=30)
            if requested_compensation == '3_MO_ULTIMATE':
                expires += timedelta(days=90)
            elif requested_compensation == '6_MO_ULTIMATE':
                expires += timedelta(days=180)

            ultimate_user_subscription.active = True
            ultimate_user_subscription.expires = expires
            ultimate_user_subscription.cancelled = True
            ultimate_user_subscription.subscribe()
            ultimate_user_subscription.save()

        return super(DataLossCompensationRequestView, self).form_valid(form)
