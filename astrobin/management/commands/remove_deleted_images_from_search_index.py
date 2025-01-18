from django.core.management.base import BaseCommand
from django.utils import timezone
from haystack.query import SearchQuerySet

from astrobin.models import Image
from astrobin.search_indexes import ImageIndex

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Removes deleted images from the search index'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually removing images from the index',
        )

    def handle(self, *args, **options):
        deleted_images = Image.deleted_objects.all()
        count = deleted_images.count()
        processed = 0
        start_time = timezone.now()

        logger.info("Found %d deleted images", count)
        self.stdout.write(f"Found {count} deleted images")

        try:
            for image in deleted_images.iterator():
                exists_in_search_index = SearchQuerySet().models(Image).filter(object_id=image.pk).count() > 0
                if exists_in_search_index:
                    progress = (processed / float(count) * 100)
                    logger.debug("%d%%: removing image %d from search index", progress, image.pk)

                    if not options['dry_run']:
                        ImageIndex().remove_object(image)

                processed += 1

                if processed % 1000 == 0:
                    self.stdout.write(f"Processed {processed}/{count} images ({progress:.1f}%)")

        except Exception as e:
            logger.error("Error processing images: %s", str(e))
            raise

        finally:
            end_time = timezone.now()
            duration = end_time - start_time
            logger.info("Processed %d images in %s", count, duration)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Processed {count} images in {duration}"
                )
            )
