import re
from datetime import datetime

from braces.views import (
    JSONResponseMixin,
    LoginRequiredMixin,
)
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import PermissionDenied
from django.core.files.images import get_image_dimensions
from django.core.urlresolvers import reverse_lazy, reverse
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.encoding import iri_to_uri, smart_unicode
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.views.generic import (
    DeleteView,
    DetailView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin
from silk.profiling.profiler import silk_profile

from astrobin.enums import SubjectType
from astrobin.forms import (
    CopyGearForm,
    ImageDemoteForm,
    ImageEditBasicForm,
    ImageEditGearForm,
    ImageEditRevisionForm,
    ImageFlagThumbsForm,
    ImagePromoteForm,
    ImageRevisionUploadForm,
    PrivateMessageForm,
    ImageEditThumbnailsForm,
    ImageEditCorruptedRevisionForm)
from astrobin.forms.uncompressed_source_upload_form import UncompressedSourceUploadForm
from astrobin.models import (
    Collection,
    Image, ImageRevision,
    DeepSky_Acquisition,
    SolarSystem_Acquisition,
    UserProfile,
    LANGUAGES,
    LICENSE_CHOICES,
)
from astrobin.stories import add_story
from astrobin.templatetags.tags import can_like
from astrobin.utils import to_user_timezone, get_image_resolution
from astrobin_apps_groups.forms import GroupSelectForm
from astrobin_apps_groups.models import Group
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import Iotd
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.services import SolutionService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import can_see_real_resolution
from nested_comments.models import NestedComment
from toggleproperties.models import ToggleProperty


class ImageSingleObjectMixin(SingleObjectMixin):
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        id = self.kwargs.get(self.pk_url_kwarg)

        # hashes will always have at least a letter
        if id.isdigit():
            # old style numerical pk
            image = super(ImageSingleObjectMixin, self).get_object(queryset)
            if image is not None:
                # if an image has a hash, we don't allow getting it by pk
                if image.hash is not None:
                    raise Http404
                return image

        # we always allow getting by hash
        queryset = queryset.filter(hash=id)
        try:
            image = queryset.get()
        except queryset.model.DoesNotExist:
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


class ImageThumbView(JSONResponseMixin, ImageDetailViewBase):
    model = Image
    queryset = Image.all_objects.all()
    pk_url_kwarg = 'id'

    def get(self, request, *args, **kwargs):
        image = self.get_object()

        alias = kwargs.pop('alias')
        r = kwargs.pop('r')
        if r is None:
            r = 'final'

        force = request.GET.get('force')
        if force is not None:
            image.thumbnail_invalidate()

        opts = {
            'revision_label': r,
            'animated': 'animated' in self.request.GET,
            'insecure': 'insecure' in self.request.GET,
        }

        sync = request.GET.get('sync')
        if sync is not None:
            opts['sync'] = True

        url = image.thumbnail(alias, opts)

        return self.render_json_response({
            'id': image.pk,
            'alias': alias,
            'revision': r,
            'url': iri_to_uri(url)
        })


class ImageRawThumbView(ImageDetailViewBase):
    model = Image
    queryset = Image.objects_including_wip.all()
    pk_url_kwarg = 'id'

    def get(self, request, *args, **kwargs):
        image = self.get_object()
        alias = kwargs.pop('alias')
        r = kwargs.pop('r')
        opts = {
            'revision_label': r,
            'animated': 'animated' in self.request.GET,
            'insecure': 'insecure' in self.request.GET,
        }

        force = request.GET.get('force')
        if force is not None:
            image.thumbnail_invalidate()

        sync = request.GET.get('sync')
        if sync is not None:
            opts['sync'] = True

        if settings.TESTING:
            thumb = image.thumbnail_raw(alias, opts)
            if thumb:
                return redirect(thumb.url)
            return None

        url = image.thumbnail(alias, opts)
        return redirect(smart_unicode(url))


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
            if not request.user.is_authenticated() or \
                    not request.user.is_superuser and \
                    not request.user.userprofile.is_image_moderator():
                raise Http404

        revision_label = kwargs.get('r')
        if image.corrupted and (revision_label == '0' or (revision_label in [None, 'final'] and image.is_final)):
            if request.user == image.user:
                return redirect(reverse('image_edit_basic', args=(image.get_id(),)) + '?corrupted')
            else:
                raise Http404

        if revision_label != '0':
            try:
                revision = image.revisions.get(label=revision_label)
                if revision.corrupted:
                    if request.user == image.user:
                        return redirect(reverse('image_edit_revision', args=(revision.pk,)) + '?corrupted')
                    else:
                        raise Http404
            except ImageRevision.DoesNotExist:
                pass

        if revision_label is None:
            # No revision specified, let's see if we need to redirect to the
            # final.
            if image.is_final == False:
                final = image.revisions.filter(is_final=True)
                if final.count() > 0:
                    url = reverse_lazy(
                        'image_detail',
                        args=(image.get_id(), final[0].label,))
                    if 'ctx' in request.GET:
                        url += '?ctx=%s' % request.GET.get('ctx')
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
        from astrobin.moon import MoonPhase;

        gear_list = (
            (ungettext('Imaging telescope or lens',
                       'Imaging telescopes or lenses',
                       len(image.imaging_telescopes.all())),
             image.imaging_telescopes.all(), 'imaging_telescopes'),
            (ungettext('Imaging camera',
                       'Imaging cameras',
                       len(image.imaging_cameras.all())),
             image.imaging_cameras.all(), 'imaging_cameras'),
            (ungettext('Mount',
                       'Mounts',
                       len(image.mounts.all())),
             image.mounts.all(), 'mounts'),
            (ungettext('Guiding telescope or lens',
                       'Guiding telescopes or lenses',
                       len(image.guiding_telescopes.all())),
             image.guiding_telescopes.all(), 'guiding_telescopes'),
            (ungettext('Guiding camera',
                       'Guiding cameras',
                       len(image.guiding_cameras.all())),
             image.guiding_cameras.all(), 'guiding_cameras'),
            (ungettext('Focal reducer',
                       'Focal reducers',
                       len(image.focal_reducers.all())),
             image.focal_reducers.all(), 'focal_reducers'),
            (_('Software'), image.software.all(), 'software'),
            (ungettext('Filter',
                       'Filters',
                       len(image.filters.all())),
             image.filters.all(), 'filters'),
            (ungettext('Accessory',
                       'Accessories',
                       len(image.accessories.all())),
             image.accessories.all(), 'accessories'),
        )

        gear_list_has_commercial = False
        gear_list_has_paid_commercial = False
        for g in gear_list:
            if g[1].exclude(commercial=None).count() > 0:
                gear_list_has_commercial = True
                break
        for g in gear_list:
            for i in g[1].exclude(commercial=None):
                if i.commercial.is_paid() or i.commercial.producer == self.request.user:
                    gear_list_has_paid_commercial = True
                    # It would be faster if we exited the outer loop, but really,
                    # how many gear items can an image have?
                    break

        makes_list = ','.join(
            filter(None, reduce(
                lambda x, y: x + y,
                [list(x.values_list('make', flat=True)) for x in [y[1] for y in gear_list]])))

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
                    if a.filter:
                        key = "filter(%s)" % a.filter.get_name()
                    if a.iso:
                        key += '-ISO(%d)' % a.iso
                    if a.gain:
                        key += '-gain(%.2f)' % a.gain
                    if a.sensor_cooling:
                        key += '-temp(%d)' % a.sensor_cooling
                    if a.binning:
                        key += '-bin(%d)' % a.binning
                    key += '-duration(%d)' % a.duration

                    try:
                        current_frames = dsa_data['frames'][key]['integration']
                    except KeyError:
                        current_frames = '0x0"'

                    integration_re = re.match(r'^(\d+)x(\d+)"$', current_frames)
                    current_number = int(integration_re.group(1))

                    dsa_data['frames'][key] = {}
                    dsa_data['frames'][key]['filter_url'] = a.filter.get_absolute_url() if a.filter else '#'
                    dsa_data['frames'][key]['filter'] = a.filter if a.filter else ''
                    dsa_data['frames'][key]['iso'] = 'ISO%d' % a.iso if a.iso else ''
                    dsa_data['frames'][key]['gain'] = '(gain: %.2f)' % a.gain if a.gain else ''
                    dsa_data['frames'][key]['sensor_cooling'] = '%dC' % a.sensor_cooling if a.sensor_cooling else ''
                    dsa_data['frames'][key]['binning'] = 'bin %sx%s' % (a.binning, a.binning) if a.binning else ''
                    dsa_data['frames'][key]['integration'] = '%sx%s"' % (current_number + a.number, a.duration)

                    dsa_data['integration'] += (a.duration * a.number / 3600.0)

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
                 u'\n'.join("%s %s" % (
                     "<a href=\"%s\">%s</a>:" % (f[1]['filter_url'], f[1]['filter']) if f[1]['filter'] else '',
                     "%s %s %s %s %s" % (
                         f[1]['integration'], f[1]['iso'], f[1]['gain'], f[1]['sensor_cooling'], f[1]['binning']),
                 ) for f in frames_list)),
                (_('Integration'), "%.1f %s" % (dsa_data['integration'], _("hours"))),
                (_('Darks'),
                 '~%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['darks'])) / len(dsa_data['darks'])) if
                 dsa_data['darks'] else 0),
                (_('Flats'),
                 '~%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['flats'])) / len(dsa_data['flats'])) if
                 dsa_data['flats'] else 0),
                (_('Flat darks'), '~%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['flat_darks'])) / len(
                    dsa_data['flat_darks'])) if dsa_data['flat_darks'] else 0),
                (_('Bias'),
                 '~%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['bias'])) / len(dsa_data['bias'])) if
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
        if self.request.user.is_authenticated():
            profile = self.request.user.userprofile

        ##############
        # BASIC DATA #
        ##############

        published_on = \
            to_user_timezone(image.uploaded, profile) \
                if profile else image.uploaded
        if image.published:
            published_on = \
                to_user_timezone(image.published, profile) \
                    if profile else image.published

        alias = 'regular' if not image.sharpen_thumbnails else 'regular_sharpened'
        mod = self.request.GET.get('mod')
        if mod == 'inverted':
            alias = 'regular_inverted'

        subjects = []
        skyplot_zoom1 = None

        if image.solution:
            subjects = SolutionService(image.solution).get_objects_in_field()
            skyplot_zoom1 = image.solution.skyplot_zoom1

        if is_revision and revision_image.solution:
            subjects = SolutionService(revision_image.solution).get_objects_in_field()
            if revision_image.solution.skyplot_zoom1:
                skyplot_zoom1 = revision_image.solution.skyplot_zoom1

        licenses = (
            (0, 'cc/c.png', LICENSE_CHOICES[0][1]),
            (1, 'cc/cc-by-nc-sa.png', LICENSE_CHOICES[1][1]),
            (2, 'cc/cc-by-nc.png', LICENSE_CHOICES[2][1]),
            (3, 'cc/cc-by-nc-nd.png', LICENSE_CHOICES[3][1]),
            (4, 'cc/cc-by.png', LICENSE_CHOICES[4][1]),
            (5, 'cc/cc-by-sa.png', LICENSE_CHOICES[5][1]),
            (6, 'cc/cc-by-nd.png', LICENSE_CHOICES[6][1]),
        )

        locations = '; '.join([u'%s' % (x) for x in image.locations.all()])

        ######################
        # PREFERRED LANGUAGE #
        ######################

        preferred_language = image.user.userprofile.language
        if preferred_language:
            try:
                preferred_language = LANGUAGES[preferred_language]
            except KeyError:
                preferred_language = _("English")
        else:
            preferred_language = _("English")

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
        try:
            nav_ctx = self.request.GET.get('nc')
            if nav_ctx is None:
                nav_ctx = self.request.session.get('nav_ctx')
            if nav_ctx is None:
                nav_ctx = 'user'

            nav_ctx_extra = self.request.GET.get('nce')
            if nav_ctx_extra is None:
                nav_ctx_extra = self.request.session.get('nav_ctx_extra')

            # Always only lookup public, non corrupted images!
            if nav_ctx == 'user':
                image_next = Image.objects \
                                 .exclude(corrupted=True) \
                                 .filter(user=image.user, pk__gt=image.pk).order_by('pk')[0:1]
                image_prev = Image.objects \
                                 .exclude(corrupted=True) \
                                 .filter(user=image.user, pk__lt=image.pk).order_by('-pk')[0:1]
            elif nav_ctx == 'collection':
                try:
                    try:
                        collection = image.collections.get(pk=nav_ctx_extra)
                    except ValueError:
                        # Maybe this image is in a single collection
                        collection = image.collections.all()[0]

                    if collection.order_by_tag:
                        collection_images = Image.objects \
                            .exclude(corrupted=True) \
                            .filter(user=image.user, collections=collection, keyvaluetags__key=collection.order_by_tag) \
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
                                         .exclude(corrupted=True) \
                                         .filter(user=image.user, collections=collection,
                                                 pk__gt=image.pk).order_by('pk')[0:1]
                        image_prev = Image.objects \
                                         .exclude(corrupted=True) \
                                         .filter(user=image.user, collections=collection,
                                                 pk__lt=image.pk).order_by('-pk')[0:1]
                except Collection.DoesNotExist:
                    # image_prev and image_next will remain None
                    pass
            elif nav_ctx == 'group':
                try:
                    group = image.part_of_group_set.get(pk=nav_ctx_extra)
                    if group.public:
                        image_next = Image.objects \
                                         .exclude(corrupted=True) \
                                         .filter(part_of_group_set=group, pk__gt=image.pk).order_by('pk')[0:1]
                        image_prev = Image.objects \
                                         .exclude(corrupted=True) \
                                         .filter(part_of_group_set=group, pk__lt=image.pk).order_by('-pk')[0:1]
                except Group.DoesNotExist:
                    # image_prev and image_next will remain None
                    pass
            elif nav_ctx == 'all':
                image_next = Image.objects.exclude(corrupted=True).filter(pk__gt=image.pk).order_by('pk')[0:1]
                image_prev = Image.objects.exclude(corrupted=True).filter(pk__lt=image.pk).order_by('-pk')[0:1]
            elif nav_ctx == 'iotd':
                try:
                    iotd = Iotd.objects.get(image=image)
                    iotd_next = Iotd.objects \
                                    .exclude(image__corrupted=True) \
                                    .filter(date__gt=iotd.date, date__lte=datetime.now().date()) \
                                    .order_by('date')[0:1]
                    iotd_prev = Iotd.objects \
                                    .exclude(image__corrupted=True) \
                                    .filter(date__lt=iotd.date, date__lte=datetime.now().date()) \
                                    .order_by('-date')[0:1]

                    if iotd_next:
                        image_next = [iotd_next[0].image]
                    if iotd_prev:
                        image_prev = [iotd_prev[0].image]
                except Iotd.DoesNotExist:
                    pass
            elif nav_ctx == 'picks':
                picks = Image.objects.exclude(iotdvote=None, corrupted=True).filter(iotd=None)
                image_next = picks.filter(pk__gt=image.pk).order_by('pk')[0:1]
                image_prev = picks.filter(pk__lt=image.pk).order_by('-pk')[0:1]
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
                .get_revisions(include_corrupted=self.request.user == image.user) \
                .select_related('image__user__userprofile'),
            'revisions_with_description': ImageService(image) \
                .get_revisions_with_description(include_corrupted=self.request.user == image.user) \
                .select_related('image__user__userprofile'),
            'is_revision': is_revision,
            'revision_image': revision_image,
            'revision_label': r,

            'instance_to_platesolve': instance_to_platesolve,
            'show_solution': instance_to_platesolve.mouse_hover_image == "SOLUTION"
                             and instance_to_platesolve.solution
                             and instance_to_platesolve.solution.status >= Solver.SUCCESS,
            'show_advanced_solution': instance_to_platesolve.mouse_hover_image == "SOLUTION"
                                      and instance_to_platesolve.solution
                                      and instance_to_platesolve.solution.status == Solver.ADVANCED_SUCCESS,
            'skyplot_zoom1': skyplot_zoom1,

            'image_ct': ContentType.objects.get_for_model(Image),
            'like_this': like_this,
            'user_can_like': can_like(self.request.user, image),
            'bookmarked_this': bookmarked_this,
            'min_index_to_like': settings.MIN_INDEX_TO_LIKE,

            'comments_number': NestedComment.objects.filter(
                deleted=False,
                content_type__app_label='astrobin',
                content_type__model='image',
                object_id=image.id).count(),
            'gear_list': gear_list,
            'makes_list': makes_list,
            'gear_list_has_commercial': gear_list_has_commercial,
            'gear_list_has_paid_commercial': gear_list_has_paid_commercial,
            'image_type': image_type,
            'ssa': ssa,
            'deep_sky_data': deep_sky_data,
            'private_message_form': PrivateMessageForm(),
            'upload_revision_form': ImageRevisionUploadForm(),
            'upload_uncompressed_source_form': UncompressedSourceUploadForm(instance=image),
            'dates_label': _("Dates"),
            'published_on': published_on,
            'show_contains': (image.subject_type == SubjectType.DEEP_SKY and subjects) or
                             (image.subject_type != SubjectType.DEEP_SKY),
            'subjects': subjects,
            'subject_type': ImageService(image).get_subject_type_label(),
            'license_icon': static('astrobin/icons/%s' % licenses[image.license][1]),
            'license_title': licenses[image.license][2],
            'resolution': '%dx%d' % (w, h) if (w and h) else None,
            'locations': locations,
            'solar_system_main_subject': ImageService(image).get_solar_system_main_subject_label(),
            'content_type': ContentType.objects.get(app_label='astrobin', model='image'),
            'preferred_language': preferred_language,
            'select_group_form': GroupSelectForm(
                user=self.request.user) if self.request.user.is_authenticated() else None,
            'in_public_groups': Group.objects.filter(Q(public=True, images=image)),
            'image_next': image_next,
            'image_prev': image_prev,
            'nav_ctx': nav_ctx,
            'nav_ctx_extra': nav_ctx_extra,
        })

        return response_dict


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

        if image.corrupted and (
                self.revision_label == '0' or (self.revision_label in [None, 'final'] and image.is_final)):
            if request.user == image.user:
                return redirect(reverse('image_edit_basic', args=(image.get_id(),)) + '?corrupted')
            else:
                raise Http404

        if self.revision_label != '0':
            try:
                revision = image.revisions.get(label=self.revision_label)
                if revision.corrupted:
                    if request.user == image.user:
                        return redirect(reverse('image_edit_revision', args=(revision.pk,)) + '?corrupted')
                    else:
                        raise Http404
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
                    if 'ctx' in request.GET:
                        url += '?ctx=%s' % request.GET.get('ctx')
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

        if request.user.is_authenticated() and request.user != image.user and not request.user.is_superuser:
            raise PermissionDenied

        return super(ImageDeleteView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('user_page', args=(self.request.user,))

    def post(self, *args, **kwargs):
        self.get_object().thumbnail_invalidate()
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

        if request.user.is_authenticated() and \
                request.user != revision.image.user:
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
        image = self.get_object()
        revisions = ImageRevision.all_objects.filter(image=image)

        if not revisions:
            return HttpResponseBadRequest()

        final = None
        if image.is_final:
            final = revisions[0]
        else:
            for r in revisions:
                if r.is_final:
                    final = r

        if final is None:
            # Fallback to the most recent revision.
            final = revisions[0]

        image.thumbnail_invalidate()

        image.image_file = final.image_file
        image.updated = final.uploaded
        image.w = final.w
        image.h = final.h
        image.is_final = True

        if image.solution:
            image.solution.delete()

        image.save(keep_deleted=True)

        if final.solution:
            # Get the solution this way, I don't know why it wouldn't work otherwise
            content_type = ContentType.objects.get_for_model(ImageRevision)
            solution = Solution.objects.get(content_type=content_type, object_id=final.pk)
            solution.content_object = image
            solution.save()

        image.thumbnails.filter(revision=final.label).update(revision='0')
        self.image = image
        final.delete()

        messages.success(self.request, _("Original version deleted!"));
        # We do not call super, because that would delete the Image
        return HttpResponseRedirect(self.get_success_url())


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

        if request.user.is_authenticated() and request.user != image.user and not request.user.is_superuser:
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

        if request.user.is_authenticated() and request.user != image.user and not request.user.is_superuser:
            raise PermissionDenied

        return super(ImagePromoteView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        image = self.get_object()
        if image.is_wip:
            previously_published = image.published
            image.is_wip = False
            image.save(keep_deleted=True)

            if not previously_published:
                followers = [
                    x.user for x in
                    ToggleProperty.objects.toggleproperties_for_object(
                        "follow",
                        UserProfile.objects.get(user__pk=request.user.pk).user)
                ]

                thumb = image.thumbnail_raw('gallery', {'sync': True})
                push_notification(followers, 'new_image', {
                    'image': image,
                    'image_thumbnail': thumb.url if thumb else None
                })

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

        if request.user.is_authenticated() and request.user != image.user and not request.user.is_superuser:
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

    def form_valid(self, form):
        self.object.corrupted = False
        return super(ImageEditBasicView, self).form_valid(form)

    def get_success_url(self):
        image = self.get_object()
        if 'submit_gear' in self.request.POST:
            return reverse_lazy('image_edit_gear', kwargs={'id': image.get_id()})
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
            except TypeError:
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
            return reverse_lazy('image_edit_acquisition', kwargs={'id': image.get_id()})
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

    def get_form_class(self):
        return ImageEditCorruptedRevisionForm if self.object.corrupted else ImageEditRevisionForm

    def get_initial(self):
        revision = self.get_object()  # type: ImageRevision

        square_cropping = revision.square_cropping
        if square_cropping == '0,0,0,0':
            square_cropping = ImageService(revision.image).get_default_cropping(revision.label)

        return {
            'square_cropping': square_cropping
        }

    def get_success_url(self):
        return reverse_lazy('image_detail', args=(self.object.image.get_id(),))

    def dispatch(self, request, *args, **kwargs):
        try:
            revision = self.model.objects.get(pk=kwargs[self.pk_url_kwarg])
        except self.model.DoesNotExist:
            raise Http404

        if request.user.is_authenticated() and request.user != revision.image.user and not request.user.is_superuser:
            raise PermissionDenied

        return super(ImageEditRevisionView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, _("Form saved. Thank you!"))
        self.object.corrupted = False
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
            except TypeError:
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
            return reverse_lazy('image_edit_watermark', kwargs={'id': image.get_id()})
        return image.get_absolute_url()

    def post(self, request, *args, **kwargs):
        image = self.get_object()  # type: Image
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
