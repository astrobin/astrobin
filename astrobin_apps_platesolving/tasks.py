import logging
from datetime import timedelta
from typing import Union

from annoying.functions import get_object_or_None
from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone
from subscription.models import UserSubscription

from astrobin.models import Image, ImageRevision
from astrobin_apps_images.services import ImageService
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.services import SolutionService
from astrobin_apps_platesolving.solver import Solver, SolverBase
from astrobin_apps_platesolving.utils import get_target
from astrobin_apps_premium.services.premium_service import PremiumService

logger = logging.getLogger(__name__)


def get_target_image_id_and_label(target: Union[Image, ImageRevision]) -> (Union[str, int], str):
    if target.__class__.__name__ == 'Image':
        image_id = target.hash or target.pk
        revision_label = '0'
    else:
        image_id = target.image.hash or target.image.pk
        revision_label = target.label

    return image_id, revision_label


@shared_task(time_limit=120)
def reset_solution_status_after_timeout():
    affected_rows = Solution.objects\
        .filter(status=Solver.ADVANCED_PENDING, created__lt=timezone.now() - timedelta(hours=3))\
        .update(status=Solver.SUCCESS)

    logger.info("reset_solution_status_after_timeout: %d solutions reset to the basic SUCCESS status" % affected_rows)


@shared_task(time_limit=300, acks_late=True)
def start_basic_solver(object_id: int, content_type_id: int):
    target = get_target(object_id, content_type_id)
    if target is None:
        logger.error(f'start_basic_solver: returning because target not found for {object_id}/{content_type_id}')
        return

    solution: Solution = SolutionService.get_or_create_solution(target)
    image: Image = SolutionService(solution).get_target_image()
    user: User = image.user

    if not ImageService(image).is_platesolvable():
        logger.debug(f'start_basic_solver: returning because image {image.hash or image.pk} is not platesolvable')
        return

    valid_subscription: UserSubscription = PremiumService(user).get_valid_usersubscription()
    if not PremiumService.can_perform_basic_platesolving(valid_subscription):
        logger.debug(
            f'start_basic_solver: returning because user {user.pk}/{user.username} cannot perform basic platesolving'
        )
        return

    if solution.status != Solver.MISSING:
        logger.debug(f'start_basic_solver: returning because solution {solution.pk} is in status {solution.status}')
        return

    SolutionService(solution).start_basic_solver()

    image_id: Union[str, int]
    revision_label: str
    image_id, revision_label = get_target_image_id_and_label(target)

    logger.debug(f'start_basic_solver: {solution.pk} for {image_id}/{revision_label}')

    check_basic_solver_status.apply_async(args=(solution.pk,), countdown=30)


@shared_task(time_limit=60)
def check_basic_solver_status(solution_id: int):
    solution: Solution = get_object_or_None(Solution, pk=solution_id)
    if solution is None:
        logger.error(f'check_basic_solver_status: returning because solution {solution_id} not found')
        return

    status: int = SolutionService(solution).update_solver_status()
    image_id: Union[str, int]
    revision_label: str
    image_id, revision_label = get_target_image_id_and_label(solution.content_object)
    logger.debug(
        f'check_basic_solver_status: {solution_id} for {image_id}/{revision_label} - '
        f'{SolverBase().get_status_name(status)}'
    )

    if status == Solver.PENDING:
        check_basic_solver_status.apply_async((solution_id,), countdown=30)
    elif status in (Solver.MISSING, Solver.FAILED):
        Solution.objects.filter(pk=solution_id).update(status=Solver.MISSING)
        if solution.attempts < 3:
            start_basic_solver.delay(solution.content_object.pk, solution.content_type_id)
    elif status == Solver.SUCCESS:
        finalize_basic_solver.delay(solution_id)


@shared_task(time_limie=300, acks_late=True)
def finalize_basic_solver(solution_id: int):
    solution: Solution = get_object_or_None(Solution, pk=solution_id)
    if solution is None:
        logger.error(f'finalize_basic_solver: returning because solution {solution_id} not found')
        return

    SolutionService(solution).finalize_basic_solver()
    image_id: Union[str, int]
    revision_label: str
    image_id, revision_label = get_target_image_id_and_label(solution.content_object)
    logger.debug(f'finalize_basic_solver: {solution_id} for {image_id}/{revision_label}')

    start_advanced_solver.delay(solution_id)


@shared_task(time_limit=300)
def start_advanced_solver(solution_id: int):
    solution: Solution = get_object_or_None(Solution, pk=solution_id)
    if solution is None:
        logger.error(f'start_advanced_solver: returning because solution {solution_id} not found')
        return

    if solution.status != Solver.SUCCESS:
        logger.debug(f'start_advanced_solver: returning because solution {solution_id} is not in Solver.SUCCESS status')
        return

    image: Image = SolutionService(solution).get_target_image()
    user: User = image.user

    valid_subscription: UserSubscription = PremiumService(user).get_valid_usersubscription()
    if not PremiumService.can_perform_advanced_platesolving(valid_subscription):
        logger.debug(
            f'start_advanced_solver: returning because user {user.pk}/{user.username} cannot perform advanced '
            f'platesolving'
        )
        return

    image_id: Union[str, int]
    revision_label: str
    image_id, revision_label = get_target_image_id_and_label(solution.content_object)
    SolutionService(solution).start_advanced_solver()
    logger.debug(f'start_advanced_solver: {solution_id} for {image_id}/{revision_label}')
