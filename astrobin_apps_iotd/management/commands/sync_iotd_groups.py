from django.core.management.base import BaseCommand

from common.constants import GroupName


class Command(BaseCommand):
    help = "Syncs IOTD AstroBin Groups to equivalent contrib.auth groups"

    def handle(self, *args, **options):
        from itertools import chain
        from django.contrib.auth.models import Group as DGroup
        from astrobin_apps_groups.models import Group as AGroup

        map_ = {
            # key: [[clear groups], [non clear groups], [clear agroups], [non clear agroups]]
            'IOTD Submitters': [[GroupName.IOTD_SUBMITTERS], [GroupName.IOTD_STAFF, 'content_moderators'], [], ['IOTD Staff']],
            'IOTD Reviewers': [[GroupName.IOTD_REVIEWERS], [GroupName.IOTD_STAFF, 'content_moderators'], [], ['IOTD Staff']],
            'IOTD Judges': [[GroupName.IOTD_JUDGES], [GroupName.IOTD_STAFF, 'content_moderators'], [], ['IOTD Staff']],
        }
        agroups = AGroup.objects.filter(name__in = list(map_.keys()))
        all_members = []

        for agroup in agroups:
            clear_dgroups_names = map_[agroup.name][0]
            non_clear_dgroups_names = map_[agroup.name][1]
            clear_agroups_names = map_[agroup.name][2]
            non_clear_agroups_names = map_[agroup.name][3]

            members = agroup.members.all()
            all_members = list(chain(all_members, list(members)))

            for dgroup_name in clear_dgroups_names:
                dgroup, created = DGroup.objects.get_or_create(name = dgroup_name)
                dgroup.user_set.clear()
                dgroup.user_set.add(*list(members))

            for dgroup_name in non_clear_dgroups_names:
                dgroup, created = DGroup.objects.get_or_create(name = dgroup_name)
                dgroup.user_set.add(*list(members))

            for agroup_name in clear_agroups_names:
                agroup_ = AGroup.objects.get(name = agroup_name)
                agroup_.members.clear()
                for member in members:
                    agroup_.members.add(member)

            for agroup_name in non_clear_agroups_names:
                agroup_ = AGroup.objects.get(name = agroup_name)
                for member in members:
                    agroup_.members.add(member)

        for agroup in agroups:
            non_clear_dgroups_names = map_[agroup.name][1]
            for dgroup_name in non_clear_dgroups_names:
                dgroup, created = DGroup.objects.get_or_create(name = dgroup_name)
                for member in dgroup.user_set.all():
                    if not member in all_members:
                        dgroup.user_set.remove(member)

            non_clear_agroups_names = map_[agroup.name][3]
            for agroup_name in non_clear_agroups_names:
                agroup_ = AGroup.objects.get(name = agroup_name)
                for member in agroup.members.all():
                    if not member in all_members:
                        agroup_.members.remove(member)
