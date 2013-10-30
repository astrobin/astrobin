# Django
from django.contrib import auth
from django.db import models

# Third party
from paypal.standard import ipn
from paypal.standard.ipn.models import PayPalIPN

class RecurringDonation(models.Model):
    payment = models.ForeignKey(PayPalIPN)
    user = models.OneToOneField(auth.models.User)
    amount = models.DecimalField(max_digits=64, decimal_places=2)
    active = models.BooleanField(default = False)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ('-timestamp',)


# PayPal IPN signals

def handle_payment_was_successful(sender, **kwargs):
    payment = sender
    user = auth.models.User.objects.get(pk = payment.custom)
    amount = payment.mc_gross

    donation, created = RecurringDonation.objects.get_or_create(user = user)

    if created:
        donation.payment = payment
        donation.amount = amount
        donation.active = True
        donation.save()


def handle_payment_was_canceled(sender, **kwargs):
    payment = sender
    user = auth.models.User.objects.get(pk = payment.custom)

    donation, created = RecurringDonation.objects.get_or_create(user = user)
    if not created:
        donation.active = False
        donation.save()


# Signup/success
ipn.signals.subscription_signup.connect(handle_payment_was_successful)
ipn.signals.payment_was_successful.connect(handle_payment_was_successful)

# Cancelled/flagged/eor
ipn.signals.subscription_cancel.connect(handle_payment_was_canceled)
ipn.signals.payment_was_flagged.connect(handle_payment_was_canceled)
ipn.signals.subscription_eot.connect(handle_payment_was_canceled)

