import datetime

from astrobin.tests.generators import Generators
from astrobin_apps_iotd.models import IotdSubmission, IotdVote, Iotd


class IotdGenerators:
    def __init__(self):
        pass

    @staticmethod
    def submission(**kwargs):
        return IotdSubmission.objects.create(
            submitter=kwargs.pop('submitter', Generators.user(groups=['iotd_submitters'])),
            image=kwargs.pop('image', Generators.image()),
        )

    @staticmethod
    def vote(**kwargs):
        return IotdVote.objects.create(
            reviewer=kwargs.pop('reviewer', Generators.user(groups=['iotd_reviewers'])),
            image=kwargs.pop('image', Generators.image()),
        )

    @staticmethod
    def iotd(**kwargs):
        return Iotd.objects.create(
            judge=kwargs.pop('judge', Generators.user(groups=['iotd_judges'])),
            image=kwargs.pop('image', Generators.image()),
            date=kwargs.pop('date', datetime.date.today()),
        )
