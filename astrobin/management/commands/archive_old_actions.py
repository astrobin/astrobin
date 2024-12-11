import logging
from datetime import timedelta
from functools import reduce
from operator import and_

from actstream.models import Action
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from astrobin.models import ActionArchive

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Archives actions older than 6 months'

    def action_exists_in_archive(self, action) -> bool:
        # Create a Q object for each field to compare
        conditions = [
            Q(actor_content_type=action.actor_content_type),
            Q(actor_object_id=action.actor_object_id),
            Q(verb=action.verb),
            Q(description=action.description),
            Q(target_content_type=action.target_content_type),
            Q(target_object_id=action.target_object_id),
            Q(action_object_content_type=action.action_object_content_type),
            Q(action_object_object_id=action.action_object_object_id),
            Q(timestamp=action.timestamp),
            Q(public=action.public)
        ]

        # Combine all conditions with AND
        query = reduce(and_, conditions)

        return ActionArchive.objects.filter(query).exists()

    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=90)

        with transaction.atomic():
            # Get old actions
            old_actions = Action.objects.filter(timestamp__lt=cutoff_date)
            count = old_actions.count()

            log.info(f'Found {count} actions to archive')

            # Track statistics
            archived_count = 0
            skipped_count = 0

            # Create archive records
            archived = []
            for action in old_actions.iterator():
                if not self.action_exists_in_archive(action):
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
                    archived_count += 1
                else:
                    skipped_count += 1

                # Bulk create in batches to manage memory
                if len(archived) >= 1000:
                    ActionArchive.objects.bulk_create(archived)
                    archived = []
                    log.info(f'Archived batch of 1000 actions')

            # Create any remaining records
            if archived:
                ActionArchive.objects.bulk_create(archived)
                log.info(f'Archived final batch of {len(archived)} actions')

            # Delete old actions that were successfully archived
            old_actions.delete()

            log.info(
                f'Archive complete: {archived_count} actions archived, '
                f'{skipped_count} actions skipped (already in archive)'
            )
