from rest_framework import throttling


class EquipmentCreateThrottle(throttling.UserRateThrottle):
    rate = '10/day'

    def allow_request(self, request, view):
        if request.method != "POST" or request.user.is_superuser:
                return True

        return super().allow_request(request, view)
