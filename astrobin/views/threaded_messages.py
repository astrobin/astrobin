from django.contrib.auth.decorators import login_required
from threaded_messages.views import compose

from astrobin.forms.private_message_form import PrivateMessageForm, PrivateMessageFormWithCaptcha
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free


@login_required
def messages_compose(
        request,
        recipient=None,
        form_class=None,
        template_name='messages/compose.html',
        success_url=None,
        recipient_filter=None):
    if not form_class:
        valid_subscription = PremiumService(request.user).get_valid_usersubscription()
        if is_free(valid_subscription):
            form_class = PrivateMessageFormWithCaptcha
        else:
            form_class = PrivateMessageForm

    return compose(request, recipient, form_class, template_name, success_url, recipient_filter)
