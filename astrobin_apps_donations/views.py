# Django
from django.conf import settings
from django.views.generic import TemplateView

# Third party
from subscription.models import Subscription


class CancelView(TemplateView):
    template_name = 'astrobin_apps_donations/cancel.html'


class SuccessView(TemplateView):
    template_name = 'astrobin_apps_donations/success.html'


class EditView(TemplateView):
    template_name = 'astrobin_apps_donations/edit.html'

    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)

        context['base_url'] = settings.BASE_URL
        context['business'] = settings.SUBSCRIPTION_PAYPAL_SETTINGS['business']

        context['monthly_coffee_sub'] = Subscription.objects.get(name='AstroBin Donor Coffee Monthly')
        context['monthly_snack_sub'] = Subscription.objects.get(name='AstroBin Donor Snack Monthly')
        context['monthly_pizza_sub'] = Subscription.objects.get(name='AstroBin Donor Pizza Monthly')
        context['monthly_movie_sub'] = Subscription.objects.get(name='AstroBin Donor Movie Monthly')
        context['monthly_dinner_sub'] = Subscription.objects.get(name='AstroBin Donor Dinner Monthly')

        context['yearly_coffee_sub'] = Subscription.objects.get(name='AstroBin Donor Coffee Yearly')
        context['yearly_snack_sub'] = Subscription.objects.get(name='AstroBin Donor Snack Yearly')
        context['yearly_pizza_sub'] = Subscription.objects.get(name='AstroBin Donor Pizza Yearly')
        context['yearly_movie_sub'] = Subscription.objects.get(name='AstroBin Donor Movie Yearly')
        context['yearly_dinner_sub'] = Subscription.objects.get(name='AstroBin Donor Dinner Yearly')

        return context
