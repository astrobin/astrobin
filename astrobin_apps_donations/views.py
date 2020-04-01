from annoying.functions import get_object_or_None
from django.conf import settings
from django.views.generic import TemplateView

from subscription.models import Subscription


def _context():
    return {
        'business': settings.SUBSCRIPTION_PAYPAL_SETTINGS['business'],

        'monthly_bronze_sub': get_object_or_None(Subscription, name='AstroBin Donor Bronze Monthly'),
        'monthly_silver_sub': get_object_or_None(Subscription, name='AstroBin Donor Silver Monthly'),
        'monthly_gold_sub': get_object_or_None(Subscription, name='AstroBin Donor Gold Monthly'),
        'monthly_platinum_sub': get_object_or_None(Subscription, name='AstroBin Donor Platinum Monthly'),

        'yearly_bronze_sub': get_object_or_None(Subscription, name='AstroBin Donor Bronze Yearly'),
        'yearly_silver_sub': get_object_or_None(Subscription, name='AstroBin Donor Silver Yearly'),
        'yearly_gold_sub': get_object_or_None(Subscription, name='AstroBin Donor Gold Yearly'),
        'yearly_platinum_sub': get_object_or_None(Subscription, name='AstroBin Donor Platinum Yearly'),
    }


class DonateView(TemplateView):
    template_name = 'astrobin_apps_donations/donate.html'

    def get_context_data(self, **kwargs):
        context = super(DonateView, self).get_context_data(**kwargs)
        context.update(_context())
        context.update({'request': self.request})
        return context


class CancelView(TemplateView):
    template_name = 'astrobin_apps_donations/cancel.html'


class SuccessView(TemplateView):
    template_name = 'astrobin_apps_donations/success.html'


class EditView(TemplateView):
    template_name = 'astrobin_apps_donations/edit.html'

    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)
        context.update(_context())
        context.update({'request': self.request})
        return context
