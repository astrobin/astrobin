# Django
from django.apps import AppConfig
from django.db.utils import IntegrityError, ProgrammingError, OperationalError


class AstroBinAppConfig(AppConfig):
    name = 'astrobin'
    verbose_name = 'AstroBin'

    def registerActStreamModels(self):
        from actstream import registry
        registry.register('auth.user')
        registry.register('astrobin.gear')
        registry.register('astrobin.telescope')
        registry.register('astrobin.camera')
        registry.register('astrobin.mount')
        registry.register('astrobin.filter')
        registry.register('astrobin.software')
        registry.register('astrobin.accessory')
        registry.register('astrobin.focalreducer')
        registry.register('astrobin.image')
        registry.register('astrobin.imagerevision')
        registry.register('rawdata.PublicDataPool')
        registry.register('rawdata.RawImage')
        registry.register('nested_comments.nestedcomment')
        registry.register('reviews.review')
        registry.register('toggleproperties.toggleproperty')
        registry.register('astrobin_apps_groups.group')


    def registerPeriodicTasks(self):
        from django_celery_beat.models import CrontabSchedule, PeriodicTask

        try:
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute='0',
                hour='0',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            PeriodicTask.objects.get_or_create(
                crontab=schedule,
                name='global_stats',
                task='astrobin.tasks.global_stats',
            )

            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute='0',
                hour='4',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            PeriodicTask.objects.get_or_create(
                crontab=schedule,
                name='sync_iotd_api',
                task='astrobin.tasks.sync_iotd_api',
            )

            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute='5',
                hour='4',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            PeriodicTask.objects.get_or_create(
                crontab=schedule,
                name='merge_gear',
                task='astrobin.tasks.merge_gear',
            )

            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute='15',
                hour='4',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
            PeriodicTask.objects.get_or_create(
                crontab=schedule,
                name='hitcount_cleanup',
                task='astrobin.tasks.hitcount_cleanup',
            )
        except ProgrammingError:
            print "Attempting to create priodic task before the migration"
        except OperationalError:
            # Happens during tests
            pass


    def ready(self):
        from astrobin.signals import *
        from astrobin_apps_notifications.signals import *
        from rawdata.signals import *

        self.registerActStreamModels()
        self.registerPeriodicTasks()
