import logging
import mimetypes
import os
import re
import time
from functools import reduce
from typing import Optional, Union

import boto3
import requests
from PIL import Image as PILImage
from braces.views import (
    JSONResponseMixin,
    LoginRequiredMixin,
)
from cairosvg import svg2png
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, PermissionDenied
from django.core.files.images import get_image_dimensions
from django.core.files.temp import NamedTemporaryFile
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import iri_to_uri, smart_text as smart_unicode
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import (
    DeleteView,
    DetailView,
    UpdateView,
)
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin
from silk.profiling.profiler import silk_profile

from astrobin.enums import SubjectType
from astrobin.enums.mouse_hover_image import MouseHoverImage
from astrobin.forms import (
    CopyGearForm, ImageDemoteForm, ImageEditBasicForm, ImageEditGearForm, ImageEditRevisionForm,
    ImageEditThumbnailsForm, ImageFlagThumbsForm, ImagePromoteForm, ImageRevisionUploadForm,
)
from astrobin.forms.uncompressed_source_upload_form import UncompressedSourceUploadForm
from astrobin.models import (Collection, DeepSky_Acquisition, Image, ImageRevision, LANGUAGES, SolarSystem_Acquisition)
from astrobin.stories import add_story
from astrobin.templatetags.tags import can_like
from astrobin.utils import get_image_resolution
from astrobin_apps_groups.forms import AutoSubmitToIotdTpProcessForm, GroupSelectForm
from astrobin_apps_groups.models import Group
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_notifications.tasks import push_notification_for_new_image
from astrobin_apps_platesolving.models import PlateSolvingAdvancedLiveLogEntry, Solution
from astrobin_apps_platesolving.services import SolutionService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import can_see_real_resolution
from common.services import DateTimeService
from common.services.caching_service import CachingService
from nested_comments.models import NestedComment

logger = logging.getLogger("apps")


class ImageSingleObjectMixin(SingleObjectMixin):
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        id = self.kwargs.get(self.pk_url_kwarg)
        image = ImageService.get_object(id, queryset)

        if image is None:
            raise Http404

        return image


class ImageDetailViewBase(ImageSingleObjectMixin, DetailView):
    pass


class ImageUpdateViewBase(ImageSingleObjectMixin, UpdateView):
    pass


class ImageDeleteViewBase(ImageSingleObjectMixin, DeleteView):
    pass


class ImageFlagThumbsView(
    LoginRequiredMixin, ImageUpdateViewBase):
    form_class = ImageFlagThumbsForm
    model = Image
    pk_url_kwarg = 'id'
    http_method_names = ('post',)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Image.objects_including_wip.all()
        return Image.objects_including_wip.filter(user=self.request.user)

    def get_success_url(self):
        return self.object.get_absolute_url()

    def post(self, request, *args, **kwargs):
        image = self.get_object()
        image.thumbnail_invalidate()
        for r in image.revisions.all():
            r.thumbnail_invalidate()
        messages.success(self.request, _("Thanks for reporting the problem. All thumbnails will be generated again."))
        return super(ImageFlagThumbsView, self).post(self.request, args, kwargs)


@method_decorator([
    never_cache
], name='dispatch')
class ImageThumbView(JSONResponseMixin, ImageDetailViewBase):
    model = Image
    queryset = Image.all_objects.all()
    pk_url_kwarg = 'id'

    def get(self, request, *args, **kwargs):
        image = self.get_object()

        alias = kwargs.pop('alias')
        if alias not in list(settings.THUMBNAIL_ALIASES[''].keys()):
            raise Http404

        revision_label = kwargs.pop('r', None)

        force = request.GET.get('force')
        if force is not None:
            if revision_label in (None, 'None', 0, '0'):
                image.thumbnail_invalidate()
            else:
                revision = ImageService(image).get_revision(revision_label)
                revision.thumbnail_invalidate()

        if revision_label is None:
            revision_label = 'final'

        url = image.thumbnail(
            alias, revision_label, animated='animated' in self.request.GET, insecure='insecure' in self.request.GET,
            sync=request.GET.get('sync') is not None)

        return self.render_json_response({
            'id': image.pk,
            'alias': alias,
            'revision': revision_label,
            'url': iri_to_uri(url)
        })


@method_decorator([
    never_cache
], name='dispatch')
class ImageRawThumbView(ImageDetailViewBase):
    model = Image
    queryset = Image.objects_including_wip.all()
    pk_url_kwarg = 'id'

    def get(self, request, *args, **kwargs):
        image = self.get_object()

        alias = kwargs.pop('alias')
        if alias not in list(settings.THUMBNAIL_ALIASES[''].keys()):
            raise Http404

        revision_label = kwargs.pop('r', None)

        force = request.GET.get('force')
        if force is not None:
            if revision_label in (None, 'None', 0, '0'):
                image.thumbnail_invalidate()
            else:
                revision = ImageService(image).get_revision(revision_label)
                revision.thumbnail_invalidate()

        if revision_label is None:
            revision_label = 'final'

        if settings.TESTING:
            thumb = image.thumbnail_raw(
                alias, revision_label, animated='animated' in self.request.GET, insecure='insecure' in self.request.GET,
                sync=request.GET.get('sync') is not None)

            if thumb:
                return redirect(thumb.url)

            return HttpResponse(status=500)

        url = image.thumbnail(
            alias, revision_label, animated='animated' in self.request.GET, insecure='insecure' in self.request.GET,
            sync=request.GET.get('sync') is not None)
        return redirect(smart_unicode(url))


@method_decorator([
    last_modified(CachingService.get_image_last_modified),
    cache_control(private=True, no_cache=True),
    vary_on_cookie
], name='dispatch')
class ImageDetailView(ImageDetailViewBase):
    model = Image
    pk_url_kwarg = 'id'
    template_name = 'image/detail.html'
    template_name_suffix = ''

    @silk_profile(name='Image detail')
    def get(self, request, *args, **kwargs):
        return super(ImageDetailView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        return Image.objects_including_wip.all()

    def dispatch(self, request, *args, **kwargs):
        # Redirect to the correct revision
        image = self.get_object(Image.objects_including_wip)

        if image.moderator_decision == 2:
            if not request.user.is_authenticated or \
                    not request.user.is_superuser and \
                    not request.user.userprofile.is_image_moderator():
                raise Http404

        revision_label = kwargs.get('r')
        if revision_label is not None and revision_label != '0':
            try:
                revision = ImageService(image).get_revisions().get(label=revision_label)
            except ImageRevision.DoesNotExist:
                revision = ImageService(image).get_final_revision()
                redirect_revision_label = revision.label if hasattr(revision, 'label') else '0'
                if request.user.is_authenticated:
                    messages.info(request, _(
                        "You requested revision %s, but it doesn't exist or it was deleted. We redirected you to the "
                        "revision currently marked as final." % revision_label
                    ))
                return redirect(reverse('image_detail', args=(image.get_id(), redirect_revision_label,)))

        if revision_label is None:
            # No revision specified, let's see if we need to redirect to the
            # final.
            if not image.is_final:
                final = image.revisions.filter(is_final=True)
                if final.count() > 0:
                    url = reverse_lazy(
                        'image_detail',
                        args=(image.get_id(), final[0].label,))
                    if 'nc' in request.GET:
                        url += '?nc=%s' % request.GET.get('nc')
                        if 'nce' in request.GET:
                            url += '&nce=%s' % request.GET.get('nce')
                    return redirect(url)

        return super(ImageDetailView, self).dispatch(request, *args, **kwargs)

    # TODO: this function is too long
    def get_context_data(self, **kwargs):
        context = super(ImageDetailView, self).get_context_data(**kwargs)

        image = context['object']
        r = self.kwargs.get('r')
        if r is None:
            r = '0'

        revision_image = None
        instance_to_platesolve = image
        is_revision = False
        if r != '0':
            try:
                revision_image = ImageRevision.objects.filter(image=image, label=r)[0]
                instance_to_platesolve = revision_image
                is_revision = True
            except:
                pass

        #############################
        # GENERATE ACQUISITION DATA #
        #############################
        from astrobin.moon import MoonPhase

        gear_list = (
            (
                _('Imaging telescopes or lenses'),
                image.imaging_telescopes.all(),
                'imaging_telescopes'
            ),

            (
                _('Imaging cameras'),
                image.imaging_cameras.all(),
                'imaging_cameras'
            ),

            (
                _('Mounts'),
                image.mounts.all(),
                'mounts'
            ),

            (
                _('Guiding telescopes or lenses'),
                image.guiding_telescopes.all(),
                'guiding_telescopes'
            ),

            (
                _('Guiding cameras'),
                image.guiding_cameras.all(),
                'guiding_cameras'
            ),

            (
                _('Focal reducers'),
                image.focal_reducers.all(),
                'focal_reducers'
            ),

            (
                _('Software'),
                image.software.all(),
                'software'
            ),

            (
                _('Filters'),
                image.filters.all(),
                'filters'
            ),

            (
                _('Accessory'),
                image.accessories.all(),
                'accessories'
            ),
        )

        deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=image)
        ssa = None
        image_type = None
        deep_sky_data = {}

        if is_revision:
            w, h = get_image_resolution(revision_image)
        else:
            w, h = get_image_resolution(image)

        try:
            ssa = SolarSystem_Acquisition.objects.get(image=image)
        except SolarSystem_Acquisition.DoesNotExist:
            pass
        except MultipleObjectsReturned:
            ssa = SolarSystem_Acquisition.objects.filter(image=image).first()

        if deep_sky_acquisitions:
            image_type = 'deep_sky'

            moon_age_list = []
            moon_illuminated_list = []

            dsa_data = {
                'dates': [],
                'frames': {},
                'integration': 0,
                'darks': [],
                'flats': [],
                'flat_darks': [],
                'bias': [],
                'bortle': [],
                'mean_sqm': [],
                'mean_fwhm': [],
                'temperature': [],
            }
            for a in deep_sky_acquisitions:
                if a.date is not None and a.date not in dsa_data['dates']:
                    dsa_data['dates'].append(a.date)
                    m = MoonPhase(a.date)
                    moon_age_list.append(m.age)
                    moon_illuminated_list.append(m.illuminated * 100.0)

                if a.number and a.duration:
                    key = ""
                    if a.filter is not None:
                        key = "filter(%s)" % a.filter
                    if a.iso is not None:
                        key += '-ISO(%d)' % a.iso
                    if a.gain is not None:
                        key += '-gain(%.2f)' % a.gain
                    if a.sensor_cooling is not None:
                        key += '-temp(%d)' % a.sensor_cooling
                    if a.binning is not None:
                        key += '-bin(%d)' % a.binning
                    key += '-duration(%d)' % a.duration

                    try:
                        current_frames = dsa_data['frames'][key]['integration']
                    except KeyError:
                        current_frames = '0x0"'

                    integration_re = re.match(r'^(\d+)x(\d+)"', current_frames)
                    current_number = int(integration_re.group(1))

                    dsa_data['frames'][key] = {}
                    dsa_data['frames'][key]['filter_url'] = a.filter.get_absolute_url() if a.filter is not None else '#'
                    dsa_data['frames'][key]['filter'] = a.filter if a.filter is not None else ''
                    dsa_data['frames'][key]['iso'] = 'ISO%d' % a.iso if a.iso is not None else ''
                    dsa_data['frames'][key]['gain'] = '(gain: %.2f)' % a.gain if a.gain is not None else ''
                    dsa_data['frames'][key][
                        'sensor_cooling'] = '%dC' % a.sensor_cooling if a.sensor_cooling is not None else ''
                    dsa_data['frames'][key]['binning'] = 'bin %sx%s' % (a.binning, a.binning) if a.binning else ''
                    dsa_data['frames'][key]['integration'] = \
                        '%sx%s" <span class="total-frame-integration">(%s)</span>' % (
                            current_number + a.number,
                            a.duration,
                            DateTimeService.human_time_duration((current_number + a.number) * a.duration)
                        )

                    dsa_data['integration'] += a.duration * a.number

                for i in ['darks', 'flats', 'flat_darks', 'bias']:
                    if a.filter and getattr(a, i):
                        dsa_data[i].append("%d" % getattr(a, i))
                    elif getattr(a, i):
                        dsa_data[i].append(getattr(a, i))

                if a.bortle:
                    dsa_data['bortle'].append(a.bortle)

                if a.mean_sqm:
                    dsa_data['mean_sqm'].append(a.mean_sqm)

                if a.mean_fwhm:
                    dsa_data['mean_fwhm'].append(a.mean_fwhm)

                if a.temperature:
                    dsa_data['temperature'].append(a.temperature)

            def average(values):
                if not len(values):
                    return 0
                return float(sum(values)) / len(values)

            frames_list = sorted(dsa_data['frames'].items())

            deep_sky_data = (
                (_('Dates'), sorted(dsa_data['dates'])),
                (_('Frames'),
                 ('\n' if len(frames_list) > 1 else '') +
                 '\n'.join("%s %s" % (
                     "<a href=\"%s\">%s</a>:" % (f[1]['filter_url'], f[1]['filter']) if f[1]['filter'] else '',
                     "%s %s %s %s %s" % (
                         f[1]['integration'], f[1]['iso'], f[1]['gain'], f[1]['sensor_cooling'], f[1]['binning']),
                 ) for f in frames_list)),
                (_('Integration'), DateTimeService.human_time_duration(dsa_data['integration'])),
                (_('Darks'),
                 '%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['darks'])) / len(dsa_data['darks'])) if
                 dsa_data['darks'] else 0),
                (_('Flats'),
                 '%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['flats'])) / len(dsa_data['flats'])) if
                 dsa_data['flats'] else 0),
                (_('Flat darks'), '%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['flat_darks'])) / len(
                    dsa_data['flat_darks'])) if dsa_data['flat_darks'] else 0),
                (_('Bias'),
                 '%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['bias'])) / len(dsa_data['bias'])) if
                 dsa_data['bias'] else 0),
                (_('Avg. Moon age'), ("%.2f " % (average(moon_age_list),) + _("days")) if moon_age_list else None),
                (_('Avg. Moon phase'), "%.2f%%" % (average(moon_illuminated_list),) if moon_illuminated_list else None),
                (_('Bortle Dark-Sky Scale'),
                 "%.2f" % (average([float(x) for x in dsa_data['bortle']])) if dsa_data['bortle'] else None),
                (_('Mean SQM'),
                 "%.2f" % (average([float(x) for x in dsa_data['mean_sqm']])) if dsa_data['mean_sqm'] else None),
                (_('Mean FWHM'),
                 "%.2f" % (average([float(x) for x in dsa_data['mean_fwhm']])) if dsa_data['mean_fwhm'] else None),
                (_('Temperature'),
                 "%.2f" % (average([float(x) for x in dsa_data['temperature']])) if dsa_data['temperature'] else None),
            )

        elif ssa:
            image_type = 'solar_system'

        profile = None
        if self.request.user.is_authenticated:
            profile = self.request.user.userprofile

        ##############
        # BASIC DATA #
        ##############

        alias = 'regular' if not image.sharpen_thumbnails else 'regular_sharpened'
        mod = self.request.GET.get('mod')
        if mod == 'inverted':
            alias = 'regular_inverted'

        subjects = []
        skyplot_zoom1 = None
        pixinsight_finding_chart = None
        pixinsight_finding_chart_small = None

        if not is_revision and image.solution:
            subjects = SolutionService(image.solution).get_objects_in_field()
            skyplot_zoom1 = image.solution.skyplot_zoom1
            pixinsight_finding_chart = image.solution.pixinsight_finding_chart
            pixinsight_finding_chart_small = image.solution.pixinsight_finding_chart_small

        if is_revision and revision_image.solution:
            subjects = SolutionService(revision_image.solution).get_objects_in_field()
            if revision_image.solution.skyplot_zoom1:
                skyplot_zoom1 = revision_image.solution.skyplot_zoom1
                pixinsight_finding_chart = revision_image.solution.pixinsight_finding_chart
                pixinsight_finding_chart_small = revision_image.solution.pixinsight_finding_chart_small

        locations = '; '.join(['%s' % (x) for x in image.locations.all()])

        #######################
        # PREFERRED LANGUAGES #
        #######################

        user_language = image.user.userprofile.language
        if user_language:
            try:
                user_language = LANGUAGES[user_language]
            except KeyError:
                user_language = _("English")
        else:
            user_language = _("English")

        preferred_languages = [str(user_language)]
        if image.user.userprofile.other_languages:
            for language in image.user.userprofile.other_languages.split(','):
                language_label = [x for x in settings.ALL_LANGUAGE_CHOICES if x[0] == language][0][1]
                if language_label != user_language:
                    preferred_languages.append(str(language_label))

        preferred_languages = ', '.join(preferred_languages)

        ##########################
        # LIKE / BOOKMARKED THIS #
        ##########################
        like_this = image.toggleproperties.filter(property_type="like")
        bookmarked_this = image.toggleproperties.filter(property_type="bookmark")

        ##############
        # NAVIGATION #
        ##############
        image_next = None
        image_prev = None

        nav_ctx = self.request.GET.get('nc', 'user')
        nav_ctx_extra = self.request.GET.get('nce')

        if not image.is_wip and image.published is not None:
            try:
                # Always only lookup public images!
                if nav_ctx == 'user':
                    image_next = Image.objects \
                                     .filter(user=image.user, published__isnull=False, published__gt=image.published) \
                                     .order_by('published')[0:1]
                    image_prev = Image.objects \
                                     .filter(user=image.user, published__isnull=False, published__lt=image.published) \
                                     .order_by('-published')[0:1]
                elif nav_ctx == 'collection':
                    try:
                        try:
                            collection = image.collections.get(pk=nav_ctx_extra)
                        except ValueError:
                            # Maybe this image is in a single collection
                            collection = image.collections.all()[0]

                        if collection.order_by_tag:
                            collection_images = Image.objects \
                                .filter(user=image.user,
                                        collections=collection,
                                        keyvaluetags__key=collection.order_by_tag) \
                                .order_by('keyvaluetags__value')

                            current_index = 0
                            for iter_image in collection_images.all():
                                if iter_image.pk == image.pk:
                                    break
                                current_index += 1

                            image_next = collection_images.all()[current_index + 1] \
                                if current_index < collection_images.count() - 1 \
                                else None
                            image_prev = collection_images.all()[current_index - 1] \
                                if current_index > 0 \
                                else None
                        else:
                            image_next = Image.objects \
                                             .filter(user=image.user, collections=collection,
                                                     published__gt=image.published).order_by('published')[0:1]
                            image_prev = Image.objects \
                                             .filter(user=image.user, collections=collection,
                                                     published__lt=image.published).order_by('-published')[0:1]
                    except Collection.DoesNotExist:
                        # image_prev and image_next will remain None
                        pass
                elif nav_ctx == 'group':
                    try:
                        group = image.part_of_group_set.get(pk=nav_ctx_extra)
                        if group.public:
                            image_next = Image.objects \
                                             .filter(part_of_group_set=group,
                                                     published__isnull=False,
                                                     published__gt=image.published) \
                                             .order_by('published')[0:1]
                            image_prev = Image.objects \
                                             .filter(part_of_group_set=group,
                                                     published__isnull=False,
                                                     published__lt=image.published) \
                                             .order_by('-published')[0:1]
                    except (Group.DoesNotExist, ValueError):
                        # image_prev and image_next will remain None
                        pass
                elif nav_ctx == 'all':
                    image_next = Image.objects \
                                     .filter(published__isnull=False, published__gt=image.published) \
                                     .order_by('published')[0:1]
                    image_prev = Image.objects \
                                     .filter(published__isnull=False, published__lt=image.published) \
                                     .order_by('-published')[0:1]
            except Image.DoesNotExist:
                image_next = None
                image_prev = None

        if image_next and isinstance(image_next, QuerySet):
            image_next = image_next[0]
        if image_prev and isinstance(image_prev, QuerySet):
            image_prev = image_prev[0]

        #################
        # RESPONSE DICT #
        #################

        from astrobin_apps_platesolving.solver import Solver

        if skyplot_zoom1 and not skyplot_zoom1.name.startswith('images/'):
            skyplot_zoom1.name = 'images/' + skyplot_zoom1.name

        response_dict = context.copy()
        response_dict.update({
            'SHARE_PATH': settings.SHORT_BASE_URL,

            'alias': alias,
            'mod': mod,
            'revisions': ImageService(image) \
                .get_revisions() \
                .select_related('image__user__userprofile'),
            'revisions_with_title_or_description': ImageService(image) \
                .get_revisions_with_title_or_description() \
                .select_related('image__user__userprofile'),
            'is_revision': is_revision,
            'revision_image': revision_image,
            'revision_label': r,

            'instance_to_platesolve': instance_to_platesolve,
            'show_solution': (
                                     instance_to_platesolve.mouse_hover_image == MouseHoverImage.SOLUTION
                                     and instance_to_platesolve.solution
                                     and instance_to_platesolve.solution.status >= Solver.SUCCESS)
                             or (
                                     mod == 'solved'
                                     and instance_to_platesolve.solution
                                     and instance_to_platesolve.solution.status >= Solver.SUCCESS
                             ),
            'show_advanced_solution': (
                                              instance_to_platesolve.mouse_hover_image == MouseHoverImage.SOLUTION
                                              and instance_to_platesolve.solution
                                              and instance_to_platesolve.solution.status == Solver.ADVANCED_SUCCESS
                                      )
                                      or (
                                              mod == 'solved'
                                              and instance_to_platesolve.solution
                                              and instance_to_platesolve.solution.status >= Solver.ADVANCED_SUCCESS
                                      ),
            'advanced_solution_last_live_log_entry':
                PlateSolvingAdvancedLiveLogEntry.objects.filter(
                    serial_number=instance_to_platesolve.solution.pixinsight_serial_number) \
                    .order_by('-timestamp').first() \
                    if instance_to_platesolve.solution \
                    else None,
            'skyplot_zoom1': skyplot_zoom1,
            'pixinsight_finding_chart': pixinsight_finding_chart,
            'pixinsight_finding_chart_small': pixinsight_finding_chart_small,

            'image_ct': ContentType.objects.get_for_model(Image),
            'user_ct': ContentType.objects.get_for_model(User),
            'like_this': like_this,
            'user_can_like': can_like(self.request.user, image),
            'bookmarked_this': bookmarked_this,

            'comments_number': NestedComment.objects.filter(
                deleted=False,
                content_type__app_label='astrobin',
                content_type__model='image',
                object_id=image.id).count(),
            'gear_list': gear_list,
            'image_type': image_type,
            'ssa': ssa,
            'deep_sky_data': deep_sky_data,
            'promote_form': ImagePromoteForm(instance=image),
            'upload_revision_form': ImageRevisionUploadForm(),
            'upload_uncompressed_source_form': UncompressedSourceUploadForm(instance=image),
            'dates_label': _("Dates"),
            'show_contains': (image.subject_type == SubjectType.DEEP_SKY and subjects) or
                             (image.subject_type != SubjectType.DEEP_SKY),
            'subjects': subjects,
            'subject_type': ImageService(image).get_subject_type_label(),
            'hemisphere': ImageService(image).get_hemisphere(r),
            'constellation': ImageService.get_constellation(revision_image.solution) \
                if revision_image \
                else ImageService.get_constellation(image.solution),
            'resolution': '%dx%d' % (w, h) if (w and h) else None,
            'locations': locations,
            'solar_system_main_subject': ImageService(image).get_solar_system_main_subject_label(),
            'content_type': ContentType.objects.get(app_label='astrobin', model='image'),
            'preferred_languages': preferred_languages,
            'select_group_form': GroupSelectForm(
                user=self.request.user
            ) if self.request.user.is_authenticated else None,
            'in_public_groups': Group.objects.filter(Q(public=True, images=image)),
            'auto_submit_to_iotd_tp_process_form': AutoSubmitToIotdTpProcessForm() \
                if self.request.user.is_authenticated \
                else None,
            'image_next': image_next,
            'image_prev': image_prev,
            'nav_ctx': nav_ctx,
            'nav_ctx_extra': nav_ctx_extra,
            'w': w,
            'h': h,
            'image_uses_full_width': w is not None and w >= 940,
            'search_query': f'{self.request.GET.get("q", "")} {self.request.GET.get("telescope", "")} {self.request.GET.get("camera", "")}'.strip(),
        })

        return response_dict


@method_decorator([
    last_modified(CachingService.get_image_last_modified),
    cache_control(private=True, no_cache=True),
    vary_on_cookie
], name='dispatch')
class ImageFullView(ImageDetailView):
    model = Image
    pk_url_kwarg = 'id'
    template_name = 'image/full.html'
    template_name_suffix = ''

    def get_queryset(self):
        return Image.objects_including_wip.all()

    # TODO: unify this with ImageDetailView.dispatch
    def dispatch(self, request, *args, **kwargs):
        # Redirect to the correct revision
        image = self.get_object()

        if image.moderator_decision == 2:
            raise Http404

        self.revision_label = kwargs['r']
        if self.revision_label != '0':
            try:
                revision = image.revisions.get(label=self.revision_label)
            except ImageRevision.DoesNotExist:
                pass

        if self.revision_label is None:
            # No revision specified, let's see if we need to redirect to the
            # final.
            if not image.is_final:
                final = image.revisions.filter(is_final=True)
                if final.count() > 0:
                    url = reverse_lazy(
                        'image_full',
                        args=(image.get_id(), final[0].label,))
                    if 'nc' in request.GET:
                        url += '?nc=%s' % request.GET.get('nc')
                        if 'nce' in request.GET:
                            url += '&nce=%s' % request.GET.get('nce')
                    return redirect(url)

            try:
                self.revision_label = image.revisions.filter(is_final=True)[0].label
            except IndexError:
                self.revision_label = '0'

        return super(ImageFullView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ImageFullView, self).get_context_data(**kwargs)

        image = self.get_object()

        mod = self.request.GET.get('mod')
        real = 'real' in self.request.GET and can_see_real_resolution(self.request.user, image)
        if real:
            alias = 'real'
        else:
            alias = 'hd' if not image.sharpen_thumbnails else 'hd_sharpened'

        if mod in settings.AVAILABLE_IMAGE_MODS:
            alias += "_%s" % mod

        response_dict = context.copy()
        response_dict.update({
            'real': real,
            'alias': alias,
            'mod': mod,
            'revision_label': self.revision_label,
            'max_file_size_before_warning': 25 * 1024 * 1024,
        })

        return response_dict


class ImageDeleteView(LoginRequiredMixin, ImageDeleteViewBase):
    model = Image
    pk_url_kwarg = 'id'

    def get_queryset(self):
        return Image.objects_including_wip.all()

    # I would like to use braces' UserPassesTest for this, but I can't
    # get_object from there because the view is not dispatched yet.
    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()

        if request.user.is_authenticated and request.user != image.user and not request.user.is_superuser:
            raise PermissionDenied

        return super(ImageDeleteView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('user_page', args=(self.request.user,))

    def post(self, *args, **kwargs):
        image = self.get_object()

        image.thumbnail_invalidate()
        for revision in image.revisions.all():
            revision.thumbnail_invalidate()

        messages.success(self.request, _("Image deleted."))
        return super(ImageDeleteView, self).post(args, kwargs)


class ImageRevisionDeleteView(LoginRequiredMixin, DeleteView):
    model = ImageRevision
    pk_url_kwarg = 'id'

    # I would like to use braces' UserPassesTest for this, but I can't
    # get_object from there because the view is not dispatched yet.
    def dispatch(self, request, *args, **kwargs):
        try:
            revision = ImageRevision.objects.get(pk=kwargs[self.pk_url_kwarg])
        except ImageRevision.DoesNotExist:
            raise Http404

        if request.user.is_authenticated and request.user != revision.image.user:
            raise PermissionDenied

        # Save this so it's accessible in get_success_url
        self.image = revision.image

        return super(ImageRevisionDeleteView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('image_detail', args=(self.image.get_id(),))

    def post(self, *args, **kwargs):
        revision = self.get_object()
        image = revision.image

        if revision.is_final:
            image.is_final = True
            image.save(keep_deleted=True)
            revision.is_final = False
            revision.save(keep_deleted=True)

        revision.thumbnail_invalidate()
        messages.success(self.request, _("Revision deleted."))

        return super(ImageRevisionDeleteView, self).post(args, kwargs)


class ImageDeleteOriginalView(ImageDeleteView):
    model = Image
    pk_url_kwarg = 'id'

    def get_success_url(self):
        return self.image.get_absolute_url()

    def post(self, *args, **kwargs):
        self.image = self.get_object()

        revisions = ImageService(self.image).get_revisions()
        if not revisions.exists():
            return HttpResponseBadRequest()

        ImageService(self.image).delete_original()
        messages.success(self.request, _("Original version deleted!"));
        # We do not call super, because that would delete the Image
        return HttpResponseRedirect(self.get_success_url())


class ImageDeleteOtherVersionsView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        image = Image.objects_including_wip.get(pk=kwargs.get('id'))  # type: Image

        if self.request.user != image.user and not self.request.user.is_superuser:
            return HttpResponseForbidden()

        revisions = ImageRevision.all_objects.filter(image=image)

        if not revisions:
            return HttpResponseBadRequest()

        revision_label = self.request.POST.get('revision', None)
        image_modified = False

        if revision_label:
            # Delete all other revisions, and original.
            revision = ImageRevision.objects.get(image=image, label=revision_label)  # type: ImageRevision

            image.thumbnail_invalidate()
            image.image_file = revision.image_file
            image.updated = revision.uploaded
            image.w = revision.w
            image.h = revision.h

            if revision.title:
                image.title = f'{image.title} ({revision.title})'

            if revision.description:
                image.description = (image.description or '') + '\n' + revision.description

            image_modified = True

            if revision.solution:
                if image.solution:
                    image.solution.delete()
                content_type = ContentType.objects.get_for_model(ImageRevision)
                solution = Solution.objects.get(content_type=content_type, object_id=revision.pk)
                solution.content_object = image
                solution.save()

        for revision in ImageRevision.all_objects.filter(image=image).iterator():
            revision.thumbnail_invalidate()
            revision.delete()

        if not image.is_final:
            image.is_final = True
            image_modified = True

        if image_modified:
            image.save(keep_deleted=True)

        return HttpResponseRedirect(
            reverse_lazy('image_detail', args=(image.get_id(),))
        )


class ImageDemoteView(LoginRequiredMixin, ImageUpdateViewBase):
    form_class = ImageDemoteForm
    model = Image
    pk_url_kwarg = 'id'
    http_method_names = ('post',)

    def get_queryset(self):
        return self.model.objects_including_wip.all()

    def get_success_url(self):
        return self.object.get_absolute_url()

    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()

        if request.user.is_authenticated and request.user != image.user and not request.user.is_superuser:
            raise PermissionDenied

        return super(ImageDemoteView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        image = self.get_object()
        if not image.is_wip:
            image.is_wip = True
            image.save(keep_deleted=True)
            messages.success(request, _("Image moved to the staging area."))

        return super(ImageDemoteView, self).post(request, args, kwargs)


class ImagePromoteView(LoginRequiredMixin, ImageUpdateViewBase):
    form_class = ImagePromoteForm
    model = Image
    pk_url_kwarg = 'id'
    http_method_names = ('post',)

    def get_queryset(self):
        return self.model.objects_including_wip.all()

    def get_success_url(self):
        return self.object.get_absolute_url()

    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()

        if request.user.is_authenticated and request.user != image.user and not request.user.is_superuser:
            raise PermissionDenied

        return super(ImagePromoteView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        image = self.get_object()
        if image.is_wip:
            skip_notifications = request.POST.get('skip_notifications', 'off').lower() == 'on'
            previously_published = image.published
            image.is_wip = False
            image.save(keep_deleted=True)

            if not previously_published:
                if not skip_notifications:
                    push_notification_for_new_image.apply_async(args=(request.user.pk, image.pk,), countdown=10)
                add_story(image.user, verb='VERB_UPLOADED_IMAGE', action_object=image)

            messages.success(request, _("Image moved to the public area."))

        return super(ImagePromoteView, self).post(request, args, kwargs)


class ImageEditBaseView(LoginRequiredMixin, ImageUpdateViewBase):
    model = Image
    pk_url_kwarg = 'id'
    template_name_suffix = ''
    context_object_name = 'image'

    def get_queryset(self):
        return self.model.objects_including_wip.all()

    def get_success_url(self):
        return self.object.get_absolute_url()

    def dispatch(self, request, *args, **kwargs):
        if settings.READONLY_MODE:
            raise PermissionDenied

        image = self.get_object()

        if request.user.is_authenticated and request.user != image.user and not request.user.is_superuser:
            raise PermissionDenied

        return super(ImageEditBaseView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, _("Form saved. Thank you!"))
        return super(ImageEditBaseView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _(
            "There was one or more errors processing the form. " +
            "You may need to scroll down to see them."))
        return super(ImageEditBaseView, self).form_invalid(form)


class ImageEditBasicView(ImageEditBaseView):
    form_class = ImageEditBasicForm
    template_name = 'image/edit/basic.html'

    def get_success_url(self):
        image = self.get_object()
        if 'submit_gear' in self.request.POST:
            return reverse_lazy('image_edit_gear', kwargs={'id': image.get_id()}) + "?upload"

        return image.get_absolute_url()

    def post(self, request, *args, **kwargs):
        image = self.get_object()  # type: Image
        previous_url = image.image_file.url

        ret = super(ImageEditBasicView, self).post(request, *args, **kwargs)

        image = self.get_object()  # type: Image
        new_url = image.image_file.url

        if new_url != previous_url:
            try:
                image.w, image.h = get_image_dimensions(image.image_file)
            except TypeError as e:
                logger.warning("ImageEditBaseView: unable to get image dimensions for %d: %s" % (image.pk, str(e)))
                pass

            image.square_cropping = ImageService(image).get_default_cropping()
            image.save(keep_deleted=True)

            image.thumbnail_invalidate()

            if image.solution:
                image.solution.delete()

        return ret


class ImageEditGearView(ImageEditBaseView):
    form_class = ImageEditGearForm
    template_name = 'image/edit/gear.html'

    def get_context_data(self, **kwargs):
        context = super(ImageEditGearView, self).get_context_data(**kwargs)

        user = self.get_object().user
        profile = user.userprofile

        context['no_gear'] = profile.telescopes.count() == 0 and profile.cameras.count() == 0
        context['copy_gear_form'] = CopyGearForm(user)
        return context

    def get_success_url(self):
        image = self.object
        if 'submit_acquisition' in self.request.POST:
            return reverse_lazy('image_edit_acquisition', kwargs={'id': image.get_id()}) + "?upload"

        return image.get_absolute_url()

    def get_form(self, form_class=None):
        image = self.get_object()

        if form_class is None:
            form_class = self.get_form_class()

        if self.request.method == 'POST':
            return form_class(
                user=image.user, instance=image, data=self.request.POST)
        else:
            return form_class(user=image.user, instance=image)


class ImageEditRevisionView(LoginRequiredMixin, UpdateView):
    model = ImageRevision
    pk_url_kwarg = 'id'
    template_name = 'image/edit/revision.html'
    context_object_name = 'revision'
    form_class = ImageEditRevisionForm

    def get_initial(self):
        revision = self.get_object()  # type: ImageRevision

        square_cropping = revision.square_cropping
        if square_cropping == '0,0,0,0':
            square_cropping = ImageService(revision.image).get_default_cropping(revision.label)

        return {
            'square_cropping': square_cropping,
            'mouse_hover_image': revision.image.mouse_hover_image
        }

    def get_success_url(self):
        return reverse_lazy('image_detail', args=(self.object.image.get_id(),))

    def dispatch(self, request, *args, **kwargs):
        try:
            revision = self.model.objects.get(pk=kwargs[self.pk_url_kwarg])
        except self.model.DoesNotExist:
            raise Http404

        if request.user.is_authenticated and request.user != revision.image.user and not request.user.is_superuser:
            raise PermissionDenied

        return super(ImageEditRevisionView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, _("Form saved. Thank you!"))
        return super(ImageEditRevisionView, self).form_valid(form)

    def post(self, request, *args, **kwargs):
        revision = self.get_object()  # type: ImageRevision
        previous_url = revision.image_file.url
        previous_square_cropping = revision.square_cropping

        ret = super(ImageEditRevisionView, self).post(request, *args, **kwargs)

        revision = self.get_object()
        new_url = revision.image_file.url

        if new_url != previous_url:
            try:
                revision.w, revision.h = get_image_dimensions(revision.image_file)
            except TypeError as e:
                logger.warning(
                    "ImageEditRevisionView: unable to get image dimensions for %d: %s" % (revision.pk, str(e)))
                pass

            revision.square_cropping = ImageService(revision.image).get_default_cropping(revision.label)
            revision.save(keep_deleted=True)

            revision.thumbnail_invalidate()

        if previous_square_cropping != revision.square_cropping:
            revision.thumbnail_invalidate()

        return ret


class ImageEditThumbnailsView(ImageEditBaseView):
    form_class = ImageEditThumbnailsForm
    template_name = 'image/edit/thumbnails.html'

    def get_initial(self):
        image = self.get_object()  # type: Image

        square_cropping = image.square_cropping
        if square_cropping == '0,0,0,0':
            square_cropping = ImageService(image).get_default_cropping()

        return {
            'square_cropping': square_cropping
        }

    def get_success_url(self):
        image = self.get_object()
        if 'submit_watermark' in self.request.POST:
            return reverse_lazy('image_edit_watermark', kwargs={'id': image.get_id()}) + "?upload"
        return image.get_absolute_url()

    def post(self, request, *args, **kwargs):
        image: Image = self.get_object()
        image.thumbnail_invalidate()

        return super(ImageEditThumbnailsView, self).post(request, *args, **kwargs)


class ImageUploadUncompressedSource(ImageEditBaseView):
    form_class = UncompressedSourceUploadForm

    def form_valid(self, form):
        if 'clear' in self.request.POST:
            self.object.uncompressed_source_file.delete()
            self.object.uncompressed_source_file = None
            self.object.save(keep_deleted=True)
            msg = "File removed. Thank you!"
        else:
            msg = "File uploaded. In the future, you can download this file from your technical card down below. " \
                  "Thank you!"

        self.object = form.save()
        messages.success(self.request, _(msg))
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, form.errors["uncompressed_source_file"])
        return redirect(self.get_success_url())


class ImageDownloadView(View):
    def download(self, url):
        response = requests.get(
            url,
            allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        content_type = mimetypes.guess_type(os.path.basename(url))

        ret = HttpResponse(response.content, content_type=content_type)
        ret['Content-Disposition'] = 'inline; filename=' + os.path.basename(url)
        return ret

    def dispatch(self, request, *args, **kwargs):
        id: Union[str, int] = self.kwargs.get('id')
        image: Image = ImageService.get_object(id, Image.objects_including_wip)

        if image is None:
            raise Http404

        if not ImageService(image).display_download_menu(request.user):
            return render(request, "403.html", {})

        return super().dispatch(request, args, kwargs)

    def get(self, request, *args, **kwargs) -> HttpResponse:
        id: Union[str, int] = self.kwargs.pop('id')
        revision_label: str = self.kwargs.pop('revision_label')
        version: str = self.kwargs.pop('version')

        image: Image = ImageService.get_object(id, Image.objects_including_wip)
        revision: Optional[ImageRevision] = None

        if image is None:
            raise Http404

        if revision_label not in (None, 0, '0'):
            try:
                revision = ImageService(image).get_revision(revision_label)
            except ImageRevision.DoesNotExist:
                raise Http404

        if version == 'original':
            if request.user != image.user and not request.user.is_superuser:
                return render(request, "403.html", {})
            return self.download(revision.image_file.url if revision else image.image_file.url)

        if version == 'basic_annotations':
            return self.download(revision.solution.image_file.url if revision else image.solution.image_file.url)

        if version == 'advanced_annotations':
            solution: Solution = revision.solution if revision and revision.solution else image.solution

            # Download SVG
            response = requests.get(
                f'{settings.MEDIA_URL}{solution.pixinsight_svg_annotation_hd}',
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            local_svg: NamedTemporaryFile = NamedTemporaryFile('w+b', suffix='.svg', delete=False)
            for block in response.iter_content(1024 * 8):
                if not block:
                    break
                local_svg.write(block)
            local_svg.seek(0)
            local_svg.close()

            # Download HD thumbnail
            thumbnail_url = image.thumbnail('hd', revision_label, sync=True)
            response = requests.get(
                thumbnail_url,
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            local_hd: NamedTemporaryFile = NamedTemporaryFile('w+b', delete=False)
            for block in response.iter_content(1024 * 8):
                if not block:
                    break
                local_hd.write(block)
            local_hd.seek(0)
            local_hd.close()

            # Build image
            local_result: NamedTemporaryFile = NamedTemporaryFile('w+b', suffix='.png', delete=False)
            svg2png(url=local_svg.name, write_to=local_result.name)
            local_result.seek(0)
            local_result.close()

            background = PILImage.open(local_hd.name)
            foreground = PILImage.open(local_result.name)

            icc_profile = background.info.get('icc_profile')
            background.paste(foreground, (0, 0), foreground)

            if background.mode != 'RGBA':
                local_result.name = local_result.name.replace('.png', '.jpg')
                save_format = 'JPEG'
            else:
                save_format = 'PNG'
            background.save(local_result.name, format=save_format, icc_profile=icc_profile)

            result_path: str = f'tmp/{solution.pixinsight_serial_number}-{int(time.time())}.jpg'

            with open(local_result.name, 'rb') as result_file:
                session = boto3.session.Session(
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                s3 = session.resource('s3')
                s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME).put_object(Key=result_path, Body=result_file)

            response = self.download(f'https://{settings.AWS_STORAGE_BUCKET_NAME}/{result_path}')

            os.unlink(local_svg.name)
            os.unlink(local_hd.name)
            os.unlink(local_result.name)

            return response

        thumbnail_url = image.thumbnail(version, revision_label, sync=True)
        return self.download(thumbnail_url)


class ImageSubmitToIotdTpProcessView(View):
    def dispatch(self, request, *args, **kwargs):
        id: Union[str, int] = self.kwargs.get('id')
        image: Image = ImageService.get_object(id, Image)

        if image is None:
            raise Http404

        return super().dispatch(request, args, kwargs)

    def post(self, request, *args, **kwargs):
        id: Union[str, int] = self.kwargs.get('id')
        auto_submit = request.POST.get('auto_submit_to_iotd_tp_process') == 'on'
        image: Image = ImageService.get_object(id, Image)

        may, reason = IotdService.submit_to_iotd_tp_process(request.user, image, auto_submit)

        if not may:
            if reason == 'UNAUTHENTICATED' or reason == 'NOT_OWNER':
                return render(request, "403.html", {})
            elif reason == 'NOT_PUBLISHED':
                return HttpResponseBadRequest("This image has not been published yet.")
            elif reason == 'ALREADY_SUBMITTED':
                return HttpResponseBadRequest("This image has already been submitted to the IOTD/TP process.")
            elif reason == 'EXCLUDED_FROM_COMPETITION':
                return HttpResponseBadRequest(
                    "This image cannot be submitted to the IOTD/TP process because the user has selected to be excluded "
                    "from competitions."
                )
            elif reason == 'BANNED_FROM_COMPETITIONS':
                return HttpResponseBadRequest(
                    "This image cannot be submitted to the IOTD/TP process because the user has been banned from "
                    "competitions."
                )
            elif reason == 'TOO_LATE':
                return HttpResponseBadRequest(
                    "Too late: images can be submitted to the IOTD/TP process only %s days after publication." % (
                        settings.IOTD_SUBMISSION_WINDOW_DAYS
                    )
                )
            else:
                return HttpResponseBadRequest("Unknown error")

        messages.success(request, _("Image submitted to the IOTD/TP process!"))
        return HttpResponseRedirect(request.POST.get('next'))
