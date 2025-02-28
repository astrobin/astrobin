from collections import Counter

from avatar.templatetags.avatar_tags import avatar_url
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
        contributors_data = cache.get(cache_key)

        if contributors_data is None:
            # Define all equipment classes
            equipment_classes = [
                EquipmentItemKlass.TELESCOPE,
                EquipmentItemKlass.CAMERA,
                EquipmentItemKlass.MOUNT,
                EquipmentItemKlass.FILTER,
                EquipmentItemKlass.ACCESSORY,
                EquipmentItemKlass.SOFTWARE
            ]
            
            # Get users excluding superusers
            users = User.objects.exclude(is_superuser=True).select_related('userprofile')
            
            # Create a Counter object to aggregate all contributions
            counter = Counter()
            
            # For each equipment class, get the contributions and add them to the counter
            for klass in equipment_classes:
                created_field = f'astrobin_apps_equipment_{klass.lower()}editproposals_created'
                reviewed_field = f'astrobin_apps_equipment_{klass.lower()}editproposals_reviewed'
                
                created_counts = dict(
                    users.annotate(count=Count(created_field, distinct=True))
                    .filter(count__gt=0)
                    .values_list('id', 'count')
                )
                
                reviewed_counts = dict(
                    users.annotate(count=Count(reviewed_field, distinct=True))
                    .filter(count__gt=0)
                    .values_list('id', 'count')
                )
                
                # Add to counter
                for user_id, count in created_counts.items():
                    counter[user_id] += count
                    
                for user_id, count in reviewed_counts.items():
                    counter[user_id] += count
            
            # Get top 50 contributors with additional information
            top_contributors = counter.most_common(50)
            
            # Fetch additional data for each contributor
            user_ids = [user_id for user_id, _ in top_contributors]
            users_dict = {
                user.id: user for user in User.objects.filter(id__in=user_ids).select_related('userprofile')
            }
            
            contributors_data = []
            for user_id, count in top_contributors:
                user = users_dict.get(user_id)
                if user:
                    # Get display name based on real_name or username
                    display_name = user.userprofile.get_display_name()
                    
                    contributors_data.append([
                        user_id,
                        count,
                        user.username,
                        display_name,
                        avatar_url(user, 200)
                    ])
            
            cache.set(cache_key, contributors_data, 60 * 60)

        return Response(contributors_data)
