from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


# Class to permit the authentication using email or username
class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        try:
            users = UserModel.objects.filter(
                Q(username__iexact=username) |
                Q(email__iexact=username)
            ).distinct()
        except UserModel.DoesNotExist:
            return None

        if users.exists():
            user_obj = users.first()
            if user_obj.check_password(password):
                return user_obj
            return None
        else:
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
