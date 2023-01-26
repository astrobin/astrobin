from rest_framework.authtoken.views import ObtainAuthToken

from astrobin.api2.throttle import AuthTokenThrottle


class CustomAuthTokenView(ObtainAuthToken):
    throttle_classes = (AuthTokenThrottle,)
