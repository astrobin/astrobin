from rest_framework import throttling


class EquipmentCreateThrottle(throttling.UserRateThrottle):
    rate = '10/day'

    def allow_request(self, request, view):
        if request.method == "POST":
            return super().allow_request(request, view)

        return True
