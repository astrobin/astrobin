import logging
import os
import re
import time
import urllib
from typing import List, Optional, Union

import simplejson
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db import IntegrityError
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone

from astrobin.models import DeepSky_Acquisition, Image, ImageRevision, Location
from astrobin.services.utils_service import UtilsService
from astrobin.utils import degrees_minutes_seconds_to_decimal_degrees
from astrobin_apps_platesolving.annotate import Annotator
from astrobin_apps_platesolving.backends.astrometry_net.errors import RequestError
from astrobin_apps_platesolving.models import (PlateSolvingAdvancedSettings, PlateSolvingSettings, Solution)
from astrobin_apps_platesolving.solver import AdvancedSolver, Solver
from astrobin_apps_platesolving.utils import ThumbnailNotReadyException

log = logging.getLogger(__name__)


class SolutionService:
    solution: Solution = None
    
    @staticmethod
    def get_radius_category(radius):
        """
        Categorize a solution's field radius
        """
        if radius is None:
            return None
            
        radius = float(radius)
        if radius > 30:
            return "very_large"  # >30 degrees
        elif radius > 15:
            return "large"       # 15-30 degrees
        elif radius > 4:
            return "medium"      # 4-15 degrees
        elif radius > 1:
            return "small"       # 1-4 degrees
        else:
            return "very_small"  # <1 degree

    @staticmethod
    def get_or_create_solution(target: Union[Image, ImageRevision]) -> (Solution, bool):
        content_type = ContentType.objects.get_for_model(target)
        try:
            solution, _ = Solution.objects.get_or_create(object_id=target.id, content_type=content_type)
        except Solution.MultipleObjectsReturned:
            solution = Solution.objects.filter(object_id=target.id, content_type=content_type).order_by(
                '-status'
            ).first()
            Solution.objects.filter(object_id=target.id, content_type=content_type).exclude(pk=solution.pk).delete()

        return solution

    @staticmethod
    def get_default_advanced_settings_for_radius_category(radius_category: Optional[str]) -> dict:
        """
        Get the default advanced settings for a specific radius category.
        
        Args:
            radius_category: One of "very_large", "large", "medium", "small", "very_small", or None
            
        Returns:
            A dictionary of default settings appropriate for the radius category
        """
        defaults = {}
        
        # If no radius category, return empty defaults
        if not radius_category:
            return defaults
            
        # Default settings for all field sizes
        defaults.update({
            'show_grid': True,
            'show_ecliptic': True,
            'show_galactic_equator': True,
            'show_constellation_borders': True,
            'show_constellation_lines': True,
        })
        
        # Very large field - only show structural elements (>30 degrees)
        if radius_category == "very_large":
            defaults.update({
                'scaled_font_size': "S",
                'show_named_stars': True,
                'show_hd': False,
                'show_messier': True,
                'show_ngc_ic': False,
                'show_vdb': False,
                'show_sharpless': False,
                'show_barnard': False,
                'show_lbn': False,
                'show_ldn': False,
                'show_pgc': False,
                'show_planets': True,
                'show_asteroids': False,
                'show_gcvs': False,
                'show_tycho_2': False,
                'show_cgpn': False,
                'show_quasars': False,
            })
            
        # Large field (15-30 degrees)
        elif radius_category == "large":
            defaults.update({
                'scaled_font_size': "S",
                'show_named_stars': True,
                'show_hd': True,
                'hd_max_magnitude': 4.5,
                'show_messier': True,
                'show_ngc_ic': False,
                'show_vdb': False,
                'show_sharpless': True,
                'show_barnard': False,
                'show_lbn': False,
                'show_ldn': False,
                'show_pgc': False,
                'show_planets': True,
                'show_asteroids': False,
                'show_gcvs': False,
                'show_tycho_2': False,
                'show_cgpn': True,
                'show_quasars': False,
            })
            
        # Medium field (4-15 degrees)
        elif radius_category == "medium":
            defaults.update({
                'scaled_font_size': "M",
                'show_named_stars': True,
                'show_hd': True,
                'hd_max_magnitude': 6.0,
                'show_messier': True,
                'show_ngc_ic': True,
                'show_vdb': True,
                'show_sharpless': True,
                'show_barnard': True,
                'show_lbn': True,
                'show_ldn': True,
                'show_pgc': False,
                'show_planets': True,
                'show_asteroids': True,
                'show_gcvs': False,
                'show_tycho_2': False,
                'show_cgpn': True,
                'show_quasars': False,
            })
            
        # Small field (1-4 degrees)
        elif radius_category == "small":
            defaults.update({
                'scaled_font_size': "M",
                'show_named_stars': True,
                'show_hd': True,
                'hd_max_magnitude': 6,
                'show_messier': True,
                'show_ngc_ic': True,
                'show_vdb': True,
                'show_sharpless': True,
                'show_barnard': True,
                'show_lbn': True,
                'show_ldn': True,
                'show_pgc': True,
                'show_planets': True,
                'show_asteroids': True,
                'show_gcvs': True,
                'gcvs_max_magnitude': 10.0,
                'show_tycho_2': False,
                'show_cgpn': True,
                'show_quasars': False,
            })
            
        # Very small field (<1 degree) - show everything
        elif radius_category == "very_small":
            defaults.update({
                'scaled_font_size': "M",
                'show_named_stars': True,
                'show_hd': True,
                'hd_max_magnitude': 8,
                'show_messier': True,
                'show_ngc_ic': True,
                'show_vdb': True,
                'show_sharpless': True,
                'show_barnard': True,
                'show_lbn': True,
                'show_ldn': True,
                'show_pgc': True,
                'show_planets': True,
                'show_asteroids': True,
                'show_gcvs': True,
                'gcvs_max_magnitude': 12.0,
                'show_tycho_2': True,
                'tycho_2_max_magnitude': 11.0,
                'show_cgpn': True,
                'show_quasars': True,
            })
            
        return defaults

    @staticmethod
    def get_or_create_advanced_settings(target: Union[Image, ImageRevision], solution=None) -> (PlateSolvingAdvancedSettings, bool):
        # Get radius of the current target if it already has a solution
        current_radius_category = None
        
        # If a solution is provided (e.g., from finalize_basic_solver), use its radius
        if solution and solution.radius:
            current_radius_category = SolutionService.get_radius_category(solution.radius)
        elif target._meta.model_name == 'image' and hasattr(target, 'solution') and target.solution and target.solution.radius:
            current_radius_category = SolutionService.get_radius_category(target.solution.radius)
        elif target._meta.model_name == 'imagerevision' and hasattr(target.image, 'solution') and target.image.solution and target.image.solution.radius:
            current_radius_category = SolutionService.get_radius_category(target.image.solution.radius)
            
        # Check if we can reuse settings from another image
        if target._meta.model_name == 'image' and hasattr(target, 'user'):
            images = Image.objects_including_wip.filter(user=target.user).order_by('-pk')  # type: QuerySet[Image]
            for image in images:
                # Skip the current image
                if image.pk == target.pk:
                    continue
                    
                if image.solution and image.solution.advanced_settings:
                    # If we know the radius category of current image, try to match with similar images
                    if current_radius_category and image.solution.radius:
                        image_radius_category = SolutionService.get_radius_category(image.solution.radius)
                        # Only use settings from images with similar field size
                        if image_radius_category != current_radius_category:
                            continue
                            
                    latest_settings = image.solution.advanced_settings  # type: PlateSolvingAdvancedSettings
                    latest_settings.pk = None
                    latest_settings.sample_raw_frame_file = None
                    latest_settings.save()
                    log.debug(
                        f'SolutionService: solution {solution.pk if solution else "None"} - '
                        f'using settings from image {image.pk}'
                    )
                    return latest_settings, False
                    
        # Try to use settings from parent image for revisions
        elif target._meta.model_name == 'imagerevision' and hasattr(target, 'image') and target.image.solution and target.image.solution.advanced_settings:
            latest_settings = target.image.solution.advanced_settings
            latest_settings.pk = None
            latest_settings.save()
            log.debug(
                f'SolutionService: solution {solution.pk if solution else "None"} - '
                f'using settings for revision from image {target.image.pk}'
            )
            return latest_settings, False

        # Get defaults for the radius category
        defaults = SolutionService.get_default_advanced_settings_for_radius_category(current_radius_category)
        
        # Create the settings with all properties in one go
        new_settings = PlateSolvingAdvancedSettings.objects.create(**defaults)

        log.debug(
            f'SolutionService: solution {solution.pk if solution else "None"} - '
            f'using default settings for radius category {current_radius_category}'
        )
            
        return new_settings, True

    def __init__(self, solution: Solution) -> None:
        self.solution = solution

    def enforce_basic_settings(self) -> None:
        """Ensures that the solution has basic settings"""
        if self.solution.settings is None:
            settings_ = PlateSolvingSettings.objects.create()
            self.solution.settings = settings_
            Solution.objects.filter(pk=self.solution.pk).update(settings=settings_)

    def enforce_advanced_settings(self) -> None:
        """Ensures that the solution has advanced settings with appropriate defaults"""
        if self.solution.advanced_settings is None:
            advanced_settings, _ = self.get_or_create_advanced_settings(
                self.solution.content_object, 
                solution=self.solution
            )
            self.solution.advanced_settings = advanced_settings
            Solution.objects.filter(pk=self.solution.pk).update(advanced_settings=advanced_settings)
            
    def enforce_settings(self) -> None:
        """Legacy method that ensures both basic and advanced settings exist"""
        self.enforce_basic_settings()
        self.enforce_advanced_settings()

    def has_submission_id(self) -> bool:
        return self.solution.submission_id is not None and self.solution.submission_id > 0

    def target_is_image(self) -> bool:
        return self.solution.content_object.__class__.__name__ == 'Image'

    def target_is_image_revision(self) -> bool:
        return self.solution.content_object.__class__.__name__ == 'ImageRevision'

    def target_thumbnail_url(self, alias: str) -> str:
        if self.target_is_image_revision():
            return self.solution.content_object.thumbnail(alias, sync=True)
        return self.solution.content_object.thumbnail(alias, '0', sync=True)

    def start_basic_solver(self) -> None:
        # For basic solver, we only need the basic settings
        self.enforce_basic_settings()

        if self.has_submission_id():
            log.debug(
                "start_basic_solver: returning because solution %d already has a submission ID" % self.solution.pk
            )
            return

        solver = Solver()
        self.solution.attempts += 1

        try:
            url = self.target_thumbnail_url('real')

            if self.solution.settings.blind:
                self.solution.submission_id = solver.solve(
                    url,
                    publicly_visible='y' if self.solution.settings.astrometry_net_publicly_visible else 'n',
                    downsample_factor=self.solution.settings.downsample_factor,
                    use_sextractor=self.solution.settings.use_sextractor,
                )

                if not self.solution.submission_id:
                    self.solution.error = "No submission ID returned"
                    self.solution.status = Solver.FAILED
                    self.solution.save()
            else:
                self.solution.submission_id = solver.solve(
                    url,
                    publicly_visible='y' if self.solution.settings.astrometry_net_publicly_visible else 'n',
                    scale_units=self.solution.settings.scale_units,
                    scale_lower=self.solution.settings.scale_min,
                    scale_upper=self.solution.settings.scale_max,
                    center_ra=self.solution.settings.center_ra,
                    center_dec=self.solution.settings.center_dec,
                    radius=self.solution.settings.radius,
                    downsample_factor=self.solution.settings.downsample_factor,
                    use_sextractor=self.solution.settings.use_sextractor,
                )
            self.solution.status = Solver.PENDING
            self.solution.error = None
        except Exception as e:
            log.error("Error during basic plate-solving: %s" % str(e))
            self.solution.status = Solver.FAILED
            self.solution.submission_id = None
            self.solution.error = str(e)
        finally:
            self.solution.save()

    def get_basic_solver_status(self) -> int:
        return Solver().status(self.solution.submission_id)

    def get_advanced_solver_status(self):
        return self.solution.status

    def update_solver_status(self) -> int:
        try:
            if self.solution.status < Solver.ADVANCED_PENDING:
                self.solution.status = self.get_basic_solver_status()
            else:
                self.solution.status = self.get_advanced_solver_status()
        except Exception as e:
            error = str(e)
            status = Solver.FAILED
            log.error("Error during basic plate-solving: %s" % error)
            self.solution.clear_advanced(save=False)
            self.solution.status = status
            self.solution.submission_id = None
            self.solution.error = error
        finally:
            self.solution.save()

        return self.solution.status

    def get_target_image(self) -> Image:
        target: Union[Image, ImageRevision] = self.solution.content_object

        if self.target_is_image_revision():
            return target.image

        return target

    def get_observation_time_and_location(self) -> (Optional[str], Optional[str], Optional[str], Optional[int]):
        observation_time: Optional[str] = None
        latitude: Optional[str] = None
        longitude: Optional[str] = None
        altitude: Optional[int] = None

        image = self.get_target_image()

        acquisitions = DeepSky_Acquisition.objects.filter(image=image)
        if acquisitions.count() > 0 and acquisitions[0].date:
            observation_time = acquisitions[0].date.isoformat()

        locations = image.locations.all()
        if locations.count() > 0:
            location: Location = locations.first()
            latitude = degrees_minutes_seconds_to_decimal_degrees(
                location.lat_deg, location.lat_min, location.lat_sec, location.lat_side
            )
            longitude = degrees_minutes_seconds_to_decimal_degrees(
                location.lon_deg, location.lon_min, location.lon_sec, location.lon_side
            )
            altitude = location.altitude

        return observation_time, latitude, longitude, altitude

    def start_advanced_solver(self, priority='normal'):
        target = self.solution.content_object
        # For advanced solver, we need both basic and advanced settings
        self.enforce_settings()

        if self.solution.pixinsight_serial_number:
            log.debug(
                "start_advanced_solver: returning because solution %d already has a PixInsight serial number"
                % self.solution.pk
            )
            return

        if self.solution.status != Solver.SUCCESS:
            log.debug(
                "start_advanced_solver: returning because solution %d is not in SUCCESS state" % self.solution.pk
            )
            return

        solver = AdvancedSolver()

        try:
            if self.solution.advanced_settings.sample_raw_frame_file:
                url = self.solution.advanced_settings.sample_raw_frame_file.url
            else:
                url = self.target_thumbnail_url('hd')

            observation_time, latitude, longitude, altitude = self.get_observation_time_and_location()

            submission = solver.solve(
                url,
                ra=self.solution.ra,
                dec=self.solution.dec,
                pixscale=self.solution.pixscale,
                radius=self.solution.radius,
                observation_time=observation_time,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                advanced_settings=self.solution.advanced_settings,
                image_width=target.w,
                image_height=target.h,
                priority=priority
            )

            self.solution.status = Solver.ADVANCED_PENDING
            self.solution.pixinsight_serial_number = submission
            self.solution.error = None
        except Exception as e:
            error = str(e)
            log.error("Error during advanced plate-solving: %s" % error)
            self.solution.status = Solver.ADVANCED_FAILED
            self.solution.pixinsight_serial_number = None
            self.solution.error = error
        finally:
            self.solution.save()

    def finalize_basic_solver(self) -> None:
        solver = Solver()
        status = solver.status(self.solution.submission_id)

        if status == Solver.SUCCESS:
            info = solver.info(self.solution.submission_id)

            if 'objects_in_field' in info:
                self.solution.objects_in_field = ', '.join(info['objects_in_field'])

            if 'calibration' in info:
                self.solution.ra = "%.3f" % info['calibration']['ra']
                self.solution.dec = "%.3f" % info['calibration']['dec']
                self.solution.orientation = "%.3f" % info['calibration']['orientation']
                self.solution.radius = "%.3f" % info['calibration']['radius']
                self.solution.pixscale = "%.3f" % info['calibration']['pixscale']

            try:
                target = self.solution.content_type.get_object_for_this_type(pk=self.solution.object_id)
            except self.solution.content_type.model_class().DoesNotExist:
                # Target image was deleted meanwhile
                return

            # Annotate image
            try:
                annotations_obj = solver.annotations(self.solution.submission_id)
                self.solution.annotations = simplejson.dumps(annotations_obj)
                annotator = Annotator(self.solution)
                annotated_image = annotator.annotate()
            except RequestError as e:
                self.solution.status = Solver.FAILED
                self.solution.error = str(e)
                self.solution.save()
                return
            except ThumbnailNotReadyException as e:
                self.solution.status = Solver.PENDING
                self.solution.error = str(e)
                self.solution.save()
                return

            # Now that we have the radius from the basic solver, we can enforce advanced settings
            # which will use the radius to set appropriate defaults
            self.enforce_advanced_settings()

            filename, _ = os.path.splitext(target.image_file.name)
            annotated_filename = "%s-%d%s" % (filename, int(time.time()), '.jpg')
            if annotated_image:
                self.solution.image_file.save(annotated_filename, annotated_image, save=False)

            # Get sky plot image
            url = solver.sky_plot_zoom1_image_url(self.solution.submission_id)
            if url:
                try:
                    img = NamedTemporaryFile()
                    data = UtilsService.http_with_retries(url)
                    img.write(data.content)
                    img.flush()
                    img.seek(0)
                    f = File(img)
                    try:
                        self.solution.skyplot_zoom1.save(target.image_file.name, f)
                    except IntegrityError:
                        pass
                except urllib.error.URLError:
                    log.error("Error downloading sky plot image: %s" % url)

        self.solution.status = status
        self.solution.save()
        

    def restart(self):
        self.solution.clear()
        target = self.solution.content_object

        if hasattr(target, 'updated'):
            model = self.solution.content_type.model_class()
            if model.__name__ == 'Image':
                Image.objects_including_wip.filter(pk=target.pk).update(updated=timezone.now())
            elif model.__name__ == 'ImageRevision':
                Image.objects_including_wip.filter(pk=target.image.pk).update(updated=timezone.now())

        from astrobin_apps_platesolving.tasks import start_basic_solver
        start_basic_solver.delay(content_type_id=self.solution.content_type.pk, object_id=self.solution.object_id)

    def get_objects_in_field(self, clean=True) -> List[str]:
        objects = []

        if self.solution and self.solution.objects_in_field:
            objects = [x.strip() for x in self.solution.objects_in_field.split(',')]
        if self.solution and self.solution.advanced_annotations:
            advanced_annotations_lines = self.solution.advanced_annotations.split('\n')
            for line in advanced_annotations_lines:
                header = line.split(',')[0]

                if header != "Label":
                    continue

                advanced_annotation = line.split(',')[-1]

                if clean:
                    regex = r"^(?P<catalog>M|NGC|IC|LDN|LBN|PGC|VDB)(?P<id>\d+)$"
                    matches = re.findall(regex, advanced_annotation)
                    if len(matches) == 1:
                        catalog = matches[0][0]
                        number = matches[0][1]
                        advanced_annotation = "%s %s" % (catalog, number)

                if advanced_annotation.lower() not in [x.lower() for x in objects] and advanced_annotation != '':
                    objects.append(advanced_annotation)

        return sorted(objects)

    def duplicate_objects_in_field_by_catalog_space(self) -> List[str]:
        value = []
        objects = self.get_objects_in_field()
        space_regex = r"^(?P<catalog>M|NGC|IC|PGC|LDN|LBN|PGC|VDB) (?P<id>\d+)$"
        dash_regex = r"^(?P<catalog>Sh2|TYC)(?P<id>.*)$"

        for obj in objects:
            space_matches = re.findall(space_regex, obj)
            dash_matches = re.findall(dash_regex, obj)

            if len(space_matches) >= 1 or len(dash_matches) >= 1:
                if len(space_matches) >= 1:
                    catalog = space_matches[0][0]
                    number = space_matches[0][1]
                    value.append(f'{catalog}{number}')
                    value.append(f'{catalog} {number}')
                elif len(dash_matches) >= 1:
                    value.append(obj)
                    value.append(obj.replace('-', '_'))
            else:
                value.append(obj)

        return sorted(value)

    def get_search_query_around(self, degrees: int) -> str:
        def _wrap_angle(angle, min_angle, max_angle):
            range_size = max_angle - min_angle
            return (angle - min_angle) % range_size + min_angle

        ra = float(self.solution.advanced_ra or self.solution.ra)
        dec = float(self.solution.advanced_dec or self.solution.dec)

        ra_min = ra - degrees * 0.5
        ra_max = ra + degrees * 0.5

        if ra_min < 0:
            ra_min += 360
        elif ra_min > 360:
            ra_min -= 360

        if ra_max > 360:
            ra_max -= 360
        elif ra_max < 0:
            ra_max += 360

        dec_min = max(dec - degrees * 0.5, -90)
        dec_max = min(dec + degrees * 0.5, 90)

        field_min = 0
        field_max = degrees

        base_search_url = reverse('haystack_search')

        url_params = [
            "q=&d=i&t=all",
            "coord_ra_min=%.2f" % ra_min,
            "coord_ra_max=%.2f" % ra_max,
            "coord_dec_min=%.2f" % dec_min,
            "coord_dec_max=%.2f" % dec_max,
            "field_radius_min=%.2f" % field_min,
            "field_radius_max=%.2f" % field_max
        ]

        return base_search_url + "?" + "&".join(url_params)
