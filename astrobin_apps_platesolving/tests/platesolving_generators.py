from django.contrib.contenttypes.models import ContentType

from astrobin_apps_platesolving.models import Solution, PlateSolvingSettings, PlateSolvingAdvancedSettings


class PlateSolvingGenerators:
    def __init__(self):
        pass

    @staticmethod
    def solution(target, *args, **kwargs):
        return Solution.objects.create(
            object_id=target.pk,
            content_type=ContentType.objects.get_for_model(target),
            image_file=kwargs.pop('image_file', 'solutions/foo.jpg')
        )

    @staticmethod
    def settings(*args, **kwargs):
        return PlateSolvingSettings.objects.create(
            blind=kwargs.get('blind', True),
            scale_units=kwargs.get('scale_units', None),
            scale_min=kwargs.get('scale_min', None),
            scale_max=kwargs.get('scale_max', None),
            center_ra=kwargs.get('center_ra', None),
            center_dec=kwargs.get('center_dec', None),
            radius=kwargs.get('radius', None),
        )

    @staticmethod
    def advanced_settings(*args, **kwargs):
        return PlateSolvingAdvancedSettings.objects.create(
            sample_raw_frame_file=kwargs.get('sample_raw_frame_file', None),
            scaled_font_size=kwargs.get('scaled_font_size', 'M'),
            show_grid=kwargs.get('show_grid', True),
            show_constellation_borders=kwargs.get('show_constellation_borders', True),
            show_constellation_lines=kwargs.get('show_constellation_lines', True),
            show_named_stars=kwargs.get('show_named_stars', True),
            show_messier=kwargs.get('show_messier', True),
            show_ngc_ic=kwargs.get('show_ngc_ic', True),
            show_vdb=kwargs.get('show_vdb', True),
            show_sharpless=kwargs.get('show_sharpless', True),
            show_barnard=kwargs.get('show_barnard', True),
            show_pgc=kwargs.get('show_pgc', False),
            show_planets=kwargs.get('show_planets', True),
            show_asteroids=kwargs.get('show_asteroids', True),
            show_gcvs=kwargs.get('show_gcvs', False),
            show_tycho_2=kwargs.get('show_tycho_2', False),
            show_cgpn=kwargs.get('show_cgpn', False),
        )
