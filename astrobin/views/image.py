import logging
from typing import Union

from braces.views import (
    JSONResponseMixin,
    LoginRequiredMixin,
)
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, PermissionDenied
from django.core.files.images import get_image_dimensions
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import iri_to_uri, smart_text as smart_unicode
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import (
    DeleteView,
    DetailView,
    UpdateView,
)
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from astrobin.enums import ImageEditorStep, SubjectType
from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.enums.mouse_hover_image import MouseHoverImage
from astrobin.forms import (
    CopyGearForm, ImageDemoteForm, ImageEditBasicForm, ImageEditGearForm, ImageEditRevisionForm,
    ImageEditThumbnailsForm, ImageFlagThumbsForm, ImagePromoteForm, ImageRevisionUploadForm,
)
from astrobin.forms.remove_as_collaborator_form import ImageRemoveAsCollaboratorForm
from astrobin.forms.uncompressed_source_upload_form import UncompressedSourceUploadForm
from astrobin.models import (Collection, DeepSky_Acquisition, Image, ImageRevision, LANGUAGES, SolarSystem_Acquisition)
from astrobin.services.gear_service import GearService
from astrobin.templatetags.tags import can_like
from astrobin.utils import add_url_params, get_client_country_code, get_image_resolution
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItem
from astrobin_apps_groups.forms import AutoSubmitToIotdTpProcessForm, GroupSelectForm
from astrobin_apps_groups.models import Group
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.templatetags.astrobin_apps_iotd_tags import humanize_may_not_submit_to_iotd_tp_process_reason
from astrobin_apps_iotd.types.may_not_submit_to_iotd_tp_reason import MayNotSubmitToIotdTpReason
from astrobin_apps_platesolving.models import PlateSolvingAdvancedLiveLogEntry, Solution
from astrobin_apps_platesolving.services import SolutionService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import can_see_real_resolution
from astrobin_apps_users.services import UserService
from common.constants import GroupName
from common.exceptions import Http410
from common.services import AppRedirectionService, DateTimeService
from common.services.caching_service import CachingService

logger = logging.getLogger(__name__)


class ImageSingleObjectMixin(SingleObjectMixin):
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        id = self.kwargs.get(self.pk_url_kwarg)
        image = ImageService.get_object(id, queryset)

        if image is None:
            deleted_image = ImageService.get_object(id, Image.deleted_objects)
            if deleted_image is not None:
                raise Http410
            raise Http404

        return image


class ImageDetailViewBase(ImageSingleObjectMixin, DetailView):
    pass


class ImageUpdateViewBase(ImageSingleObjectMixin, UpdateView):
    pass


class ImageDeleteViewBase(ImageSingleObjectMixin, DeleteView):
    pass


class ImageFlagThumbsView(
    LoginRequiredMixin, ImageUpdateViewBase
):
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
        logger.info(f"User {request.user} flagged thumbs for image {image.get_id()}")
        ImageService(image).invalidate_all_thumbnails()
        messages.success(self.request, _("Thanks for reporting the problem. All thumbnails will be generated again."))
        return super(ImageFlagThumbsView, self).post(self.request, args, kwargs)


class ImageRemoveAsCollaboratorView(
    LoginRequiredMixin, ImageUpdateViewBase
):
    form_class = ImageRemoveAsCollaboratorForm
    model = Image
    pk_url_kwarg = 'id'
    http_method_names = ('post',)

    def get_queryset(self):
        return Image.objects_including_wip.all()

    def get_success_url(self):
        return self.object.get_absolute_url()

    def post(self, request, *args, **kwargs):
        image = self.get_object()

        if self.request.user not in image.collaborators.all():
            messages.error(self.request, _("You are not a collaborator to this image."))

        ImageService(image).remove_collaborator(self.request.user, self.request.user)

        messages.success(self.request, _("You have been removed as a collaborator to this image."))

        return super().post(self.request, args, kwargs)


@method_decorator(
    [
        last_modified(CachingService.get_image_thumb_last_modified),
        cache_control(public=True, no_cache=True, must_revalidate=True, maxAge=0),
    ], name='dispatch'
)
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
        if force is not None and request.user.is_superuser:
            if revision_label in (None, 'None', 0, '0'):
                image.thumbnail_invalidate()
            else:
                revision = ImageService(image).get_revision(revision_label)
                revision.thumbnail_invalidate()

        if revision_label is None:
            revision_label = 'final'

        try:
            url = image.thumbnail(
                alias, revision_label, animated='animated' in self.request.GET, insecure='insecure' in self.request.GET,
                sync=request.GET.get('sync') is not None
            )
        except FileNotFoundError:
            url = ImageService(image).get_error_thumbnail(revision_label, alias)

        return self.render_json_response(
            {
                'id': image.pk,
                'alias': alias,
                'revision': revision_label,
                'url': iri_to_uri(url)
            }
        )


@method_decorator(
    [
        last_modified(CachingService.get_image_thumb_last_modified),
        cache_control(public=True, no_cache=True, must_revalidate=True, maxAge=0),
    ], name='dispatch'
)
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
        if force is not None and request.user.is_superuser:
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
                sync=request.GET.get('sync') is not None
            )

            if thumb:
                return redirect(thumb.url)

            return HttpResponse(status=500)

        try:
            url = image.thumbnail(
                alias, revision_label, animated='animated' in self.request.GET, insecure='insecure' in self.request.GET,
                sync=request.GET.get('sync') is not None
            )
        except FileNotFoundError:
            url = ImageService(image).get_error_thumbnail(revision_label, alias)

        if not url:
            url = ImageService(image).get_error_thumbnail(revision_label, alias)

        return redirect(smart_unicode(url))


@method_decorator(
    [
        last_modified(CachingService.get_image_last_modified),
        cache_control(private=True, no_cache=True),
        vary_on_cookie
    ], name='dispatch'
)
class ImageDetailView(ImageDetailViewBase):
    model = Image
    pk_url_kwarg = 'id'
    template_name = 'image/detail.html'
    template_name_suffix = ''

    def get_queryset(self):
        return Image.objects_including_wip.prefetch_related(
            'collaborators',
            'revisions',
            'thumbnails',
        ).all()

    def dispatch(self, request, *args, **kwargs):
        # Redirect to the correct revision
        image = self.get_object(Image.objects_including_wip)
        profile = image.user.userprofile

        if profile.suspended:
            return render(request, 'user/suspended_account.html')

        if image.moderator_decision == ModeratorDecision.REJECTED:
            if not request.user.is_authenticated or \
                    not request.user.is_superuser and \
                    not request.user.userprofile.is_image_moderator():
                raise Http404

        if AppRedirectionService.should_redirect_to_new_gallery_experience(request):
            return redirect(
                AppRedirectionService.image_redirect(request, image.get_id(), kwargs.get('r'), kwargs.get('cid'))
            )

        revision_label = kwargs.get('r')
        if revision_label is not None and revision_label != '0':
            try:
                revision = ImageService(image).get_revisions().get(label=revision_label)
            except ImageRevision.DoesNotExist:
                revision = ImageService(image).get_final_revision()
                redirect_revision_label = revision.label if hasattr(revision, 'label') else '0'
                if request.user.is_authenticated:
                    messages.info(
                        request, _(
                            "You requested revision %s, but it doesn't exist or it was deleted. We redirected you to the "
                            "revision currently marked as final." % revision_label
                        )
                    )
                return redirect(reverse('image_detail', args=(image.get_id(), redirect_revision_label,)))

        if revision_label is None:
            # No revision specified, let's see if we need to redirect to the
            # final.
            if not image.is_final:
                final = image.revisions.filter(is_final=True)
                if final.count() > 0:
                    url = str(
                        reverse_lazy(
                            'image_detail',
                            args=(image.get_id(), final[0].label,)
                        )
                    )

                    params = {}
                    if 'nc' in request.GET:
                        params['nc'] = request.GET.get('nc')
                        if 'nce' in request.GET:
                            params['nce'] = request.GET.get('nce')

                    if 'cid' in request.GET:
                        params['cid'] = request.GET.get('cid')

                    if 'force-classic-view' in request.GET:
                        params['force-classic-view'] = ''

                    # Add parameters to URL
                    url = add_url_params(url, params)

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

        if is_revision:
            w, h = get_image_resolution(revision_image)
        else:
            w, h = get_image_resolution(image)

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
                    image_next = Image.objects.filter(
                        user=image.user,
                        published__isnull=False,
                        published__gt=image.published,
                        moderator_decision=ModeratorDecision.APPROVED,
                    ).order_by('published')[0:1]

                    image_prev = Image.objects.filter(
                        user=image.user,
                        published__isnull=False,
                        published__lt=image.published,
                        moderator_decision=ModeratorDecision.APPROVED,
                    ).order_by('-published')[0:1]
                elif nav_ctx == 'collection':
                    try:
                        try:
                            collection = image.collections.get(pk=nav_ctx_extra)
                        except ValueError:
                            # Maybe this image is in a single collection
                            try:
                                collection = image.collections.all()[0]
                            except IndexError:
                                collection = None

                        if collection is None:
                            image_next = None
                            image_prev = None
                        else:
                            if collection.order_by_tag:
                                collection_images = Image.objects.filter(
                                    user=image.user,
                                    collections=collection,
                                    keyvaluetags__key=collection.order_by_tag,
                                    moderator_decision=ModeratorDecision.APPROVED,
                                ).order_by('keyvaluetags__value')

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
                                image_next = Image.objects.filter(
                                    user=image.user,
                                    collections=collection,
                                    published__gt=image.published,
                                    moderator_decision=ModeratorDecision.APPROVED,
                                ).order_by('published')[0:1]

                                image_prev = Image.objects.filter(
                                    user=image.user,
                                    collections=collection,
                                    published__lt=image.published,
                                    moderator_decision=ModeratorDecision.APPROVED,
                                ).order_by('-published')[0:1]
                    except Collection.DoesNotExist:
                        # image_prev and image_next will remain None
                        pass
                elif nav_ctx == 'group':
                    try:
                        group = image.part_of_group_set.get(pk=nav_ctx_extra)
                        if group.public:
                            image_next = Image.objects.filter(
                                part_of_group_set=group,
                                published__isnull=False,
                                published__gt=image.published,
                                moderator_decision=ModeratorDecision.APPROVED,
                            ).order_by('published')[0:1]

                            image_prev = Image.objects.filter(
                                part_of_group_set=group,
                                published__isnull=False,
                                published__lt=image.published,
                                moderator_decision=ModeratorDecision.APPROVED,
                            ).order_by('-published')[0:1]
                    except (Group.DoesNotExist, ValueError):
                        # image_prev and image_next will remain None
                        pass
                elif nav_ctx == 'all':
                    image_next = Image.objects.filter(
                        published__isnull=False,
                        published__gt=image.published,
                        moderator_decision=ModeratorDecision.APPROVED,
                    ).order_by('published')[0:1]

                    image_prev = Image.objects.filter(
                        published__isnull=False,
                        published__lt=image.published,
                        moderator_decision=ModeratorDecision.APPROVED,
                    ).order_by('-published')[0:1]
            except Image.DoesNotExist:
                image_next = None
                image_prev = None

        if image_next and isinstance(image_next, QuerySet):
            image_next = image_next[0]
        if image_prev and isinstance(image_prev, QuerySet):
            image_prev = image_prev[0]

        ############################
        # DOWNLOAD ORIGINAL URL    #
        ############################

        download_original_url = reverse('image_download', args=(image.get_id(), r or 'final', 'original'))

        #################
        # RESPONSE DICT #
        #################

        from astrobin_apps_platesolving.solver import Solver

        if skyplot_zoom1 and not skyplot_zoom1.name.startswith('images/'):
            skyplot_zoom1.name = 'images/' + skyplot_zoom1.name

        search_query = f'{self.request.GET.get("q", "")} {self.request.GET.get("telescope", "")} {self.request.GET.get("camera", "")}'.strip()

        response_dict = context.copy()
        response_dict.update(
            {
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
                                          ) or (
                                                  mod == 'solved'
                                                  and instance_to_platesolve.solution
                                                  and instance_to_platesolve.solution.status >= Solver.ADVANCED_SUCCESS
                                          ),
                'show_advanced_solution_on_full': (
                        instance_to_platesolve.mouse_hover_image != MouseHoverImage.NOTHING
                        and instance_to_platesolve.solution
                        and instance_to_platesolve.solution.status == Solver.ADVANCED_SUCCESS
                ),
                'advanced_solution_last_live_log_entry':
                    PlateSolvingAdvancedLiveLogEntry.objects.filter(
                        serial_number=instance_to_platesolve.solution.pixinsight_serial_number
                    ) \
                    .order_by('-timestamp').first() \
                        if instance_to_platesolve.solution and instance_to_platesolve.solution.pixinsight_serial_number \
                        else None,
                'skyplot_zoom1': skyplot_zoom1,
                'pixinsight_finding_chart': pixinsight_finding_chart,
                'pixinsight_finding_chart_small': pixinsight_finding_chart_small,

                'image_ct': ContentType.objects.get_for_model(Image),
                'user_ct': ContentType.objects.get_for_model(User),
                'user_can_like': can_like(self.request.user, image),
                'promote_form': ImagePromoteForm(instance=image),
                'upload_revision_form': ImageRevisionUploadForm(),
                'upload_uncompressed_source_form': UncompressedSourceUploadForm(instance=image),
                'show_contains': (image.subject_type == SubjectType.DEEP_SKY and subjects) or
                                 (image.subject_type != SubjectType.DEEP_SKY),
                'subjects': subjects,
                'subject_type': ImageService(image).get_subject_type_label(),
                'hemisphere': ImageService(image).get_hemisphere(r),
                'constellation': ImageService.get_constellation(revision_image.solution) \
                    if revision_image \
                    else ImageService.get_constellation(image.solution),
                'solar_system_main_subject': ImageService(image).get_solar_system_main_subject_label(),
                'content_type': ContentType.objects.get(app_label='astrobin', model='image'),
                'preferred_languages': preferred_languages,
                'select_group_form': GroupSelectForm(
                    user=self.request.user
                ) if self.request.user.is_authenticated else None,
                'in_public_groups': Group.objects.filter(Q(public=True, images=image)),
                'in_collections': Collection.objects.filter(
                    user=image.user, images=image
                ) if not image.is_wip else None,
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
                'search_query': search_query,
                'download_original_url': download_original_url,
            }
        )

        return response_dict


@method_decorator(
    [
        last_modified(CachingService.get_image_last_modified),
        cache_control(private=True, no_cache=True),
        vary_on_cookie
    ], name='dispatch'
)
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
        profile = image.user.userprofile

        if profile.suspended:
            return render(request, 'user/suspended_account.html')

        if image.moderator_decision == ModeratorDecision.REJECTED:
            raise Http404

        if AppRedirectionService.should_redirect_to_new_gallery_experience(request):
            redirect_url = AppRedirectionService.redirect(f'/i/{image.get_id()}')
            if revision_label := kwargs.get('r'):
                redirect_url += f'?r={revision_label}'
            redirect_url += '#fullscreen'
            return redirect(redirect_url)

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
                        args=(image.get_id(), final[0].label,)
                    )
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
            alias = 'qhd' if not image.sharpen_thumbnails else 'qhd_sharpened'

        if mod in settings.AVAILABLE_IMAGE_MODS:
            alias += "_%s" % mod

        response_dict = context.copy()
        response_dict.update(
            {
                'real': real,
                'alias': alias,
                'mod': mod,
                'revision_label': self.revision_label,
                'max_file_size_before_warning': 25 * 1024 * 1024,
            }
        )

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
        
        # Get collections before deleting the image
        collections = list(image.collections.all())

        from astrobin.tasks import invalidate_all_image_thumbnails
        invalidate_all_image_thumbnails.delay(image.pk)

        result = super(ImageDeleteView, self).post(args, kwargs)
        
        # Update counts for affected collections
        for collection in collections:
            collection.update_counts()
            
        messages.success(self.request, _("Image deleted."))
        return result


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
        messages.success(self.request, _("Original version deleted!"))

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
            image.mouse_hover_image = revision.mouse_hover_image \
                if revision.mouse_hover_image == MouseHoverImage.NOTHING \
                else MouseHoverImage.SOLUTION

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

    def get_queryset(self) -> QuerySet:
        return self.model.objects_including_wip.all()

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()

    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()

        if request.user.is_authenticated and request.user != image.user and not request.user.is_superuser:
            raise PermissionDenied

        return super(ImageDemoteView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        image = form.instance

        ImageService(image).demote_to_staging_area()
        
        # Update counts for collections that contain this image
        for collection in image.collections.all():
            collection.update_counts()

        # No need to show the success message if the user is going to be redirected to the new page.
        if not AppRedirectionService.should_redirect_to_new_gallery_experience(self.request):
            messages.success(self.request, _("Image moved to the staging area."))

        return super().form_valid(form)


class ImagePromoteView(LoginRequiredMixin, ImageUpdateViewBase):
    form_class = ImagePromoteForm
    model = Image
    pk_url_kwarg = 'id'
    http_method_names = ('post',)

    def get_queryset(self) -> QuerySet:
        return self.model.objects_including_wip.all()

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()

    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()

        if request.user.is_authenticated and request.user != image.user and not request.user.is_superuser:
            raise PermissionDenied

        return super(ImagePromoteView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        image = form.instance

        image.skip_notifications = self.request.POST.get('skip_notifications', 'off').lower() == 'on'
        image.skip_activity_stream = self.request.POST.get('skip_activity_stream', 'off').lower() == 'on'

        ImageService(image).promote_to_public_area(image.skip_notifications, image.skip_activity_stream)
        
        # Update counts for collections that contain this image
        for collection in image.collections.all():
            collection.update_counts()

        # No need to show the success message if the user is going to be redirected to the new page.
        if not AppRedirectionService.should_redirect_to_new_gallery_experience(self.request):
            messages.success(self.request, _("Image moved to the public area."))

        return super().form_valid(form)


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
        messages.error(
            self.request, _(
                "There was one or more errors processing the form. " +
                "You may need to scroll down to see them."
            )
        )
        return super(ImageEditBaseView, self).form_invalid(form)


class ImageEditBasicView(ImageEditBaseView):
    form_class = ImageEditBasicForm
    template_name = 'image/edit/basic.html'

    def get_success_url(self):
        image = self.get_object()
        if 'submit_gear' in self.request.POST:
            return reverse_lazy('image_edit_gear', kwargs={'id': image.get_id()}) + "?upload"

        return image.get_absolute_url()

    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()

        return redirect(
            AppRedirectionService.redirect(
                f'/i/{image.get_id()}/edit#'
                f'{AppRedirectionService.image_editor_step_number(request.user, ImageEditorStep.BASIC_INFORMATION)}'
            )
        )

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
        context['copy_gear_form'] = CopyGearForm(user, context['image'])
        context['is_own_equipment_migrator'] = UserService(user).is_in_group(
            [GroupName.EQUIPMENT_MODERATORS, GroupName.OWN_EQUIPMENT_MIGRATORS]
        )

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
                user=image.user, instance=image, data=self.request.POST
            )
        else:
            return form_class(user=image.user, instance=image)

    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()
        has_legacy_gear = GearService.image_has_legacy_gear(image)

        if not has_legacy_gear:
            return redirect(
                AppRedirectionService.redirect(
                    f'/i/{image.get_id()}/edit#'
                    f'{AppRedirectionService.image_editor_step_number(request.user, ImageEditorStep.EQUIPMENT)}'
                )
            )

        return super().dispatch(request, args, kwargs)


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
            'mouse_hover_image': revision.mouse_hover_image
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
        revision: ImageRevision = self.get_object()

        if revision.image_file:
            previous_url = revision.image_file.url
        else:
            previous_url = None

        previous_square_cropping = revision.square_cropping

        ret = super(ImageEditRevisionView, self).post(request, *args, **kwargs)

        revision = self.get_object()

        if revision.image_file and previous_url:
            new_url = revision.image_file.url

            if new_url != previous_url:
                try:
                    revision.w, revision.h = get_image_dimensions(revision.image_file)
                except TypeError as e:
                    logger.warning(
                        "ImageEditRevisionView: unable to get image dimensions for %d: %s" % (revision.pk, str(e))
                    )
                    pass

                revision.square_cropping = ImageService(revision.image).get_default_cropping(revision.label)
                revision.save(keep_deleted=True)

                revision.thumbnail_invalidate()

        if previous_square_cropping not in (None, '', '0,0,0,0') and \
                previous_square_cropping != revision.square_cropping:
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

    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()

        return redirect(
            AppRedirectionService.redirect(
                f'/i/{image.get_id()}/edit#'
                f'{AppRedirectionService.image_editor_step_number(request.user, ImageEditorStep.THUMBNAIL)}'
            )
        )


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
    def dispatch(self, request, *args, **kwargs):
        image_id: Union[str, int] = self.kwargs.get('id')
        image: Image = ImageService.get_object(image_id, Image.objects_including_wip)

        if image is None:
            raise Http404

        if not ImageService(image).display_download_menu(request.user):
            return render(request, "403.html", {})

        return super().dispatch(request, args, kwargs)

    def get(self, request, *args, **kwargs) -> HttpResponse:
        image_id: Union[str, int] = self.kwargs.pop('id')
        revision_label: str = self.kwargs.pop('revision_label')
        version: str = self.kwargs.pop('version')

        image: Image = ImageService.get_object(image_id, Image.objects_including_wip)

        if image is None:
            raise Http404

        return ImageService(image).download(request.user, revision_label, version)


class ImageSubmitToIotdTpProcessView(View):
    def dispatch(self, request, *args, **kwargs):
        id: Union[str, int] = self.kwargs.get('id')
        image: Image = ImageService.get_object(id, Image)

        if image is None:
            raise Http404

        return super().dispatch(request, args, kwargs)

    def post(self, request, *args, **kwargs):
        id: Union[str, int] = self.kwargs.get('id')
        auto_submit = request.POST.get('auto_submit_to_iotd_tp_process', 'off').lower() == 'on'
        agreed = request.POST.get('agreed_to_iotd_tp_rules_and_guidelines', 'off').lower() == 'on'
        image: Image = ImageService.get_object(id, Image)

        if image is None:
            raise Http404

        may, reason = IotdService.submit_to_iotd_tp_process(request.user, image, auto_submit, agreed)

        if not may:
            if reason == MayNotSubmitToIotdTpReason.NOT_AUTHENTICATED or reason == MayNotSubmitToIotdTpReason.NOT_OWNER:
                return render(request, "403.html", {})
            else:
                return HttpResponseBadRequest(humanize_may_not_submit_to_iotd_tp_process_reason(reason))

        messages.success(request, _("Image submitted to the IOTD/TP process!"))
        return HttpResponseRedirect(request.POST.get('next'))


@method_decorator(
    [
        last_modified(CachingService.get_image_last_modified),
        cache_control(public=True, no_cache=True, must_revalidate=True, maxAge=0),
        csrf_exempt,
    ], name='dispatch'
)
class ImageEquipmentFragment(View):
    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()

        id: Union[str, int] = self.kwargs.get('id')
        try:
            image: Image = ImageService.get_object(id, Image.objects_including_wip_plain)
        except Image.DoesNotExist:
            raise Http404

        if image is None:
            raise Http404

        search_query = (
            f'{self.request.GET.get("q", "")} '
            f'{self.request.GET.get("telescope", "")} '
            f'{self.request.GET.get("camera", "")}'
        ).strip()

        return render(
            request, 'image/detail/image_card_equipment.html', {
                'image': image,
                'search_query': search_query,
                'equipment_list': ImageService(image).get_equipment_list(
                    get_client_country_code(self.request)
                ),
            }
        )


@method_decorator(
    [
        last_modified(CachingService.get_image_last_modified),
        cache_control(public=True, no_cache=True, must_revalidate=True, maxAge=0),
        csrf_exempt,
    ], name='dispatch'
)
class ImageAcquisitionFragment(View):
    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()

        id: Union[str, int] = self.kwargs.get('id')
        try:
            image: Image = ImageService.get_object(id, Image.objects_including_wip_plain)
        except Image.DoesNotExist:
            raise Http404

        if image is None:
            raise Http404

        r = self.kwargs.get('r')
        if r is None:
            r = '0'

        revision_image = None
        is_revision = False
        instance_to_platesolve = image
        if r != '0':
            try:
                revision_image = ImageRevision.objects.filter(image=image, label=r)[0]
                is_revision = True
                instance_to_platesolve = revision_image
            except:
                pass

        locations = '; '.join(['%s' % str(x) for x in image.locations.all()])

        #############################
        # GENERATE ACQUISITION DATA #
        #############################

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
            deep_sky_data = ImageService(image).get_deep_sky_acquisition_html()
        elif ssa:
            image_type = 'solar_system'

        search_query = (
            f'{self.request.GET.get("q", "")} '
            f'{self.request.GET.get("telescope", "")} '
            f'{self.request.GET.get("camera", "")}'
        ).strip()

        return render(
            request, 'image/detail/image_card_acquisition.html', {
                'image': image,
                'deep_sky_data': deep_sky_data,
                'ssa': ssa,
                'image_type': image_type,
                'w': w,
                'h': h,
                'is_revision': is_revision,
                'instance_to_platesolve': instance_to_platesolve,
                'file_size': revision_image.uploader_upload_length if revision_image else image.uploader_upload_length,
                'resolution': '%dx%d' % (w, h) if (w and h) else None,
                'locations': locations,
                'search_query': search_query,
                'dates_label': _("Dates"),
            }
        )


@method_decorator(
    [
        csrf_exempt,
    ], name='dispatch'
)
class ImageMarketplaceFragment(View):
    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()

        image_id: Union[str, int] = self.kwargs.get('id')
        try:
            image: Image = ImageService.get_object(image_id, Image.objects_including_wip_plain)
        except Image.DoesNotExist:
            raise Http404

        if image is None:
            raise Http404

        line_items = []

        for prop in (
                'imaging_telescopes_2',
                'guiding_telescopes_2',
                'imaging_cameras_2',
                'guiding_cameras_2',
                'mounts_2',
                'filters_2',
                'accessories_2',
                'software_2',
        ):
            for x in getattr(image, prop).all():
                line_item_objects = EquipmentItemMarketplaceListingLineItem.objects.filter(
                    user=image.user,
                    item_object_id=x.pk,
                    item_content_type=ContentType.objects.get_for_model(x),
                    sold__isnull=True,
                    listing__approved__isnull=False,
                    listing__expiration__gt=DateTimeService.now(),
                )

                if line_item_objects.exists():
                    for line_item_object in line_item_objects.iterator():
                        line_items.append(line_item_object)

        return render(
            request, 'image/detail/marketplace.html', {
                'line_items': line_items,
            }
        )


class ImageCollaboratorRequestAccept(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        image_id: Union[str, int] = self.kwargs.get('id')
        image: Image = ImageService.get_object(image_id, Image.objects_including_wip_plain)

        if image is None:
            raise Http404

        try:
            ImageService(image).accept_collaborator_request(request.user)
        except Exception as e:
            return HttpResponseBadRequest(str(e))

        messages.success(request, _("You are now a collaborator on this image!"))

        return HttpResponseRedirect(image.get_absolute_url())


class ImageCollaboratorRequestDeny(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        image_id: Union[str, int] = self.kwargs.get('id')
        image: Image = ImageService.get_object(image_id, Image.objects_including_wip_plain)

        if image is None:
            raise Http404

        try:
            ImageService(image).deny_collaborator_request(request.user)
        except Exception as e:
            return HttpResponseBadRequest(str(e))

        messages.success(request, _("Collaborator request denied."))

        return HttpResponseRedirect(image.get_absolute_url())
