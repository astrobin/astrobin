from celery import shared_task

from astrobin_apps_iotd.services import IotdService


@shared_task()
def update_top_pick_nomination_archive():
    IotdService().update_top_pick_nomination_archive()


@shared_task()
def update_top_pick_archive():
    IotdService().update_top_pick_archive()
