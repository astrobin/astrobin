from rest_framework import throttling


class AuthTokenThrottle(throttling.UserRateThrottle):
    rate = '1/minute'
