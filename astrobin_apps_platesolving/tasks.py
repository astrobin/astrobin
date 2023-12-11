import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.solver import Solver

logger = logging.getLogger(__name__)


@shared_task(time_limit=120)
def reset_solution_status_after_timeout():
    affected_rows = Solution.objects\
        .filter(status=Solver.ADVANCED_PENDING, created__lt=timezone.now() - timedelta(hours=3))\
        .update(status=Solver.SUCCESS)

    logger.info("reset_solution_status_after_timeout: %d solutions reset to the basic SUCCESS status" % affected_rows)
