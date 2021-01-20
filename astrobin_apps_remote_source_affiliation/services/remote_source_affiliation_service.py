from annoying.functions import get_object_or_None

from astrobin_apps_remote_source_affiliation.models import RemoteSourceAffiliate
from common.services import DateTimeService


class RemoteSourceAffiliationService:
    @staticmethod
    def is_remote_source_affiliate(code):
        # type: (unicode) -> bool

        remote_source = get_object_or_None(RemoteSourceAffiliate, code=code)  # type: RemoteSourceAffiliate

        if remote_source is None:
            return False

        return remote_source.affiliation_start is not None and \
               remote_source.affiliation_expiration >= DateTimeService.today()
