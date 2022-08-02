from django.apps import apps
from django.core.cache import cache


class SearchIndexUpdateService:
    @staticmethod
    def update_index(model_class, instance):
        signal_processor = apps.get_app_config('haystack').signal_processor
        cache_key = f'astrobin_common_search_index_update_service_{model_class.__name__}_{instance.pk}'

        if cache.get(cache_key):
            return

        signal_processor.enqueue_save(model_class, instance)

        # Don't update an item more frequently than once in 10 seconds.
        cache.set(cache_key, '1', 10)
