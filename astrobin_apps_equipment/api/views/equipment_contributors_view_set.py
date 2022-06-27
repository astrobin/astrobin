from collections import Counter

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass


class EquipmentContributorsViewSet(views.APIView):
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        cache_key = 'astrobin_apps_equipment_contributors'
        contributors = cache.get(cache_key)

        if contributors is None:
            contributions = [
                User.objects.annotate(
                    contributions= \
                        Count(f'astrobin_apps_equipment_{klass.lower()}editproposals_created', distinct=True) +
                        Count(f'astrobin_apps_equipment_{klass.lower()}editproposals_reviewed', distinct=True)
                ).filter(
                    contributions__gt=0
                ).exclude(
                    is_superuser=True
                ).order_by(
                    '-contributions'
                ).values_list(
                    'id', 'contributions'
                ) \
                for klass in [
                    EquipmentItemKlass.TELESCOPE,
                    EquipmentItemKlass.CAMERA,
                    EquipmentItemKlass.MOUNT,
                    EquipmentItemKlass.FILTER,
                    EquipmentItemKlass.ACCESSORY,
                    EquipmentItemKlass.SOFTWARE
                ]
            ]

            counter = sum(map(lambda l: Counter(dict(l)), contributions), Counter())
            contributors = counter.most_common(50)
            cache.set(cache_key, contributors, 60 * 60)

        return Response(contributors)
