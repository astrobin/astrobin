import datetime

from astrobin.tests.generators import Generators
from astrobin_apps_iotd.models import IotdSubmission, IotdVote, Iotd
from common.constants import GroupName


class IotdGenerators:
    def __init__(self):
        pass

    @staticmethod
    def submission(**kwargs):
        return IotdSubmission.objects.create(
            submitter=kwargs.pop('submitter', Generators.user(groups=[GroupName.IOTD_SUBMITTERS])),
            image=kwargs.pop('image', Generators.image()),
        )

    @staticmethod
    def vote(**kwargs):
        return IotdVote.objects.create(
            reviewer=kwargs.pop('reviewer', Generators.user(groups=[GroupName.IOTD_REVIEWERS])),
            image=kwargs.pop('image', Generators.image()),
        )

    @staticmethod
    def iotd(**kwargs):
        return Iotd.objects.create(
            judge=kwargs.pop('judge', Generators.user(groups=[GroupName.IOTD_JUDGES])),
            image=kwargs.pop('image', Generators.image()),
            date=kwargs.pop('date', datetime.date.today()),
        )
