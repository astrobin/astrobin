import logging

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from actstream.models import Action
from astrobin.models import ActionArchive

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Archives actions older than 3 months'

    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=90)

        with transaction.atomic():
            # Get old actions
            old_actions = Action.objects.filter(timestamp__lt=cutoff_date)
            count = old_actions.count()

            log.debug(f'Found {count} actions to archive...')

            # Create archive records
            archived = []
            for action in old_actions.iterator():
                archived.append(
                    ActionArchive(
                        actor_content_type=action.actor_content_type,
                        actor_object_id=action.actor_object_id,
                        verb=action.verb,
                        description=action.description,
                        target_content_type=action.target_content_type,
                        target_object_id=action.target_object_id,
                        action_object_content_type=action.action_object_content_type,
                        action_object_object_id=action.action_object_object_id,
                        timestamp=action.timestamp,
                        public=action.public
                    )
                )

                # Bulk create in batches to manage memory
                if len(archived) >= 1000:
                    ActionArchive.objects.bulk_create(archived)
                    archived = []

            # Create any remaining records
            if archived:
                ActionArchive.objects.bulk_create(archived)

            # Delete old actions
            old_actions.delete()

            log.debug(f'Successfully archived {count} actions')
