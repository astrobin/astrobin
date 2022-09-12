from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache


class SearchIndexUpdateService:
    @staticmethod
    def update_index(instance, max_frequency=10):
        from astrobin.tasks import update_index

        content_type = ContentType.objects.get_for_model(instance)

        cache_key = f'astrobin_common_search_index_update_service_{content_type.pk}_{instance.pk}'

        if cache.get(cache_key):
            return

        # Delay by a few seconds so that the instance will have time to process all the m2m stages.
        update_index.apply_async(args=(content_type.pk, instance.pk), countdown=30)

        # Don't update an item more frequently than once in `max_frequency` seconds.
        cache.set(cache_key, '1', max_frequency)
