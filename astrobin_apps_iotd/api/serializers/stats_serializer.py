from rest_framework import serializers

from astrobin_apps_iotd.models import IotdStats
from common.templatetags.common_tags import percentage as p


class StatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IotdStats
        fields = '__all__'

    def to_representation(self, instance):
        r = super().to_representation(instance)

        # Subject type
        
        # Prepare IOTD percentages.
        r['deep_sky_iotds'] = p(r['deep_sky_iotds'], r['total_iotds'])
        r['solar_system_iotds'] = p(r['solar_system_iotds'], r['total_iotds'])
        r['wide_field_iotds'] = p(r['wide_field_iotds'], r['total_iotds'])
        r['star_trails_iotds'] = p(r['star_trails_iotds'], r['total_iotds'])
        r['northern_lights_iotds'] = p(r['northern_lights_iotds'], r['total_iotds'])
        r['noctilucent_clouds_iotds'] = p(r['noctilucent_clouds_iotds'], r['total_iotds'])
        r['landscape_iotds'] = p(r['landscape_iotds'], r['total_iotds'])
        r['artificial_satellite_iotds'] = p(r['artificial_satellite_iotds'], r['total_iotds'])

        # Prepare TP percentages.
        r['deep_sky_tps'] = p(r['deep_sky_tps'], r['total_tps'])
        r['solar_system_tps'] = p(r['solar_system_tps'], r['total_tps'])
        r['wide_field_tps'] = p(r['wide_field_tps'], r['total_tps'])
        r['star_trails_tps'] = p(r['star_trails_tps'], r['total_tps'])
        r['northern_lights_tps'] = p(r['northern_lights_tps'], r['total_tps'])
        r['noctilucent_clouds_tps'] = p(r['noctilucent_clouds_tps'], r['total_tps'])
        r['landscape_tps'] = p(r['landscape_tps'], r['total_tps'])
        r['artificial_satellite_tps'] = p(r['artificial_satellite_tps'], r['total_tps'])

        # Prepare TPN percentages.
        r['deep_sky_tpns'] = p(r['deep_sky_tpns'], r['total_tpns'])
        r['solar_system_tpns'] = p(r['solar_system_tpns'], r['total_tpns'])
        r['wide_field_tpns'] = p(r['wide_field_tpns'], r['total_tpns'])
        r['star_trails_tpns'] = p(r['star_trails_tpns'], r['total_tpns'])
        r['northern_lights_tpns'] = p(r['northern_lights_tpns'], r['total_tpns'])
        r['noctilucent_clouds_tpns'] = p(r['noctilucent_clouds_tpns'], r['total_tpns'])
        r['landscape_tpns'] = p(r['landscape_tpns'], r['total_tpns'])
        r['artificial_satellite_tpns'] = p(r['artificial_satellite_tpns'], r['total_tpns'])

        # Prepare total percentages.
        r['total_deep_sky_images'] = p(r['total_deep_sky_images'], r['total_submitted_images'])
        r['total_solar_system_images'] = p(r['total_solar_system_images'], r['total_submitted_images'])
        r['total_wide_field_images'] = p(r['total_wide_field_images'], r['total_submitted_images'])
        r['total_star_trails_images'] = p(r['total_star_trails_images'], r['total_submitted_images'])
        r['total_northern_lights_images'] = p(r['total_northern_lights_images'], r['total_submitted_images'])
        r['total_noctilucent_clouds_images'] = p(r['total_noctilucent_clouds_images'], r['total_submitted_images'])
        r['total_landscape_images'] = p(r['total_landscape_images'], r['total_submitted_images'])
        r['total_artificial_satellite_images'] = p(r['total_artificial_satellite_images'], r['total_submitted_images'])

        # Data source
        
        # Prepare IOTD percentages.
        r['backyard_iotds'] = p(r['backyard_iotds'], r['total_iotds'])
        r['traveller_iotds'] = p(r['traveller_iotds'], r['total_iotds'])
        r['own_remote_iotds'] = p(r['own_remote_iotds'], r['total_iotds'])
        r['amateur_hosting_iotds'] = p(r['amateur_hosting_iotds'], r['total_iotds'])
        r['public_amateur_data_iotds'] = p(r['public_amateur_data_iotds'], r['total_iotds'])
        r['pro_data_iotds'] = p(r['pro_data_iotds'], r['total_iotds'])
        r['mix_iotds'] = p(r['mix_iotds'], r['total_iotds'])
        r['other_iotds'] = p(r['other_iotds'], r['total_iotds'])
        r['unknown_iotds'] = p(r['unknown_iotds'], r['total_iotds'])

        # Prepare TP percentages.
        r['backyard_tps'] = p(r['backyard_tps'], r['total_tps'])
        r['traveller_tps'] = p(r['traveller_tps'], r['total_tps'])
        r['own_remote_tps'] = p(r['own_remote_tps'], r['total_tps'])
        r['amateur_hosting_tps'] = p(r['amateur_hosting_tps'], r['total_tps'])
        r['public_amateur_data_tps'] = p(r['public_amateur_data_tps'], r['total_tps'])
        r['pro_data_tps'] = p(r['pro_data_tps'], r['total_tps'])
        r['mix_tps'] = p(r['mix_tps'], r['total_tps'])
        r['other_tps'] = p(r['other_tps'], r['total_tps'])
        r['unknown_tps'] = p(r['unknown_tps'], r['total_tps'])

        # Prepare TPN percentages.
        r['backyard_tpns'] = p(r['backyard_tpns'], r['total_tpns'])
        r['traveller_tpns'] = p(r['traveller_tpns'], r['total_tpns'])
        r['own_remote_tpns'] = p(r['own_remote_tpns'], r['total_tpns'])
        r['amateur_hosting_tpns'] = p(r['amateur_hosting_tpns'], r['total_tpns'])
        r['public_amateur_data_tpns'] = p(r['public_amateur_data_tpns'], r['total_tpns'])
        r['pro_data_tpns'] = p(r['pro_data_tpns'], r['total_tpns'])
        r['mix_tpns'] = p(r['mix_tpns'], r['total_tpns'])
        r['other_tpns'] = p(r['other_tpns'], r['total_tpns'])
        r['unknown_tpns'] = p(r['unknown_tpns'], r['total_tpns'])

        # Prepare total percentages.
        r['total_backyard_images'] = p(r['total_backyard_images'], r['total_submitted_images'])
        r['total_traveller_images'] = p(r['total_traveller_images'], r['total_submitted_images'])
        r['total_own_remote_images'] = p(r['total_own_remote_images'], r['total_submitted_images'])
        r['total_amateur_hosting_images'] = p(r['total_amateur_hosting_images'], r['total_submitted_images'])
        r['total_public_amateur_data_images'] = p(r['total_public_amateur_data_images'], r['total_submitted_images'])
        r['total_pro_data_images'] = p(r['total_pro_data_images'], r['total_submitted_images'])
        r['total_mix_images'] = p(r['total_mix_images'], r['total_submitted_images'])
        r['total_other_images'] = p(r['total_other_images'], r['total_submitted_images'])
        r['total_unknown_images'] = p(r['total_unknown_images'], r['total_submitted_images'])

        return r
