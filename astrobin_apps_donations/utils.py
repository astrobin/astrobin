from subscription.models import UserSubscription

def user_is_donor(user):
    if user.is_authenticated:
        return UserSubscription.objects.filter(user = user, subscription__name = 'AstroBin Donor').count() > 0
    return False

