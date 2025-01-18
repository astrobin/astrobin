from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from haystack.query import SearchQuerySet
from datetime import timedelta
import re

from astrobin.models import Image
from astrobin.search_indexes import ImageIndex

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Removes deleted images from the search index, optionally filtering by deletion time'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually removing images from the index',
        )
        parser.add_argument(
            '--time-limit',
            type=str,
            help='Only process images deleted within this time period (e.g. 24h or 30d)',
        )

    def parse_time_limit(self, time_limit):
        if not time_limit:
            return None

        match = re.match(r'^(\d+)(h|d)$', time_limit)
        if not match:
            raise CommandError('Time limit must be specified in hours (h) or days (d), e.g. 24h or 30d')

        value = int(match.group(1))
        unit = match.group(2)

        if unit == 'h':
            return timezone.now() - timedelta(hours=value)
        else:  # unit == 'd'
            return timezone.now() - timedelta(days=value)

    def handle(self, *args, **options):
        time_threshold = self.parse_time_limit(options.get('time_limit'))

        deleted_images = Image.deleted_objects.all()
        if time_threshold:
            deleted_images = deleted_images.filter(deleted__gte=time_threshold)

        count = deleted_images.count()
        processed = 0
        start_time = timezone.now()

        time_info = f" deleted after {time_threshold}" if time_threshold else ""
        logger.info("Found %d deleted images%s", count, time_info)
        self.stdout.write(f"Found {count} deleted images{time_info}")

        try:
            for image in deleted_images.iterator():
                exists_in_search_index = SearchQuerySet().models(Image).filter(object_id=image.pk).count() > 0
                if exists_in_search_index:
                    progress = (processed / float(count) * 100) if count > 0 else 0
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
