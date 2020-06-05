import csv
import logging
import operator
import os
import urllib2

import flickrapi
import simplejson
from actstream.models import Action
from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import MultipleObjectsReturned
from django.core.files.images import get_image_dimensions
from django.core.paginator import Paginator, InvalidPage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.http import Http404, HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template import loader, RequestContext
from django.template.defaultfilters import filesizeformat
from django.template.loader import render_to_string
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ngettext as _n
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from el_pagination.decorators import page_template
from flickrapi.auth import FlickrAccessToken
from haystack.exceptions import SearchFieldError
from haystack.query import SearchQuerySet
from reviews.models import Review
from reviews.views import ReviewAddForm
from silk.profiling.profiler import silk_profile

from astrobin.context_processors import notices_count, user_language, user_scores, common_variables
from astrobin.enums import SubjectType
from astrobin.forms import ImageUploadForm, ImageLicenseForm, PrivateMessageForm, UserProfileEditBasicForm, \
    DeepSky_AcquisitionBasicForm, SolarSystem_AcquisitionForm, UserProfileEditCommercialForm, \
    UserProfileEditRetailerForm, DefaultImageLicenseForm, TelescopeEditNewForm, MountEditNewForm, CameraEditNewForm, \
    FocalReducerEditNewForm, SoftwareEditNewForm, FilterEditNewForm, AccessoryEditNewForm, TelescopeEditForm, \
    MountEditForm, CameraEditForm, FocalReducerEditForm, SoftwareEditForm, FilterEditForm, AccessoryEditForm, \
    GearUserInfoForm, LocationEditForm, ImageEditWatermarkForm, DeepSky_AcquisitionForm, ClaimCommercialGearForm, \
    MergeCommercialGearForm, ClaimRetailedGearForm, MergeRetailedGearForm, UserProfileEditPreferencesForm, \
    RetailedGearForm, ImageRevisionUploadForm, UserProfileEditGearForm, CommercialGearForm
from astrobin.gear import is_gear_complete, get_correct_gear
from astrobin.models import Image, UserProfile, CommercialGear, Gear, Location, ImageRevision, DeepSky_Acquisition, \
    SolarSystem_Acquisition, RetailedGear, GearUserInfo, Telescope, Mount, Camera, FocalReducer, Software, Filter, \
    Accessory, GearHardMergeRedirect, GlobalStat, App, GearMakeAutoRename, Acquisition
from astrobin.shortcuts import ajax_response, ajax_success, ajax_fail
from astrobin.utils import user_is_producer, user_is_retailer, to_user_timezone, base26_encode, base26_decode
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_platesolving.forms import PlateSolvingSettingsForm, PlateSolvingAdvancedSettingsForm
from astrobin_apps_platesolving.models import PlateSolvingSettings, Solution, PlateSolvingAdvancedSettings
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import can_restore_from_trash, \
    can_perform_advanced_platesolving
from astrobin_apps_premium.utils import premium_get_max_allowed_image_size, premium_get_max_allowed_revisions, \
    premium_user_has_valid_subscription
from astrobin_apps_users.services import UserService
from toggleproperties.models import ToggleProperty

log = logging.getLogger('apps')


def get_image_or_404(queryset, id):
    # hashes will always have at least a letter
    if id.isdigit():
        # old style numerical id
        image = get_object_or_404(queryset, pk=id)
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


def object_list(request, queryset, paginate_by=None, page=None,
                allow_empty=True, template_name=None, template_loader=loader,
                extra_context=None, context_processors=None, template_object_name='object',
                mimetype=None):
    """
    Generic list of objects.

    Templates: ``<app_label>/<model_name>_list.html``
    Context:
        object_list
            list of objects
        is_paginated
            are the results paginated?
        results_per_page
            number of objects per page (if paginated)
        has_next
            is there a next page?
        has_previous
            is there a prev page?
        page
            the current page
        next
            the next page
        previous
            the previous page
        pages
            number of pages, total
        hits
            number of objects, total
        last_on_page
            the result number of the last of object in the
            object_list (1-indexed)
        first_on_page
            the result number of the first object in the
            object_list (1-indexed)
        page_range:
            A list of the page numbers (1-indexed).
    """
    if extra_context is None: extra_context = {}

    queryset = queryset._clone()

    if paginate_by:
        paginator = Paginator(queryset, paginate_by, allow_empty_first_page=allow_empty)

        if not page:
            page = request.GET.get('page', 1)

        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                # Page is not 'last', nor can it be converted to an int.
                raise Http404
        try:
            page_obj = paginator.page(page_number)
        except InvalidPage:
            raise Http404

        c = RequestContext(request, {
            '%s_list' % template_object_name: page_obj.object_list,
            'paginator': paginator,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),

            # Legacy template context stuff. New templates should use page_obj
            # to access this instead.
            'results_per_page': paginator.per_page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page': page_obj.number,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'first_on_page': page_obj.start_index(),
            'last_on_page': page_obj.end_index(),
            'pages': paginator.num_pages,
            'hits': paginator.count,
            'page_range': paginator.page_range,
        }, context_processors)
    else:
        c = RequestContext(request, {
            '%s_list' % template_object_name: queryset,
            'paginator': None,
            'page_obj': None,
            'is_paginated': False,
        }, context_processors)

        if not allow_empty and len(queryset) == 0:
            raise Http404

    for key, value in extra_context.items():
        if callable(value):
            c[key] = value()
        else:
            c[key] = value

    if not template_name:
        model = queryset.model
        template_name = "%s/%s_list.html" % (model._meta.app_label, model._meta.object_name.lower())

    t = template_loader.get_template(template_name)

    context = c.flatten()
    context.update(notices_count(request))
    context.update(user_language(request))
    context.update(user_scores(request))
    context.update(common_variables(request))

    return HttpResponse(t.render(context, request))


def monthdelta(date, delta):
    m, y = (date.month + delta) % 12, date.year + ((date.month) + delta - 1) // 12
    if not m: m = 12
    d = [31,
         29 if y % 4 == 0 and not y % 400 == 0 else 28,
         31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return date.replace(day=d, month=m, year=y)


def valueReader(source, field):
    def unicode_truncate(s, length, encoding='utf-8'):
        encoded = s.encode(encoding)[:length]
        return encoded.decode(encoding, 'ignore')

    def utf_8_encoder(data):
        for line in data:
            yield line.encode('utf-8')

    as_field = 'as_values_' + field
    value = ''
    if as_field in source:
        value += source[as_field]
    if field in source:
        value += ',' + source[field]

    if not (as_field in source or field in source):
        return [], ""

    items = []
    reader = csv.reader(utf_8_encoder([value]),
                        skipinitialspace=True)
    for row in reader:
        items += [unicode_truncate(unicode(x, 'utf-8'), 64) for x in row if x != '']

    return items, value


def get_or_create_location(prop, value):
    k = None
    created = False

    try:
        return Location.objects.get(id=value)
    except ValueError:
        pass

    try:
        k, created = Location.objects.get_or_create(**{prop: value})
    except MultipleObjectsReturned:
        k = Location.objects.filter(**{prop: value})[0]

    if created:
        k.user_generated = True
        k.save()

    return k


def jsonDump(all):
    if len(all) > 0:
        return simplejson.dumps([{'id': i.id, 'name': i.get_name(), 'complete': is_gear_complete(i.id)} for i in all])
    else:
        return []


def upload_error(request, image=None):
    messages.error(request, _("Invalid image or no image provided. Allowed formats are JPG, PNG and GIF."))

    if image is not None:
        return HttpResponseRedirect(image.get_absolute_url())

    return HttpResponseRedirect('/upload/')


def upload_size_error(request, max_size, image=None):
    subscriptions_url = reverse('subscription_list')
    open_link = "<a href=\"%s\">" % subscriptions_url
    close_link = "</a>"
    msg = "Sorry, but this image is too large. Under your current subscription plan, the maximum allowed image size is %(max_size)s. %(open_link)sWould you like to upgrade?%(close_link)s"

    messages.error(request, _(msg) % {
        "max_size": filesizeformat(max_size),
        "open_link": open_link,
        "close_link": close_link
    })

    if image is not None:
        return HttpResponseRedirect(image.get_absolute_url())

    return HttpResponseRedirect('/upload/')


def upload_max_revisions_error(request, max_revisions, image):
    subscriptions_url = reverse('subscription_list')
    open_link = "<a href=\"%s\">" % subscriptions_url
    close_link = "</a>"
    msg_singular = "Sorry, but you have reached the maximum amount of allowed image revisions. Under your current subscription, the limit is %(max_revisions)s revision per image. %(open_link)sWould you like to upgrade?%(close_link)s"
    msg_plural = "Sorry, but you have reached the maximum amount of allowed image revisions. Under your current subscription, the limit is %(max_revisions)s revisions per image. %(open_link)sWould you like to upgrade?%(close_link)s"

    messages.error(request, _n(msg_singular, msg_plural, max_revisions) % {
        "max_revisions": max_revisions,
        "open_link": open_link,
        "close_link": close_link
    })

    return HttpResponseRedirect(image.get_absolute_url())


# VIEWS

@page_template('index/stream_page.html', key='stream_page')
@page_template('index/recent_images_page.html', key='recent_images_page')
@silk_profile('Index')
def index(request, template='index/root.html', extra_context=None):
    """Main page"""

    if not request.user.is_authenticated():
        from django.shortcuts import redirect
        return redirect("https://welcome.astrobin.com/")

    image_ct = ContentType.objects.get_for_model(Image)
    image_rev_ct = ContentType.objects.get_for_model(ImageRevision)
    user_ct = ContentType.objects.get_for_model(User)

    recent_images = Image.objects \
        .exclude(title=None) \
        .exclude(title='') \
        .filter(moderator_decision=1)

    response_dict = {
        'recent_images': recent_images,
        'recent_images_alias': 'gallery',
        'recent_images_batch_size': 70,
        'section': 'recent',
    }

    profile = request.user.userprofile

    section = request.GET.get('s')
    if section is None:
        section = profile.default_frontpage_section
    response_dict['section'] = section

    if section == 'global':
        ##################
        # GLOBAL ACTIONS #
        ##################
        actions = Action.objects.all().prefetch_related(
            'actor__userprofile',
            'target_content_type',
            'target')
        response_dict['actions'] = actions
        response_dict['cache_prefix'] = 'astrobin_global_actions'

    elif section == 'personal':
        ####################
        # PERSONAL ACTIONS #
        ####################
        cache_key = 'astrobin_users_image_ids_%s' % request.user
        users_image_ids = cache.get(cache_key)
        if users_image_ids is None:
            users_image_ids = [
                str(x) for x in
                Image.objects.filter(
                    user=request.user).values_list('id', flat=True)
            ]
            cache.set(cache_key, users_image_ids, 300)

        cache_key = 'astrobin_users_revision_ids_%s' % request.user
        users_revision_ids = cache.get(cache_key)
        if users_revision_ids is None:
            users_revision_ids = [
                str(x) for x in
                ImageRevision.objects.filter(
                    image__user=request.user).values_list('id', flat=True)
            ]
            cache.set(cache_key, users_revision_ids, 300)

        cache_key = 'astrobin_followed_user_ids_%s' % request.user
        followed_user_ids = cache.get(cache_key)
        if followed_user_ids is None:
            followed_user_ids = [
                str(x) for x in
                ToggleProperty.objects.filter(
                    property_type="follow",
                    user=request.user,
                    content_type=ContentType.objects.get_for_model(User)
                ).values_list('object_id', flat=True)
            ]
            cache.set(cache_key, followed_user_ids, 900)
        response_dict['has_followed_users'] = len(followed_user_ids) > 0

        cache_key = 'astrobin_followees_image_ids_%s' % request.user
        followees_image_ids = cache.get(cache_key)
        if followees_image_ids is None:
            followees_image_ids = [
                str(x) for x in
                Image.objects.filter(user_id__in=followed_user_ids).values_list('id', flat=True)
            ]
            cache.set(cache_key, followees_image_ids, 900)

        actions = Action.objects \
            .prefetch_related(
            'actor__userprofile',
            'target_content_type',
            'target'
        ).filter(
            # Actor is user, or...
            Q(
                Q(actor_content_type=user_ct) &
                Q(actor_object_id=request.user.id)
            ) |

            # Action concerns user's images as target, or...
            Q(
                Q(target_content_type=image_ct) &
                Q(target_object_id__in=users_image_ids)
            ) |
            Q(
                Q(target_content_type=image_rev_ct) &
                Q(target_object_id__in=users_revision_ids)
            ) |

            # Action concerns user's images as object, or...
            Q(
                Q(action_object_content_type=image_ct) &
                Q(action_object_object_id__in=users_image_ids)
            ) |
            Q(
                Q(action_object_content_type=image_rev_ct) &
                Q(action_object_object_id__in=users_revision_ids)
            ) |

            # Actor is somebody the user follows, or...
            Q(
                Q(actor_content_type=user_ct) &
                Q(actor_object_id__in=followed_user_ids)
            ) |

            # Action concerns an image by a followed user...
            Q(
                Q(target_content_type=image_ct) &
                Q(target_object_id__in=followees_image_ids)
            ) |
            Q(
                Q(action_object_content_type=image_ct) &
                Q(action_object_object_id__in=followees_image_ids)
            )
        )
        response_dict['actions'] = actions
        response_dict['cache_prefix'] = 'astrobin_personal_actions'

    elif section == 'followed':
        followed = [x.object_id for x in ToggleProperty.objects.filter(
            property_type="follow",
            content_type=ContentType.objects.get_for_model(User),
            user=request.user)]

        response_dict['recent_images'] = recent_images.filter(user__in=followed)

    if extra_context is not None:
        response_dict.update(extra_context)

    return render(request, template, response_dict)


@login_required
def image_upload(request):
    from astrobin_apps_premium.utils import (
        premium_used_percent,
        premium_progress_class,
        premium_user_has_subscription,
        premium_user_has_invalid_subscription,
    )

    tmpl_premium_used_percent = premium_used_percent(request.user)
    tmpl_premium_progress_class = premium_progress_class(tmpl_premium_used_percent)
    tmpl_premium_has_inactive_subscription = \
        premium_user_has_subscription(request.user) and \
        premium_user_has_invalid_subscription(request.user) and \
        not premium_user_has_valid_subscription(request.user)

    response_dict = {
        'premium_used_percent': tmpl_premium_used_percent,
        'premium_progress_class': tmpl_premium_progress_class,
        'premium_has_inactive_subscription': tmpl_premium_has_inactive_subscription,
    }

    if tmpl_premium_used_percent < 100:
        response_dict['upload_form'] = ImageUploadForm()

    return render(request, "upload.html", response_dict)


@login_required
@require_POST
def image_upload_process(request):
    """Process the form"""

    from astrobin_apps_premium.utils import premium_used_percent

    used_percent = premium_used_percent(request.user)
    if used_percent >= 100:
        messages.error(request, _("You have reached your image count limit. Please upgrade!"))
        return HttpResponseRedirect('/upload/')

    if settings.READONLY_MODE:
        messages.error(request, _(
            "AstroBin is currently in read-only mode, because of server maintenance. Please try again soon!"))
        return HttpResponseRedirect('/upload/')

    if 'image_file' not in request.FILES:
        return upload_error(request)

    form = ImageUploadForm(request.POST, request.FILES)

    if not form.is_valid():
        return upload_error(request)

    image_file = request.FILES["image_file"]
    ext = os.path.splitext(image_file.name)[1].lower()

    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        return upload_error(request)

    max_size = premium_get_max_allowed_image_size(request.user)
    if image_file.size > max_size:
        return upload_size_error(request, max_size)

    if image_file.size < 1e+7:
        try:
            from PIL import Image as PILImage
            trial_image = PILImage.open(image_file)
            trial_image.verify()
            image_file.file.seek(0)  # Because we opened it with PIL

            if ext == '.png' and trial_image.mode == 'I':
                messages.warning(request, _(
                    "You uploaded an Indexed PNG file. AstroBin will need to lower the color count to 256 in order to work with it."))
        except:
            return upload_error(request)

    profile = request.user.userprofile
    image = form.save(commit=False)
    image.user = request.user
    image.license = profile.default_license

    if 'wip' in request.POST:
        image.is_wip = True

    image.save(keep_deleted=True)

    from astrobin.tasks import retrieve_primary_thumbnails
    retrieve_primary_thumbnails.delay(image.pk, {'revision_label': '0'})

    return HttpResponseRedirect(reverse('image_edit_thumbnails', kwargs={'id': image.get_id()}))


@login_required
@require_GET
def image_edit_watermark(request, id):
    image = get_image_or_404(Image.objects_including_wip, id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    profile = image.user.userprofile
    if not profile.default_watermark_text or profile.default_watermark_text == '':
        profile.default_watermark_text = "Copyright %s" % image.user.username
        profile.save(keep_deleted=True)

    image.watermark = profile.default_watermark
    image.watermark_text = profile.default_watermark_text
    image.watermark_position = profile.default_watermark_position
    image.watermark_size = profile.default_watermark_size
    image.watermark_opacity = profile.default_watermark_opacity

    form = ImageEditWatermarkForm(instance=image)

    return render(request, 'image/edit/watermark.html', {
        'image': image,
        'form': form,
    })


@login_required
@require_GET
def image_edit_acquisition(request, id):
    image = get_image_or_404(Image.objects_including_wip, id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    from astrobin_apps_platesolving.solver import Solver

    dsa_qs = DeepSky_Acquisition.objects.filter(image=image)
    solar_system_acquisition = None

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=image)
    except:
        pass

    if dsa_qs:
        edit_type = 'deep_sky'
    elif solar_system_acquisition:
        edit_type = 'solar_system'
    elif 'edit_type' in request.GET:
        edit_type = request.GET['edit_type']
    else:
        edit_type = None

    deep_sky_acquisition_formset = None
    deep_sky_acquisition_basic_form = None
    advanced = False
    if edit_type == 'deep_sky' or (image.solution and image.solution.status != Solver.FAILED):
        advanced = dsa_qs[0].advanced if dsa_qs else False
        advanced = request.GET['advanced'] if 'advanced' in request.GET else advanced
        advanced = True if advanced == 'true' else advanced
        advanced = False if advanced == 'false' else advanced
        if advanced:
            extra = 0
            if 'add_more' in request.GET:
                extra = 1
            if not dsa_qs:
                extra = 1
            DSAFormSet = inlineformset_factory(Image, DeepSky_Acquisition, extra=extra, can_delete=False,
                                               form=DeepSky_AcquisitionForm)
            profile = image.user.userprofile
            filter_queryset = profile.filters.all()
            deep_sky_acquisition_formset = DSAFormSet(instance=image, form_kwargs={'queryset': filter_queryset})
        else:
            dsa = dsa_qs[0] if dsa_qs else DeepSky_Acquisition({image: image, advanced: False})
            deep_sky_acquisition_basic_form = DeepSky_AcquisitionBasicForm(instance=dsa)

    response_dict = {
        'image': image,
        'edit_type': edit_type,
        'ssa_form': SolarSystem_AcquisitionForm(instance=solar_system_acquisition),
        'deep_sky_acquisitions': deep_sky_acquisition_formset,
        'deep_sky_acquisition_basic_form': deep_sky_acquisition_basic_form,
        'advanced': advanced,
        'solar_system_acquisition': solar_system_acquisition,
    }

    return render(request, 'image/edit/acquisition.html', response_dict)


@login_required
@require_GET
def image_edit_acquisition_reset(request, id):
    image = get_image_or_404(Image.objects_including_wip, id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    DeepSky_Acquisition.objects.filter(image=image).delete()
    SolarSystem_Acquisition.objects.filter(image=image).delete()

    response_dict = {
        'image': image,
        'deep_sky_acquisition_basic_form': DeepSky_AcquisitionBasicForm(),
    }
    return render(request, 'image/edit/acquisition.html', response_dict)


@login_required
@require_GET
def image_edit_make_final(request, id):
    image = get_image_or_404(Image.objects_including_wip, id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    revisions = ImageRevision.all_objects.filter(image=image)
    for r in revisions:
        r.is_final = False
        r.save(keep_deleted=True)
    image.is_final = True
    image.save(keep_deleted=True)

    return HttpResponseRedirect(image.get_absolute_url())


@login_required
@require_GET
def image_edit_revision_make_final(request, id):
    r = get_object_or_404(ImageRevision, pk=id)
    if request.user != r.image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    other = ImageRevision.all_objects.filter(image=r.image)
    for i in other:
        i.is_final = False
        i.save(keep_deleted=True)

    r.image.is_final = False
    r.image.save(keep_deleted=True)

    r.is_final = True
    r.save(keep_deleted=True)

    return HttpResponseRedirect('/%s/%s/' % (r.image.get_id(), r.label))


@login_required
@require_GET
def image_edit_license(request, id):
    image = get_image_or_404(Image.objects_including_wip, id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    form = ImageLicenseForm(instance=image)
    return render(request, 'image/edit/license.html', {
        'form': form,
        'image': image
    })


@login_required
def image_edit_platesolving_settings(request, id, revision_label):
    image = get_image_or_404(Image.objects_including_wip, id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if revision_label in (None, 'None', '0'):
        url = reverse('image_edit_platesolving_settings', args=(image.get_id(),))
        if image.revisions.count() > 0:
            return_url = reverse('image_detail', args=(image.get_id(), '0',))
        else:
            return_url = reverse('image_detail', args=(image.get_id(),))
        solution, created = Solution.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Image),
            object_id=image.pk)
    else:
        url = reverse('image_edit_platesolving_settings', args=(image.get_id(), revision_label,))
        return_url = reverse('image_detail', args=(image.get_id(), revision_label,))
        revision = ImageRevision.objects.get(image=image, label=revision_label)
        solution, created = Solution.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(ImageRevision),
            object_id=revision.pk)

    settings = solution.settings
    if settings is None:
        solution.settings = PlateSolvingSettings.objects.create()
        solution.save()

    if request.method == 'GET':
        form = PlateSolvingSettingsForm(instance=settings)
        return render(request, 'image/edit/platesolving_settings.html', {
            'form': form,
            'image': image,
            'revision_label': revision_label,
            'return_url': return_url,
        })

    if request.method == 'POST':
        form = PlateSolvingSettingsForm(instance=settings, data=request.POST)
        if not form.is_valid():
            messages.error(
                request,
                _("There was one or more errors processing the form. You may need to scroll down to see them."))
            return render(request, 'image/edit/platesolving_settings.html', {
                'form': form,
                'image': image,
                'revision_label': revision_label,
                'return_url': return_url,
            })

        form.save()
        solution.clear()

        messages.success(
            request,
            _("Form saved. A new plate-solving process will start now."))
        return HttpResponseRedirect(return_url)


@login_required
def image_edit_platesolving_advanced_settings(request, id, revision_label):
    image = get_image_or_404(Image.objects_including_wip, id)
    if request.user != image.user and not request.user.is_superuser and not can_perform_advanced_platesolving(
            image.user):
        return HttpResponseForbidden()

    if revision_label in (None, 'None', '0'):
        if image.revisions.count() > 0:
            return_url = reverse('image_detail', args=(image.get_id(), '0',))
        else:
            return_url = reverse('image_detail', args=(image.get_id(),))
        solution, created = Solution.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Image),
            object_id=image.pk)
    else:
        return_url = reverse('image_detail', args=(image.get_id(), revision_label,))
        revision = ImageRevision.objects.get(image=image, label=revision_label)
        solution, created = Solution.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(ImageRevision),
            object_id=revision.pk)

    advanced_settings = solution.advanced_settings
    if advanced_settings is None:
        solution.advanced_settings = PlateSolvingAdvancedSettings.objects.create()
        solution.save()

    if request.method == 'GET':
        form = PlateSolvingAdvancedSettingsForm(instance=advanced_settings)
        return render(request, 'image/edit/platesolving_advanced_settings.html', {
            'form': form,
            'image': image,
            'revision_label': revision_label,
            'return_url': return_url,
        })

    if request.method == 'POST':
        form = PlateSolvingAdvancedSettingsForm(request.POST or None, request.FILES or None, instance=advanced_settings)
        if not form.is_valid():
            messages.error(
                request,
                _("There was one or more errors processing the form. You may need to scroll down to see them."))
            return render(request, 'image/edit/platesolving_advanced_settings.html', {
                'form': form,
                'image': image,
                'revision_label': revision_label,
                'return_url': return_url,
            })

        form.save()
        solution.clear_advanced()

        messages.success(
            request,
            _("Form saved. A new advanced plate-solving process will start now."))
        return HttpResponseRedirect(return_url)


@login_required
def image_restart_platesolving(request, id, revision_label):
    image = get_image_or_404(Image.objects_including_wip, id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if revision_label in (None, 'None', '0'):
        if image.revisions.count() > 0:
            return_url = reverse('image_detail', args=(image.get_id(), '0',))
        else:
            return_url = reverse('image_detail', args=(image.get_id(),))
        solution, created = Solution.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Image),
            object_id=image.pk)
    else:
        return_url = reverse('image_detail', args=(image.get_id(), revision_label,))
        revision = ImageRevision.objects.get(image=image, label=revision_label)
        solution, created = Solution.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(ImageRevision),
            object_id=revision.pk)

    solution.delete()

    return HttpResponseRedirect(return_url)


@login_required
def image_restart_advanced_platesolving(request, id, revision_label):
    image = get_image_or_404(Image.objects_including_wip, id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if revision_label in (None, 'None', '0'):
        if image.revisions.count() > 0:
            return_url = reverse('image_detail', args=(image.get_id(), '0',))
        else:
            return_url = reverse('image_detail', args=(image.get_id(),))
        solution, created = Solution.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Image),
            object_id=image.pk)
    else:
        return_url = reverse('image_detail', args=(image.get_id(), revision_label,))
        revision = ImageRevision.objects.get(image=image, label=revision_label)
        solution, created = Solution.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(ImageRevision),
            object_id=revision.pk)

    solution.clear_advanced()

    return HttpResponseRedirect(return_url)


@login_required
@require_POST
def image_edit_save_watermark(request):
    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404

    image = get_image_or_404(Image.objects_including_wip, image_id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    form = ImageEditWatermarkForm(data=request.POST, instance=image)
    if not form.is_valid():
        messages.error(request,
                       _("There was one or more errors processing the form. You may need to scroll down to see them."))
        return render(request, 'image/edit/watermark.html', {
            'image': image,
            'form': form,
        })

    form.save()

    # Save defaults in profile
    profile = image.user.userprofile
    profile.default_watermark = form.cleaned_data['watermark']
    profile.default_watermark_text = form.cleaned_data['watermark_text']
    profile.default_watermark_position = form.cleaned_data['watermark_position']
    profile.default_watermark_size = form.cleaned_data['watermark_size']
    profile.default_watermark_opacity = form.cleaned_data['watermark_opacity']
    profile.save(keep_deleted=True)

    if not image.title:
        return HttpResponseRedirect(
            reverse('image_edit_basic', kwargs={'id': image.get_id()}))

    # Force new thumbnails
    image.thumbnail_invalidate()

    return HttpResponseRedirect(image.get_absolute_url())


@login_required
@require_POST
def image_edit_save_acquisition(request):
    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404

    image = get_image_or_404(Image.objects_including_wip, image_id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    edit_type = request.POST.get('edit_type')
    advanced = request.POST['advanced'] if 'advanced' in request.POST else False
    advanced = True if advanced == 'true' else False

    response_dict = {
        'image': image,
        'edit_type': edit_type,
    }

    dsa_qs = DeepSky_Acquisition.objects.filter(image=image)

    for a in SolarSystem_Acquisition.objects.filter(image=image):
        a.delete()

    if edit_type == 'deep_sky' or image.solution:
        if advanced:
            DSAFormSet = inlineformset_factory(Image, DeepSky_Acquisition, can_delete=False,
                                               form=DeepSky_AcquisitionForm)
            saving_data = {}
            for i in request.POST:
                saving_data[i] = request.POST[i]
            saving_data['advanced'] = advanced
            deep_sky_acquisition_formset = DSAFormSet(saving_data, instance=image)
            response_dict['deep_sky_acquisitions'] = deep_sky_acquisition_formset
            response_dict['advanced'] = True
            if deep_sky_acquisition_formset.is_valid():
                deep_sky_acquisition_formset.save()
                if 'add_more' in request.POST:
                    DSAFormSet = inlineformset_factory(Image, DeepSky_Acquisition, extra=1, can_delete=False,
                                                       form=DeepSky_AcquisitionForm)
                    profile = image.user.userprofile
                    filter_queryset = profile.filters.all()
                    deep_sky_acquisition_formset = DSAFormSet(instance=image, form_kwargs={'queryset': filter_queryset})
                    response_dict['deep_sky_acquisitions'] = deep_sky_acquisition_formset
                    response_dict['next_acquisition_session'] = deep_sky_acquisition_formset.total_form_count() - 1
                    if not dsa_qs:
                        messages.info(request, _("Fill in one session, before adding more."))
                    return render(request, 'image/edit/acquisition.html', response_dict)
            else:
                messages.error(request, _(
                    "There was one or more errors processing the form. You may need to scroll down to see them."))
                return render(request, 'image/edit/acquisition.html', response_dict)
        else:
            DeepSky_Acquisition.objects.filter(image=image).delete()
            dsa = DeepSky_Acquisition()
            dsa.image = image
            deep_sky_acquisition_basic_form = DeepSky_AcquisitionBasicForm(data=request.POST, instance=dsa)
            if deep_sky_acquisition_basic_form.is_valid():
                deep_sky_acquisition_basic_form.save()
            else:
                messages.error(request, _(
                    "There was one or more errors processing the form. You may need to scroll down to see them."))
                response_dict['deep_sky_acquisition_basic_form'] = deep_sky_acquisition_basic_form
                return render(request, 'image/edit/acquisition.html', response_dict)

    elif edit_type == 'solar_system':
        ssa = SolarSystem_Acquisition(image=image)
        form = SolarSystem_AcquisitionForm(data=request.POST, instance=ssa)
        response_dict['ssa_form'] = form
        if not form.is_valid():
            response_dict['ssa_form'] = form
            messages.error(request, _(
                "There was one or more errors processing the form. You may need to scroll down to see them."))
            return render(request, 'image/edit/acquisition.html', response_dict)
        form.save()

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect(image.get_absolute_url())


@login_required
@require_POST
def image_edit_save_license(request):
    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404

    image = get_image_or_404(Image.objects_including_wip, image_id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    form = ImageLicenseForm(data=request.POST, instance=image)
    if not form.is_valid():
        messages.error(request,
                       _("There was one or more errors processing the form. You may need to scroll down to see them."))
        return render(request, 'image/edit/license.html', {
            'form': form,
            'image': image
        })

    form.save()

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect(image.get_absolute_url())


@login_required
@require_GET
def me(request):
    return HttpResponseRedirect(
        '/users/%s/%s' % (request.user.username, '?staging' if 'staging' in request.GET else ''))


@require_GET
@silk_profile('User page')
def user_page(request, username):
    """Shows the user's public page"""
    user = get_object_or_404(UserProfile, user__username=username).user

    if Image.objects_including_wip.filter(user=user, moderator_decision=2).count() > 0:
        if (not request.user.is_authenticated() or \
                not request.user.is_superuser and \
                not request.user.userprofile.is_image_moderator()):
            raise Http404

    profile = user.userprofile
    user_ct = ContentType.objects.get_for_model(User)
    image_ct = ContentType.objects.get_for_model(Image)

    viewer_profile = None
    if request.user.is_authenticated():
        viewer_profile = request.user.userprofile

    section = 'public'
    subsection = request.GET.get('sub')
    if subsection is None:
        subsection = profile.default_gallery_sorting
        if subsection == 1:
            subsection = 'acquired'
        elif subsection == 2:
            subsection = 'subject'
        elif subsection == 3:
            subsection = 'year'
        elif subsection == 4:
            subsection = 'gear'
        elif subsection == 5:
            subsection = 'collections'
        elif subsection == 6:
            subsection = 'title'
        else:
            subsection = 'uploaded'

    if subsection == 'collections':
        return HttpResponseRedirect(reverse('user_collections_list', args=(username,)))

    active = request.GET.get('active')
    menu = []

    qs = UserService(user).get_public_images()
    wip_qs = UserService(user).get_wip_images()
    corrupted_qs = UserService(user).get_corrupted_images()

    if request.user != user:
        qs = qs.exclude(pk__in=[x.pk for x in corrupted_qs])

    if 'staging' in request.GET:
        if request.user != user and not request.user.is_superuser:
            return HttpResponseForbidden()
        qs = wip_qs
        section = 'staging'
        subsection = None
    if 'trash' in request.GET:
        if request.user != user or not can_restore_from_trash(request.user) and not request.user.is_superuser:
            return HttpResponseForbidden()
        qs = Image.deleted_objects.filter(user=user)
        section = 'trash'
        subsection = None
    elif 'corrupted' in request.GET:
        if request.user != user and not request.user.is_superuser:
            return HttpResponseForbidden()
        qs = corrupted_qs
        section = 'corrupted'
        subsection = None
    else:
        #########
        # TITLE #
        #########
        if subsection == 'title':
            qs = qs.order_by('title')

        ############
        # UPLOADED #
        ############
        if subsection == 'uploaded':
            # All good already
            pass

        ############
        # ACQUIRED #
        ############
        elif subsection == 'acquired':
            lad_sql = 'SELECT date FROM astrobin_acquisition ' \
                      'WHERE date IS NOT NULL AND image_id = astrobin_image.id ' \
                      'ORDER BY date DESC ' \
                      'LIMIT 1'
            qs = qs.extra(select={'last_acquisition_date': lad_sql},
                          order_by=['-last_acquisition_date'])

        ########
        # YEAR #
        ########
        elif subsection == 'year':
            acq = Acquisition.objects.filter(
                image__user=user,
                image__is_wip=False,
                image__deleted=None)
            if acq:
                years = sorted(list(set([a.date.year for a in acq if a.date])), reverse=True)
                nd = _("No date specified")
                menu = [(str(x), str(x)) for x in years] + [(0, nd)]

                if active == '0':
                    qs = qs.filter(
                        Q(subject_type__in=(
                            SubjectType.DEEP_SKY,
                            SubjectType.SOLAR_SYSTEM,
                            SubjectType.WIDE_FIELD,
                            SubjectType.STAR_TRAILS,
                            SubjectType.NORTHERN_LIGHTS,
                            SubjectType.OTHER
                        )) &
                        Q(acquisition=None) | Q(acquisition__date=None)).distinct()
                else:
                    if active is None:
                        if years:
                            active = str(years[0])

                    if active:
                        qs = qs.filter(acquisition__date__year=active).distinct()

        ########
        # GEAR #
        ########
        elif subsection == 'gear':
            telescopes = profile.telescopes.all()
            cameras = profile.cameras.all()

            nd = _("No imaging telescopes or lenses, or no imaging cameras specified")
            gi = _("Gear images")

            menu += [(x.id, unicode(x)) for x in telescopes]
            menu += [(x.id, unicode(x)) for x in cameras]
            menu += [(0, nd)]
            menu += [(-1, gi)]

            if active == '0':
                qs = qs.filter(
                    (Q(subject_type=SubjectType.DEEP_SKY) | Q(subject_type=SubjectType.SOLAR_SYSTEM)) &
                    (Q(imaging_telescopes=None) | Q(imaging_cameras=None))).distinct()
            elif active == '-1':
                qs = qs.filter(Q(subject_type=SubjectType.GEAR)).distinct()
            else:
                if active is None:
                    if telescopes:
                        active = telescopes[0].id
                if active:
                    qs = qs.filter(Q(imaging_telescopes__id=active) |
                                   Q(imaging_cameras__id=active)).distinct()

        ###########
        # SUBJECT #
        ###########
        elif subsection == 'subject':
            menu += [('DEEP', _("Deep sky"))]
            menu += [('SOLAR', _("Solar system"))]
            menu += [('WIDE', _("Extremely wide field"))]
            menu += [('TRAILS', _("Star trails"))]
            menu += [('GEAR', _("Gear"))]
            menu += [('OTHER', _("Other"))]

            if active is None:
                active = 'DEEP'

            if active == 'DEEP':
                qs = qs.filter(subject_type=SubjectType.DEEP_SKY)

            elif active == 'SOLAR':
                qs = qs.filter(subject_type=SubjectType.SOLAR_SYSTEM)

            elif active == 'WIDE':
                qs = qs.filter(subject_type=SubjectType.WIDE_FIELD)

            elif active == 'TRAILS':
                qs = qs.filter(subject_type=SubjectType.STAR_TRAILS)

            elif active == 'GEAR':
                qs = qs.filter(subject_type=SubjectType.GEAR)

            elif active == 'OTHER':
                qs = qs.filter(subject_type=SubjectType.OTHER)

        ###########
        # NO DATA #
        ###########
        elif subsection == 'nodata':
            menu += [('SUB', _("No subjects specified"))]
            menu += [('GEAR', _("No imaging telescopes or lenses, or no imaging cameras specified"))]
            menu += [('ACQ', _("No acquisition details specified"))]

            if active is None:
                active = 'SUB'

            if active == 'SUB':
                qs = qs.filter(
                    (Q(subject_type=SubjectType.DEEP_SKY) | Q(subject_type=SubjectType.SOLAR_SYSTEM)) &
                    (Q(solar_system_main_subject=None)))
                qs = [x for x in qs if (x.solution is None or x.solution.objects_in_field is None)]
                for i in qs:
                    for r in i.revisions.all():
                        if r.solution and r.solution.objects_in_field:
                            if i in qs:
                                qs.remove(i)

            elif active == 'GEAR':
                qs = qs.filter(
                    Q(subject_type__in=(
                        SubjectType.DEEP_SKY,
                        SubjectType.SOLAR_SYSTEM,
                        SubjectType.WIDE_FIELD,
                        SubjectType.STAR_TRAILS,
                        SubjectType.NORTHERN_LIGHTS,
                    )) &
                    (Q(imaging_telescopes=None) | Q(imaging_cameras=None)))

            elif active == 'ACQ':
                qs = qs.filter(
                    Q(subject_type__in=(
                        SubjectType.DEEP_SKY,
                        SubjectType.SOLAR_SYSTEM,
                        SubjectType.WIDE_FIELD,
                        SubjectType.STAR_TRAILS,
                        SubjectType.NORTHERN_LIGHTS,
                    )) &
                    Q(acquisition=None))

    # Calculate some stats
    from django.template.defaultfilters import timesince
    from pybb.models import Post

    member_since = None
    date_time = user.date_joined.replace(tzinfo=None)
    span = timesince(date_time)
    if span == "0 " + _("minutes"):
        member_since = _("seconds ago")
    else:
        member_since = _("%s ago") % span

    last_login = user.last_login
    if request.user.is_authenticated():
        viewer_profile = request.user.userprofile
        last_login = to_user_timezone(user.last_login, viewer_profile)

    followers = ToggleProperty.objects.toggleproperties_for_object("follow", user).count()
    following = ToggleProperty.objects.filter(
        property_type="follow",
        user=user,
        content_type=user_ct).count()

    key = "User.%d.Stats" % user.pk
    data = cache.get(key)
    if data is None:
        sqs = SearchQuerySet()
        sqs = sqs.filter(username=user.username).models(Image)
        sqs = sqs.order_by('-uploaded')

        data = {}
        try:
            data['images'] = len(sqs)
            integrated_images = len(sqs.filter(integration__gt=0))
            data['integration'] = sum([x.integration for x in sqs]) / 3600.0
            data['avg_integration'] = (data['integration'] / integrated_images) if integrated_images > 0 else 0
        except SearchFieldError:
            data['images'] = 0
            data['integration'] = 0
            data['avg_integration'] = 0

        cache.set(key, data, 84600)

    stats = (
        (_('Member since'), member_since),
        (_('Last login'), last_login),
        (_('Total integration time'), "%.1f %s" % (data['integration'], _("hours"))),
        (_('Average integration time'), "%.1f %s" % (data['avg_integration'], _("hours"))),
        (_('Forum posts'), "%d" % Post.objects.filter(user=user).count()),
    )

    response_dict = {
        'followers': followers,
        'following': following,
        'image_list': qs,
        'sort': request.GET.get('sort'),
        'view': request.GET.get('view', 'default'),
        'requested_user': user,
        'profile': profile,
        'private_message_form': PrivateMessageForm(),
        'section': section,
        'subsection': subsection,
        'active': active,
        'menu': menu,
        'stats': stats,
        'images_no': data['images'],
        'alias': 'gallery',
        'has_corrupted_images': Image.objects_including_wip.filter(
            corrupted=True, user=user).count() > 0,
    }

    response_dict.update(UserService(user).get_image_numbers(include_corrupted=request.user == user))

    template_name = 'user/profile.html'
    if request.is_ajax():
        template_name = 'inclusion_tags/image_list_entries.html'

    return render(request, template_name, response_dict)


@require_GET
def user_page_commercial_products(request, username):
    user = get_object_or_404(UserProfile, user__username=username).user
    if user != request.user:
        return HttpResponseForbidden()

    profile = user.userprofile
    image_ct = ContentType.objects.get_for_model(Image)

    response_dict = {
        'requested_user': user,
        'profile': profile,
        'user_is_producer': user_is_producer(user),
        'user_is_retailer': user_is_retailer(user),
        'commercial_gear_list': CommercialGear.objects.filter(producer=user).exclude(base_gear=None),
        'retailed_gear_list': RetailedGear.objects.filter(retailer=user).exclude(gear=None),
        'claim_commercial_gear_form': ClaimCommercialGearForm(user=user),
        'merge_commercial_gear_form': MergeCommercialGearForm(user=user),
        'claim_retailed_gear_form': ClaimRetailedGearForm(user=user),
        'merge_retailed_gear_form': MergeRetailedGearForm(user=user),
    }

    response_dict.update(UserService(user).get_image_numbers(include_corrupted=request.user == user))

    return render(request, 'user/profile/commercial/products.html', response_dict)


@user_passes_test(lambda u: u.is_superuser)
def user_ban(request, username):
    user = get_object_or_404(UserProfile, user__username=username).user

    if request.method == 'POST':
        user.userprofile.delete()

    return render(request, 'user/ban.html', {
        'user': user,
        'deleted': request.method == 'POST',
    })


@require_GET
def user_page_bookmarks(request, username):
    user = get_object_or_404(UserProfile, user__username=username).user

    template_name = 'user/bookmarks.html'
    if request.is_ajax():
        template_name = 'inclusion_tags/image_list_entries.html'

    response_dict = {
        'requested_user': user,
        'image_list': UserService(user).get_bookmarked_images(),
        'private_message_form': PrivateMessageForm(),
        'alias': 'gallery',
    }

    response_dict.update(UserService(user).get_image_numbers(include_corrupted=request.user == user))

    return render(request, template_name, response_dict)


@require_GET
def user_page_liked(request, username):
    user = get_object_or_404(UserProfile, user__username=username).user

    template_name = 'user/liked.html'
    if request.is_ajax():
        template_name = 'inclusion_tags/image_list_entries.html'

    response_dict = {
        'requested_user': user,
        'image_list': UserService(user).get_liked_images(),
        'private_message_form': PrivateMessageForm(),
        'alias': 'gallery',
    }

    response_dict.update(UserService(user).get_image_numbers(include_corrupted=request.user == user))

    return render(request, template_name, response_dict)


@require_GET
@page_template('astrobin_apps_users/inclusion_tags/user_list_entries.html', key='users_page')
def user_page_following(request, username, extra_context=None):
    user = get_object_or_404(UserProfile, user__username=username).user

    user_ct = ContentType.objects.get_for_model(User)
    followed_users = []
    properties = ToggleProperty.objects.filter(
        property_type="follow",
        user=user,
        content_type=user_ct)

    for p in properties:
        try:
            followed_users.append(user_ct.get_object_for_this_type(pk=p.object_id))
        except User.DoesNotExist:
            pass

    template_name = 'user/following.html'
    if request.is_ajax():
        template_name = 'astrobin_apps_users/inclusion_tags/user_list_entries.html'

    response_dict = {
        'request_user': UserProfile.objects.get(
            user=request.user).user if request.user.is_authenticated() else None,
        'requested_user': user,
        'user_list': followed_users,
        'view': request.GET.get('view', 'default'),
        'private_message_form': PrivateMessageForm(),
    }

    response_dict.update(UserService(user).get_image_numbers(include_corrupted=request.user == user))

    return render(request, template_name, response_dict)


@require_GET
@page_template('astrobin_apps_users/inclusion_tags/user_list_entries.html', key='users_page')
def user_page_followers(request, username, extra_context=None):
    user = get_object_or_404(UserProfile, user__username=username).user

    user_ct = ContentType.objects.get_for_model(User)
    followers = [
        x.user for x in
        ToggleProperty.objects.filter(
            property_type="follow",
            object_id=user.pk,
            content_type=user_ct)
    ]

    template_name = 'user/followers.html'
    if request.is_ajax():
        template_name = 'astrobin_apps_users/inclusion_tags/user_list_entries.html'

    response_dict = {
        'request_user': UserProfile.objects.get(
            user=request.user).user if request.user.is_authenticated() else None,
        'requested_user': user,
        'user_list': followers,
        'view': request.GET.get('view', 'default'),
        'private_message_form': PrivateMessageForm(),
    }

    response_dict.update(UserService(user).get_image_numbers(include_corrupted=request.user == user))

    return render(request, template_name, response_dict)


@require_GET
def user_page_plots(request, username):
    """Shows the user's public page"""
    user = get_object_or_404(UserProfile, user__username=username).user
    profile = user.userprofile

    response_dict = {
        'requested_user': user,
        'profile': profile,
    }

    response_dict.update(UserService(user).get_image_numbers(include_corrupted=request.user == user))

    return render(request, 'user/plots.html', response_dict)


@require_GET
def user_page_api_keys(request, username):
    """Shows the user's API Keys"""
    user = get_object_or_404(UserProfile, user__username=username).user
    if user != request.user:
        return HttpResponseForbidden()

    profile = user.userprofile
    keys = App.objects.filter(registrar=user)

    response_dict = {
        'requested_user': user,
        'profile': profile,
        'api_keys': keys,
    }

    response_dict.update(UserService(user).get_image_numbers(include_corrupted=request.user == user))

    return render(request, 'user/api_keys.html', response_dict)


@require_GET
def user_profile_stats_get_integration_hours_ajax(request, username, period='monthly', since=0):
    user = get_object_or_404(UserProfile, user__username=username).user

    import astrobin.stats as _s
    (label, data, options) = _s.integration_hours(user, period, int(since))
    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def user_profile_stats_get_integration_hours_by_gear_ajax(request, username, period='monthly'):
    user = get_object_or_404(UserProfile, user__username=username).user

    import astrobin.stats as _s
    (data, options) = _s.integration_hours_by_gear(user, period)
    response_dict = {
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def user_profile_stats_get_uploaded_images_ajax(request, username, period='monthly'):
    user = get_object_or_404(UserProfile, user__username=username).user

    import astrobin.stats as _s
    (label, data, options) = _s.uploaded_images(user, period)
    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def user_profile_stats_get_views_ajax(request, username, period='monthly'):
    user = get_object_or_404(UserProfile, user__username=username).user

    import astrobin.stats as _s
    (label, data, options) = _s.views(user, period)
    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_get_image_views_ajax(request, id, period='monthly'):
    import astrobin.stats as _s

    (label, data, options) = _s.image_views(id, period)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@login_required
@require_GET
def user_profile_edit_basic(request):
    """Edits own profile"""
    profile = request.user.userprofile
    form = UserProfileEditBasicForm(instance=profile)

    response_dict = {
        'form': form,
    }
    return render(request, "user/profile/edit/basic.html", response_dict)


@login_required
@require_POST
def user_profile_save_basic(request):
    """Saves the form"""

    profile = request.user.userprofile
    form = UserProfileEditBasicForm(data=request.POST, instance=profile)
    response_dict = {'form': form}

    if not form.is_valid():
        return render(request, "user/profile/edit/basic.html", response_dict)

    form.save()

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect("/profile/edit/basic/")


@login_required
@user_passes_test(lambda u: user_is_producer(u) or user_is_retailer(u))
def user_profile_edit_commercial(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileEditCommercialForm(data=request.POST, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, _("Form saved. Thank you!"))
            return HttpResponseRedirect('/profile/edit/commercial/')
    else:
        form = UserProfileEditCommercialForm(instance=profile)

    return render(request, "user/profile/edit/commercial.html", {
        'form': form,
    })


@login_required
@user_passes_test(lambda u: user_is_retailer(u))
def user_profile_edit_retailer(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileEditRetailerForm(data=request.POST, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, _("Form saved. Thank you!"))
            return HttpResponseRedirect('/profile/edit/retailer/')
    else:
        form = UserProfileEditRetailerForm(instance=profile)

    return render(request, "user/profile/edit/retailer.html", {
        'form': form,
    })


@login_required
@require_GET
def user_profile_edit_license(request):
    profile = request.user.userprofile
    form = DefaultImageLicenseForm(instance=profile)
    return render(request, 'user/profile/edit/license.html', {
        'form': form
    })


@login_required
@require_POST
def user_profile_save_license(request):
    profile = request.user.userprofile
    form = DefaultImageLicenseForm(data=request.POST, instance=profile)

    if not form.is_valid():
        return render(request, 'user/profile/edit/license.html', {
            'form': form
        })

    form.save()

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect('/profile/edit/license/')


@login_required
@require_GET
def user_profile_edit_gear(request):
    """Edits own profile"""
    profile = request.user.userprofile

    def uniq(seq):
        # Not order preserving
        keys = {}
        for e in seq:
            keys[e] = 1
        return keys.keys()

    response_dict = {
        'initial': 'initial' in request.GET,
        'all_gear_makes': simplejson.dumps(
            uniq([x.get_make() for x in Gear.objects.exclude(make=None).exclude(make='')])),
        'all_gear_names': simplejson.dumps(
            uniq([x.get_name() for x in Gear.objects.exclude(name=None).exclude(name='')])),
    }

    prefill = {}
    for attr, label, klass in (
            ['telescopes', _("Telescopes and lenses"), 'Telescope'],
            ['cameras', _("Cameras"), 'Camera'],
            ['mounts', _("Mounts"), 'Mount'],
            ['focal_reducers', _("Focal reducers"), 'FocalReducer'],
            ['software', _("Software"), 'Software'],
            ['filters', _("Filters"), 'Filter'],
            ['accessories', _("Accessories"), 'Accessory']):
        all_gear = getattr(profile, attr).all()
        prefill[label] = [all_gear, klass]

    response_dict['prefill'] = prefill
    return render(request, "user/profile/edit/gear.html", response_dict)


@login_required
@require_POST
def user_profile_edit_gear_remove(request, id):
    profile = request.user.userprofile
    gear, gear_type = get_correct_gear(id)
    if not gear:
        raise Http404

    profile.remove_gear(gear, gear_type)

    return ajax_success()


@login_required
@require_GET
def user_profile_edit_locations(request):
    profile = request.user.userprofile
    LocationsFormset = inlineformset_factory(
        UserProfile, Location, form=LocationEditForm, extra=1)

    return render(request, 'user/profile/edit/locations.html', {
        'formset': LocationsFormset(instance=profile),
        'profile': profile,
    })


@login_required
@require_POST
def user_profile_save_locations(request):
    profile = request.user.userprofile
    LocationsFormset = inlineformset_factory(
        UserProfile, Location, form=LocationEditForm, extra=1)
    formset = LocationsFormset(data=request.POST, instance=profile)
    if not formset.is_valid():
        messages.error(request,
                       _("There was one or more errors processing the form. You may need to scroll down to see them."))
        return render(request, 'user/profile/edit/locations.html', {
            'formset': formset,
            'profile': profile,
        })

    formset.save()
    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect('/profile/edit/locations/')


@login_required
@require_POST
def user_profile_save_gear(request):
    """Saves the form"""

    profile = request.user.userprofile

    profile.telescopes.clear()
    profile.mounts.clear()
    profile.cameras.clear()
    profile.focal_reducers.clear()
    profile.filters.clear()
    profile.software.clear()
    profile.accessories.clear()

    form = UserProfileEditGearForm(data=request.POST)
    if not form.is_valid():
        response_dict = {"form": form}
        prefill_dict = {}
        for k in ("telescopes", "mounts", "cameras", "focal_reducers",
                  "software", "filters", "accessories",):
            allGear = getattr(profile, k).all()
            prefill_dict[k] = jsonDump(allGear)

        return render(request, "user/profile/edit/gear.html", response_dict)

    for k, v in {"telescopes": [Telescope, profile.telescopes],
                 "mounts": [Mount, profile.mounts],
                 "cameras": [Camera, profile.cameras],
                 "focal_reducers": [FocalReducer, profile.focal_reducers],
                 "software": [Software, profile.software],
                 "filters": [Filter, profile.filters],
                 "accessories": [Accessory, profile.accessories],
                 }.iteritems():
        (names, value) = valueReader(request.POST, k)
        for name in names:
            try:
                id = float(name)
                gear_item = v[0].objects.get(id=id)
            except ValueError:
                gear_item, created = v[0].objects.get_or_create(name=name)
            except v[0].DoesNotExist:
                continue
            getattr(profile, k).add(gear_item)
        form.fields[k].initial = value

    profile.save(keep_deleted=True)

    initial = "&initial=true" if "initial" in request.POST else ""
    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect("/profile/edit/gear/" + initial)


@login_required
def user_profile_flickr_import(request):
    from django.core.files import File
    from django.core.files.temp import NamedTemporaryFile
    from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free

    response_dict = {
        'readonly': settings.READONLY_MODE
    }

    log.debug("Flickr import (user %s): accessed view" % request.user.username)

    if not request.user.is_superuser and is_free(request.user) or settings.READONLY_MODE:
        return render(request, "user/profile/flickr_import.html", response_dict)

    flickr_token = None
    if 'flickr_token_token' in request.session:
        flickr_token = FlickrAccessToken(
            request.session['flickr_token_token'],
            request.session['flickr_token_token_secret'],
            request.session['flickr_token_access_level'],
            request.session['flickr_token_fullname'],
            request.session['flickr_token_username'],
            request.session['flickr_token_token_user_nsid'],
        )

    flickr = flickrapi.FlickrAPI(settings.FLICKR_API_KEY,
                                 settings.FLICKR_SECRET,
                                 username=request.user.username,
                                 token=flickr_token)

    if not flickr.token_valid(perms=u'read'):
        # We were never authenticated, or authentication expired. We need
        # to reauthenticate.
        log.debug("Flickr import (user %s): token not valid" % request.user.username)
        flickr.get_request_token(settings.BASE_URL + reverse('flickr_auth_callback'))
        authorize_url = flickr.auth_url(perms=u'read')
        request.session['request_token'] = flickr.flickr_oauth.resource_owner_key
        request.session['request_token_secret'] = flickr.flickr_oauth.resource_owner_secret
        request.session['requested_permissions'] = flickr.flickr_oauth.requested_permissions
        return HttpResponseRedirect(authorize_url)

    if not request.POST:
        # If we made it this far (it's a GET request), it means that we
        # are authenticated with flickr. Let's fetch the sets and send them to
        # the template.
        log.debug("Flickr import (user %s): token valid, GET request, fetching sets" % request.user.username)

        # Does it have to be so insane to get the info on the
        # authenticated user?
        sets = flickr.photosets_getList().find('photosets').findall('photoset')

        log.debug("Flickr import (user %s): token valid, fetched sets" % request.user.username)
        template_sets = {}
        for set in sets:
            template_sets[set.find('title').text] = set.attrib['id']
        response_dict['flickr_sets'] = template_sets
    else:
        log.debug("Flickr import (user %s): token valid, POST request" % request.user.username)
        if 'id_flickr_set' in request.POST:
            log.debug("Flickr import (user %s): set in POST request" % request.user.username)
            set_id = request.POST['id_flickr_set']
            urls_sq = {}
            for photo in flickr.walk_set(set_id, extras='url_sq'):
                urls_sq[photo.attrib['id']] = photo.attrib['url_sq']
                response_dict['flickr_photos'] = urls_sq
        elif 'flickr_selected_photos[]' in request.POST:
            log.debug("Flickr import (user %s): photos in POST request" % request.user.username)
            selected_photos = request.POST.getlist('flickr_selected_photos[]')
            # Starting the process of importing
            for index, photo_id in enumerate(selected_photos):
                log.debug("Flickr import (user %s): iterating photo %s" % (request.user.username, photo_id))
                sizes = flickr.photos_getSizes(photo_id=photo_id)
                info = flickr.photos_getInfo(photo_id=photo_id).find('photo')

                title = info.find('title').text
                description = info.find('description').text

                # Attempt to find the largest image
                found_size = None
                for label in ['Square', 'Thumbnail', 'Small', 'Medium', 'Medium640', 'Large', 'Original']:
                    for size in sizes.find('sizes').findall('size'):
                        if size.attrib['label'] == label:
                            found_size = size

                if found_size is not None:
                    log.debug("Flickr import (user %s): found largest side of photo %s" % (
                        request.user.username, photo_id))
                    source = found_size.attrib['source']

                    img = NamedTemporaryFile(delete=True)
                    img.write(urllib2.urlopen(source).read())
                    img.flush()
                    img.seek(0)
                    f = File(img)

                    profile = request.user.userprofile
                    image = Image(image_file=f,
                                  user=request.user,
                                  title=title if title is not None else '',
                                  description=description if description is not None else '',
                                  subject_type=600,  # Default to Other only when doing a Flickr import
                                  is_wip=True,
                                  license=profile.default_license)
                    image.save(keep_deleted=True)
                    log.debug("Flickr import (user %s): saved image %d" % (request.user.username, image.pk))

        log.debug("Flickr import (user %s): returning ajax response: %s" % (
            request.user.username, simplejson.dumps(response_dict)))
        return ajax_response(response_dict)

    return render(request, "user/profile/flickr_import.html", response_dict)


def flickr_auth_callback(request):
    log.debug("Flickr import (user %s): received auth callback" % request.user.username)
    flickr = flickrapi.FlickrAPI(
        settings.FLICKR_API_KEY, settings.FLICKR_SECRET,
        username=request.user.username)
    flickr.flickr_oauth.resource_owner_key = request.session['request_token']
    flickr.flickr_oauth.resource_owner_secret = request.session['request_token_secret']
    flickr.flickr_oauth.requested_permissions = request.session['requested_permissions']
    verifier = request.GET['oauth_verifier']
    flickr.get_access_token(verifier)

    request.session['flickr_token_token'] = flickr.token_cache.token.token
    request.session['flickr_token_token_secret'] = flickr.token_cache.token.token_secret
    request.session['flickr_token_access_level'] = flickr.token_cache.token.access_level
    request.session['flickr_token_fullname'] = flickr.token_cache.token.fullname
    request.session['flickr_token_username'] = flickr.token_cache.token.username
    request.session['flickr_token_token_user_nsid'] = flickr.token_cache.token.user_nsid

    return HttpResponseRedirect("/profile/edit/flickr/")


@login_required
@require_POST
def user_profile_seen_realname(request):
    profile = request.user.userprofile
    profile.seen_realname = True
    profile.save(keep_deleted=True)

    return HttpResponseRedirect(request.POST.get('next', '/'))


@login_required
@require_POST
def user_profile_seen_email_permissions(request):
    profile = request.user.userprofile
    profile.seen_email_permissions = True
    profile.save(keep_deleted=True)

    return HttpResponseRedirect(request.POST.get('next', '/'))


@login_required
@require_GET
def user_profile_edit_preferences(request):
    """Edits own preferences"""
    profile = request.user.userprofile
    form = UserProfileEditPreferencesForm(instance=profile)
    response_dict = {
        'form': form,
    }

    return render(request, "user/profile/edit/preferences.html", response_dict)


@login_required
@require_POST
def user_profile_save_preferences(request):
    """Saves the form"""

    profile = request.user.userprofile
    form = UserProfileEditPreferencesForm(data=request.POST, instance=profile)
    response_dict = {'form': form}
    response = HttpResponseRedirect("/profile/edit/preferences/")

    if form.is_valid():
        form.save()
        # Activate the chosen language
        from django.utils.translation import check_for_language, activate
        lang = form.cleaned_data['language']
        if lang and check_for_language(lang):
            if hasattr(request, 'session'):
                request.session['django_language'] = lang

            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
            activate(lang)
    else:
        return render(request, "user/profile/edit/preferences.html", response_dict)

    messages.success(request, _("Form saved. Thank you!"))
    return response


@login_required
def user_profile_delete(request):
    if request.method == 'POST':
        request.user.userprofile.delete()
        auth.logout(request)

    return render(request, 'user/profile/delete.html', {})


@login_required
@require_POST
def image_revision_upload_process(request):
    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404

    image = get_image_or_404(Image.objects_including_wip, image_id)

    if settings.READONLY_MODE:
        messages.error(request, _(
            "AstroBin is currently in read-only mode, because of server maintenance. Please try again soon!"))
        return HttpResponseRedirect(image.get_absolute_url())

    form = ImageRevisionUploadForm(request.POST, request.FILES)

    if not form.is_valid():
        return upload_error(request, image)

    max_revisions = premium_get_max_allowed_revisions(request.user)
    if image.revisions.count() >= max_revisions:
        return upload_max_revisions_error(request, max_revisions, image)

    image_file = request.FILES["image_file"]
    ext = os.path.splitext(image_file.name)[1].lower()

    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        return upload_error(request, image)

    max_size = premium_get_max_allowed_image_size(request.user)
    if image_file.size > max_size:
        return upload_size_error(request, max_size, image)

    if image_file.size < 1e+7:
        try:
            from PIL import Image as PILImage
            trial_image = PILImage.open(image_file)
            trial_image.verify()
            image_file.file.seek(0)  # Because we opened it with PIL

            if ext == '.png' and trial_image.mode == 'I':
                messages.warning(request, _(
                    "You uploaded an Indexed PNG file. AstroBin will need to lower the color count to 256 in order to work with it."))
        except:
            return upload_error(request, image)

    revisions = ImageRevision.all_objects.filter(image=image).order_by('id')

    mark_as_final = request.POST.get(u'mark_as_final', None) == u'on' # type: bool

    highest_label = 'A'
    for r in revisions:
        highest_label = r.label
        if mark_as_final:
            r.is_final = False
            r.save(keep_deleted=True)

    image_revision = form.save(commit=False)

    if mark_as_final:
        image.is_final = False
        image.save(keep_deleted=True)
        image_revision.is_final = True

    image_revision.user = request.user
    image_revision.image = image
    image_revision.label = base26_encode(base26_decode(highest_label) + 1)

    w, h = image_revision.w, image_revision.h

    if w == 0 or h == 0:
        w, h = get_image_dimensions(image_revision.image_file.file)

    if w == image.w and h == image.h:
        image_revision.square_cropping = image.square_cropping

    image_revision.save(keep_deleted=True)

    messages.success(request, _("Image uploaded. Thank you!"))
    return HttpResponseRedirect(image_revision.get_absolute_url())


@require_GET
@user_passes_test(lambda u: u.is_superuser)
def stats(request):
    response_dict = {}

    sqs = SearchQuerySet()
    gs = GlobalStat.objects.first()

    if gs:
        response_dict['total_users'] = gs.users
        response_dict['total_images'] = gs.images
        response_dict['total_integration'] = gs.integration

    sort = '-user_integration'
    if 'sort' in request.GET:
        sort = request.GET.get('sort')
        if sort == 'tot_integration':
            sort = '-user_integration'
        elif sort == 'avg_integration':
            sort = '-user_avg_integration'
        elif sort == 'images':
            sort = '-user_images'

    queryset = sqs.filter(user_images__gt=0).models(User).order_by(sort)

    return object_list(
        request,
        queryset=queryset,
        template_name='stats.html',
        template_object_name='user',
        extra_context=response_dict,
    )


@require_GET
def trending_astrophotographers(request):
    response_dict = {}

    if 'page' in request.GET:
        raise Http404

    sqs = SearchQuerySet()

    sort = request.GET.get('sort', 'index')
    if sort == 'index':
        sort = '-normalized_likes'
    elif sort == 'followers':
        sort = '-followers'
    elif sort == 'integration':
        sort = '-integration'
    elif sort == 'images':
        sort = '-images'
    else:
        sort = '-normalized_likes'

    t = request.GET.get('t', '1y')
    if t not in ('', 'all', None):
        sort += '_%s' % t

    queryset = sqs.models(User).order_by(sort)

    return object_list(
        request,
        queryset=queryset,
        template_name='trending_astrophotographers.html',
        template_object_name='user',
        extra_context=response_dict,
    )


@require_GET
def api_help(request):
    return render(request, 'api.html')


@login_required
@require_GET
def location_edit(request, id):
    location = get_object_or_404(Location, pk=id)
    form = LocationEditForm(instance=location)

    return render(request, 'location/edit.html', {
        'form': form,
        'id': id,
    })


@require_GET
@never_cache
def set_language(request, lang):
    from django.utils.translation import check_for_language, activate

    next = request.GET.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', None)
    if not next:
        next = '/'
    response = HttpResponseRedirect(next)
    if lang and check_for_language(lang):
        if hasattr(request, 'session'):
            request.session['django_language'] = lang

        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
        activate(lang)

    if request.user.is_authenticated():
        profile = request.user.userprofile
        profile.language = lang
        profile.save(keep_deleted=True)

    return response


@require_GET
@login_required
@never_cache
def get_edit_gear_form(request, id):
    gear, gear_type = get_correct_gear(id)
    if not gear:
        raise Http404

    form = None
    if gear_type == 'Telescope':
        form = TelescopeEditForm(instance=gear)
    elif gear_type == 'Mount':
        form = MountEditForm(instance=gear)
    elif gear_type == 'Camera':
        form = CameraEditForm(instance=gear)
    elif gear_type == 'FocalReducer':
        form = FocalReducerEditForm(instance=gear)
    elif gear_type == 'Software':
        form = SoftwareEditForm(instance=gear)
    elif gear_type == 'Filter':
        form = FilterEditForm(instance=gear)
    elif gear_type == 'Accessory':
        form = AccessoryEditForm(instance=gear)

    from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
    response_dict = {
        'form': as_bootstrap(form, 'horizontal') if form else '',
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        content_type='application/javascript')


@require_GET
@login_required
def get_empty_edit_gear_form(request, gear_type):
    form_lookup = {
        'Telescope': TelescopeEditNewForm,
        'Mount': MountEditNewForm,
        'Camera': CameraEditNewForm,
        'FocalReducer': FocalReducerEditNewForm,
        'Software': SoftwareEditNewForm,
        'Filter': FilterEditNewForm,
        'Accessory': AccessoryEditNewForm,
    }

    form = form_lookup[gear_type]()
    from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
    response_dict = {
        'form': as_bootstrap(form, 'horizontal') if form else '',
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        content_type='application/javascript')


@require_POST
@login_required
def save_gear_details(request):
    gear = None
    if 'gear_id' in request.POST:
        id = request.POST.get('gear_id')
        gear, gear_type = get_correct_gear(id)
    else:
        gear_type = request.POST.get('gear_type')

    from astrobin.gear import CLASS_LOOKUP

    form_lookup = {
        'Telescope': TelescopeEditNewForm,
        'Mount': MountEditNewForm,
        'Camera': CameraEditNewForm,
        'FocalReducer': FocalReducerEditNewForm,
        'Software': SoftwareEditNewForm,
        'Filter': FilterEditNewForm,
        'Accessory': AccessoryEditNewForm,
    }

    if gear and gear.get_name() != '':
        form_lookup = {
            'Telescope': TelescopeEditForm,
            'Mount': MountEditForm,
            'Camera': CameraEditForm,
            'FocalReducer': FocalReducerEditForm,
            'Software': SoftwareEditForm,
            'Filter': FilterEditForm,
            'Accessory': AccessoryEditForm,
        }

    user_gear_lookup = {
        'Telescope': 'telescopes',
        'Mount': 'mounts',
        'Camera': 'cameras',
        'FocalReducer': 'focal_reducers',
        'Software': 'software',
        'Filter': 'filters',
        'Accessory': 'accessories',
    }

    name = request.POST.get('name')
    filters = Q(name=name)
    if request.POST.get('make'):
        filters = filters & Q(make=request.POST.get('make'))

    if not gear:
        try:
            if request.POST.get('make'):
                gear, created = CLASS_LOOKUP[gear_type].objects.get_or_create(
                    make=request.POST.get('make'),
                    name=request.POST.get('name'))
            else:
                gear, created = CLASS_LOOKUP[gear_type].objects.get_or_create(
                    name=request.POST.get('name'))
        except CLASS_LOOKUP[gear_type].MultipleObjectsReturned:
            gear = CLASS_LOOKUP[gear_type].objects.filter(filters)[0]

    form = form_lookup[gear_type](data=request.POST, instance=gear)
    if not form.is_valid():
        from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
        response_dict = {
            'form': as_bootstrap(form, 'horizontal') if form else '',
            'gear_id': gear.id,
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            content_type='application/javascript')

    form.save()

    profile = request.user.userprofile
    user_gear = getattr(profile, user_gear_lookup[gear_type])
    if gear not in user_gear.all():
        user_gear.add(gear)

    alias = _("no alias")
    gear_user_info = GearUserInfo(gear=gear, user=request.user)
    if gear_user_info.alias is not None and gear_user_info.alias != '':
        alias = gear_user_info.alias

    response_dict = {
        'success': True,
        'id': gear.id,
        'make': gear.get_make(),
        'name': gear.get_name(),
        'alias': alias,
        'complete': is_gear_complete(gear.id),
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        content_type='application/javascript')


@require_GET
@login_required
@never_cache
def get_is_gear_complete(request, id):
    return HttpResponse(
        simplejson.dumps({'complete': is_gear_complete(id)}),
        content_type='application/javascript')


@require_GET
@login_required
@never_cache
def get_gear_user_info_form(request, id):
    gear = get_object_or_404(Gear, id=id)
    gear_user_info, created = GearUserInfo.objects.get_or_create(
        gear=gear,
        user=request.user,
    )

    form = GearUserInfoForm(instance=gear_user_info)

    from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
    response_dict = {
        'form': as_bootstrap(form, 'horizontal') if form else '',
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        content_type='application/javascript')


@require_POST
@login_required
def save_gear_user_info(request):
    gear = get_object_or_404(Gear, id=request.POST.get('gear_id'))
    gear_user_info, created = GearUserInfo.objects.get_or_create(
        gear=gear,
        user=request.user,
    )

    form = GearUserInfoForm(data=request.POST, instance=gear_user_info)
    if not form.is_valid():
        from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
        response_dict = {
            'form': as_bootstrap(form, 'horizontal') if form else '',
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            content_type='application/javascript')

    form.save()
    return ajax_success()


@require_GET
@never_cache
def gear_popover_ajax(request, id):
    gear, gear_type = get_correct_gear(id)
    template = 'popover/gear.html'

    if gear_type == 'Telescope':
        template = 'popover/gear_telescope.html'
    elif gear_type == 'Mount':
        template = 'popover/gear_mount.html'
    elif gear_type == 'Camera':
        template = 'popover/gear_camera.html'
    elif gear_type == 'FocalReducer':
        template = 'popover/gear_focal_reducer.html'
    elif gear_type == 'Software':
        template = 'popover/gear_software.html'
    elif gear_type == 'Filter':
        template = 'popover/gear_filter.html'
    elif gear_type == 'Accessory':
        template = 'popover/gear_accessory.html'

    html = render_to_string(template,
                            {
                                'request': request,
                                'user': request.user,
                                'gear': gear,
                                'is_authenticated': request.user.is_authenticated(),
                                'IMAGES_URL': settings.IMAGES_URL,
                            })

    response_dict = {
        'success': True,
        'html': html,
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        content_type='application/javascript')


@require_GET
@never_cache
def user_popover_ajax(request, username):
    profile = get_object_or_404(UserProfile, user__username=username)
    template = 'popover/user.html'

    from django.template.defaultfilters import timesince

    date_time = profile.user.date_joined.replace(tzinfo=None)
    span = timesince(date_time)
    span = span.split(",")[0]  # just the most significant digit
    if span == "0 " + _("minutes"):
        member_since = _("seconds ago")
    else:
        member_since = _("%s ago") % span

    html = render_to_string(template,
                            {
                                'user': profile.user,
                                'images': Image.objects.filter(user=profile.user).count(),
                                'member_since': member_since,
                                'is_authenticated': request.user.is_authenticated(),
                                'request': request,
                            })

    response_dict = {
        'success': True,
        'html': html,
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        content_type='application/javascript')


@require_GET
def gear_page(request, id, slug):
    gear, gear_type = get_correct_gear(id)
    if not gear:
        try:
            redirect = GearHardMergeRedirect.objects.get(fro=id)
        except GearHardMergeRedirect.DoesNotExist:
            raise Http404

        gear, gear_type = get_correct_gear(redirect.to)
        if not gear:
            raise Http404
        else:
            return HttpResponseRedirect(gear.get_absolute_url())

    user_attr_lookup = {
        'Telescope': 'telescopes',
        'Camera': 'cameras',
        'Mount': 'mounts',
        'FocalReducer': 'focal_reducers',
        'Software': 'software',
        'Filter': 'filters',
        'Accessory': 'accessories',
    }

    from astrobin.gear import CLASS_LOOKUP

    all_images = Image.by_gear(gear, gear_type).filter(is_wip=False)
    show_commercial = (gear.commercial and gear.commercial.is_paid()) or (
            gear.commercial and gear.commercial.producer == request.user)
    content_type = ContentType.objects.get(app_label='astrobin', model='gear')
    reviews = Review.objects.filter(content_id=id, content_type=content_type)

    response_dict = {
        'gear': gear,
        'examples': all_images[:28],
        'review_form': ReviewAddForm(
            instance=Review(content_type=ContentType.objects.get_for_model(Gear), content=gear)),
        'reviews': reviews,
        'content_type': ContentType.objects.get_for_model(Gear),
        'owners_count': UserProfile.objects.filter(**{user_attr_lookup[gear_type]: gear}).count(),
        'images_count': all_images.count(),
        'attributes': [
            (_(CLASS_LOOKUP[gear_type]._meta.get_field(k[0]).verbose_name),
             getattr(gear, k[0]),
             k[1]) for k in gear.attributes()],

        'show_tagline': show_commercial and gear.commercial.tagline,
        'show_link': show_commercial and gear.commercial.link,
        'show_image': show_commercial and gear.commercial.image,
        'show_other_images': show_commercial and gear.commercial.image and gear.commercial.image.revisions.all(),
        'show_description': show_commercial and gear.commercial.description,
    }

    return render(request, 'gear/page.html', response_dict)


@require_GET
def stats_subject_images_monthly_ajax(request, id):
    import astrobin.stats as _s

    (label, data, options) = _s.subject_images_monthly(id)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_subject_integration_monthly_ajax(request, id):
    import astrobin.stats as _s

    (label, data, options) = _s.subject_integration_monthly(id)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_subject_total_images_ajax(request, id):
    import astrobin.stats as _s

    (label, data, options) = _s.subject_total_images(id)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_subject_camera_types_ajax(request, id):
    import astrobin.stats as _s

    (label, data, options) = _s.subject_camera_types(id, request.LANGUAGE_CODE)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_subject_telescope_types_ajax(request, id):
    import astrobin.stats as _s

    (label, data, options) = _s.subject_telescope_types(id, request.LANGUAGE_CODE)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_camera_types_trend_ajax(request):
    import astrobin.stats as _s

    (data, options) = _s.camera_types_trend()

    response_dict = {
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_telescope_types_trend_ajax(request):
    import astrobin.stats as _s

    (data, options) = _s.telescope_types_trend()

    response_dict = {
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_subject_type_trend_ajax(request):
    import astrobin.stats as _s

    (data, options) = _s.subject_type_trend()

    response_dict = {
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def gear_by_image(request, image_id):
    image = get_object_or_404(Image, pk=image_id)

    attrs = ('imaging_telescopes', 'guiding_telescopes', 'mounts',
             'imaging_cameras', 'guiding_cameras', 'focal_reducers',
             'software', 'filters', 'accessories',)
    response_dict = {}

    for attr in attrs:
        ids = [int(x) for x in getattr(image, attr).all().values_list('id', flat=True)]
        response_dict[attr] = ids

    return HttpResponse(
        simplejson.dumps(response_dict),
        content_type='application/javascript')


@require_GET
def gear_by_make(request, make):
    klass = request.GET.get('klass', Gear)
    unclaimed = request.GET.get('unclaimed', False)

    ret = {
        'make': make,
        'gear': []
    }

    from astrobin.gear import CLASS_LOOKUP

    try:
        autorename = GearMakeAutoRename.objects.get(rename_from=make)
        ret['make'] = autorename.rename_to
    except:
        pass

    if klass != Gear:
        klass = CLASS_LOOKUP[klass]

    gear = klass.objects.filter(make=ret['make']).order_by('name')

    if unclaimed == 'true':
        gear = gear.filter(commercial=None)

    ret['gear'] = [{'id': x.id, 'name': x.get_name()} for x in gear]

    return HttpResponse(
        simplejson.dumps(ret),
        content_type='application/javascript')


@require_GET
def gear_by_ids(request, ids):
    filters = reduce(operator.or_, [Q(**{'id': x}) for x in ids.split(',')])
    gear = [[str(x.id), x.get_make(), x.get_name()] for x in Gear.objects.filter(filters)]
    return HttpResponse(
        simplejson.dumps(gear),
        content_type='application/javascript')


@require_GET
def get_makes_by_type(request, klass):
    ret = {
        'makes': []
    }

    from astrobin.gear import CLASS_LOOKUP
    from astrobin.utils import unique_items

    ret['makes'] = unique_items([x.get_make() for x in CLASS_LOOKUP[klass].objects.exclude(make='').exclude(make=None)])
    return HttpResponse(
        simplejson.dumps(ret),
        content_type='application/javascript')


@require_GET
@login_required
def gear_fix(request, id):
    # Disable this view for now. We're good.
    return HttpResponseForbidden()

    # gear = get_object_or_404(Gear, id=id)
    # form = ModeratorGearFixForm(instance=gear)
    # next_gear = Gear.objects.filter(moderator_fixed=None).order_by('?')[:1].get()
    #
    # return render(request, 'gear/fix.html', {
    #     'form': form,
    #     'gear': gear,
    #     'next_gear': next_gear,
    #     'already_fixed': Gear.objects.exclude(moderator_fixed=None).count(),
    #     'remaining': Gear.objects.filter(moderator_fixed=None).count(),
    # })


@require_POST
@login_required
def gear_fix_save(request):
    # Disable this view for now. We're good.
    return HttpResponseForbidden()

    # id = request.POST.get('gear_id')
    # gear = get_object_or_404(Gear, id=id)
    # form = ModeratorGearFixForm(data=request.POST, instance=gear)
    # next_gear = Gear.objects.filter(moderator_fixed=None).order_by('?')[:1].get()
    #
    # if not form.is_valid():
    #     return render(request, 'gear/fix.html', {
    #         'form': form,
    #         'gear': gear,
    #         'next_gear': next_gear,
    #         'already_fixed': Gear.objects.exclude(moderator_fixed=None).count(),
    #         'remaining': Gear.objects.filter(moderator_fixed=None).count(),
    #     })
    #
    # form.save()
    # return HttpResponseRedirect('/gear/fix/%d/' % next_gear.id)


@require_GET
@login_required
def gear_fix_thanks(request):
    # Disable this view for now. We're good.
    return HttpResponseForbidden()

    return render(request, 'gear/fix_thanks.html')


@require_POST
@login_required
def gear_review_save(request):
    form = ReviewAddForm(data=request.POST)

    if form.is_valid():
        gear, gear_type = get_correct_gear(form.data['gear_id'])
        review = form.save(commit=False)
        review.content_object = gear
        review.user = request.user
        review.save()

        user_attr_lookup = {
            'Telescope': 'telescopes',
            'Camera': 'cameras',
            'Mount': 'mounts',
            'FocalReducer': 'focal_reducers',
            'Software': 'software',
            'Filter': 'filters',
            'Accessory': 'accessories',
        }

        url = '%s/gear/%d#r%d' % (settings.BASE_URL, gear.id, review.id)
        recipients = [x.user for x in UserProfile.objects.filter(
            **{user_attr_lookup[gear_type]: gear})]
        notification = 'new_gear_review'

        push_notification(
            recipients, notification,
            {
                'url': url,
                'user': review.user.userprofile.get_display_name(),
            }
        )

        response_dict = {
            'success': True,
            'score': review.score,
            'content': review.content,
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            content_type='application/javascript')

    return ajax_fail()


@require_POST
@login_required
@user_passes_test(lambda u: user_is_producer(u))
def commercial_products_claim(request, id):
    from astrobin.templatetags.tags import gear_owners, gear_images

    def error(form):
        from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
        response_dict = {
            'form': as_bootstrap(form, 'horizontal') if form else '',
            'success': False,
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            content_type='application/javascript')

    form = ClaimCommercialGearForm(data=request.POST, user=request.user)
    try:
        gear = Gear.objects.get(id=id)
        # Can't claim something that's already claimed:
        if gear.commercial:
            return error(form)
    except Gear.DoesNotExist:
        return error(form)

    # We need to add the choice to the field so that the form will validate.
    # If we don't, it won't validate because the selected option, which was
    # added via AJAX, is not among those available.
    form.fields['name'].choices += [(gear.id, gear.get_name())]
    if request.POST.get('merge_with'):
        merge_with = CommercialGear.objects.get(id=int(request.POST.get('merge_with')))
        proper_name = merge_with.proper_name if merge_with.proper_name else merge_with.gear_set.all()[0].get_name()
        form.fields['merge_with'].choices += [(merge_with.id, proper_name)]

    if not form.is_valid():
        return error(form)

    if form.cleaned_data['merge_with'] != '':
        commercial_gear = CommercialGear.objects.get(id=int(form.cleaned_data['merge_with']))
    else:
        commercial_gear = CommercialGear(
            producer=request.user,
            proper_name=gear.get_name(),
        )
        commercial_gear.save()

    gear.commercial = commercial_gear
    gear.save()

    claimed_gear = Gear.objects.filter(commercial=commercial_gear).values_list('id', flat=True)
    return HttpResponse(
        simplejson.dumps({
            'success': True,
            'id': commercial_gear.id,
            'claimed_gear_id': gear.id,
            'gear_ids': u','.join(str(x) for x in claimed_gear),
            'gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
            'make': gear.get_make(),
            'name': gear.get_name(),
            'owners': gear_owners(gear),
            'images': gear_images(gear),
            'is_merge': form.cleaned_data['merge_with'] != '',
        }),
        content_type='application/javascript')


@require_GET
@login_required
@user_passes_test(lambda u: user_is_producer(u))
def commercial_products_unclaim(request, id):
    try:
        gear = Gear.objects.get(id=id)
    except Gear.DoesNotExist:
        return HttpResponseForbidden()

    commercial = gear.commercial
    commercial_id = commercial.id
    commercial_was_removed = False

    if commercial is None or commercial.producer != request.user:
        return HttpResponseForbidden()

    all_gear = Gear.objects.filter(commercial=commercial)
    if all_gear.count() == 1:
        commercial.delete()
        commercial_was_removed = True

    gear.commercial = None
    gear.save()

    if commercial_was_removed:
        claimed_gear = []
    else:
        claimed_gear = Gear.objects.filter(commercial=commercial).values_list('id', flat=True)

    return HttpResponse(
        simplejson.dumps({
            'success': True,
            'gear_id': id,
            'commercial_id': commercial_id,
            'commercial_was_removed': commercial_was_removed,
            'claimed_gear_ids': u','.join(str(x) for x in claimed_gear),
            'claimed_gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
        }),
        content_type='application/javascript')


@require_GET
@login_required
@user_passes_test(lambda u: user_is_producer(u))
def commercial_products_merge(request, from_id, to_id):
    if from_id != to_id:
        try:
            from_cg = CommercialGear.objects.get(id=int(from_id))
            to_cg = CommercialGear.objects.get(id=int(to_id))
        except CommercialGear.DoesNotExist:
            return HttpResponseForbidden()

        if from_cg.producer != request.user or to_cg.producer != request.user:
            return HttpResponseForbidden()

        Gear.objects.filter(commercial=from_cg).update(commercial=to_cg)
        from_cg.delete()

        claimed_gear = Gear.objects.filter(commercial=to_cg).values_list('id', flat=True)

        return HttpResponse(
            simplejson.dumps({
                'success': True,
                'claimed_gear_ids': u','.join(str(x) for x in claimed_gear),
                'claimed_gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
            }),
            content_type='application/javascript')

    return HttpResponse(
        simplejson.dumps({
            'success': False,
            'message': _("You can't merge a product to itself."),
        }),
        content_type='application/javascript')


@require_GET
@login_required
@user_passes_test(lambda u: user_is_producer(u))
def commercial_products_edit(request, id):
    product = get_object_or_404(CommercialGear, id=id)
    if product.producer != request.user:
        return HttpResponseForbidden()

    form = CommercialGearForm(instance=product, user=request.user)

    return render(request, 'commercial/products/edit.html', {
        'form': form,
        'product': product,
        'gear': Gear.objects.filter(commercial=product)[0],
    })


@require_POST
@login_required
@user_passes_test(lambda u: user_is_producer(u))
def commercial_products_save(request, id):
    product = get_object_or_404(CommercialGear, id=id)
    if product.producer != request.user:
        return HttpResponseForbidden()

    form = CommercialGearForm(
        data=request.POST,
        instance=product,
        user=request.user)

    if form.is_valid():
        form.save()
        messages.success(request, _("Form saved. Thank you!"))
        return HttpResponseRedirect('/commercial/products/edit/%i/' % product.id)

    return render(request, 'commercial/products/edit.html', {
        'form': form,
        'product': product,
        'gear': Gear.objects.filter(commercial=product)[0],
    })


@require_POST
@login_required
@user_passes_test(lambda u: user_is_retailer(u))
def retailed_products_claim(request, id):
    from astrobin.templatetags.tags import gear_owners, gear_images

    def error(form):
        from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
        response_dict = {
            'form': as_bootstrap(form, 'horizontal') if form else '',
            'success': False,
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            content_type='application/javascript')

    form = ClaimRetailedGearForm(data=request.POST, user=request.user)
    try:
        gear = Gear.objects.get(id=id)
        # Here, instead, we can claim something that's already claimed!
    except Gear.DoesNotExist:
        return error(form)

    # We need to add the choice to the field so that the form will validate.
    # If we don't, it won't validate because the selected option, which was
    # added via AJAX, is not among those available.
    form.fields['name'].choices += [(gear.id, gear.get_name())]
    if request.POST.get('merge_with'):
        merge_with = RetailedGear.objects.get(id=int(request.POST.get('merge_with')))
        proper_name = merge_with.gear_set.all()[0].get_name()
        form.fields['merge_with'].choices += [(merge_with.id, proper_name)]

    if not form.is_valid():
        return error(form)

    if form.cleaned_data['merge_with'] != '':
        retailed_gear = RetailedGear.objects.get(id=int(form.cleaned_data['merge_with']))
    else:
        retailed_gear = RetailedGear(
            retailer=request.user,
        )
        retailed_gear.save()

    gear.retailed.add(retailed_gear)
    gear.save()

    claimed_gear = Gear.objects.filter(retailed=retailed_gear).values_list('id', flat=True)
    return HttpResponse(
        simplejson.dumps({
            'success': True,
            'id': retailed_gear.id,
            'claimed_gear_id': gear.id,
            'gear_ids': u','.join(str(x) for x in claimed_gear),
            'gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
            'make': gear.get_make(),
            'name': gear.get_name(),
            'owners': gear_owners(gear),
            'images': gear_images(gear),
            'is_merge': form.cleaned_data['merge_with'] != '',
        }),
        content_type='application/javascript')


@require_GET
@login_required
@user_passes_test(lambda u: user_is_retailer(u))
def retailed_products_unclaim(request, id):
    try:
        gear = Gear.objects.get(id=id)
    except Gear.DoesNotExist:
        return HttpResponseForbidden()

    try:
        retailed = RetailedGear.objects.get(retailer=request.user, gear=gear)
    except RetailedGear.DoesNotExist:
        return HttpResponseForbidden()

    retailed_id = retailed.id
    retailed_was_removed = False

    if retailed is None or retailed.retailer != request.user:
        return HttpResponseForbidden()

    all_gear = Gear.objects.filter(retailed=retailed)
    if all_gear.count() == 1:
        retailed.delete()
        retailed_was_removed = True

    gear.retailed.remove(retailed)

    if retailed_was_removed:
        claimed_gear = []
    else:
        claimed_gear = Gear.objects.filter(retailed=retailed).values_list('id', flat=True)

    return HttpResponse(
        simplejson.dumps({
            'success': True,
            'gear_id': id,
            'retailed_id': retailed_id,
            'retailed_was_removed': retailed_was_removed,
            'claimed_gear_ids': u','.join(str(x) for x in claimed_gear),
            'claimed_gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
        }),
        content_type='application/javascript')


@require_GET
@login_required
@user_passes_test(lambda u: user_is_retailer(u))
def retailed_products_merge(request, from_id, to_id):
    if from_id != to_id:
        try:
            from_rg = RetailedGear.objects.get(id=int(from_id))
            to_rg = RetailedGear.objects.get(id=int(to_id))
        except RetailedGear.DoesNotExist:
            return HttpResponseForbidden()

        if from_rg.retailer != request.user or to_rg.retailer != request.user:
            return HttpResponseForbidden()

        all_gear = Gear.objects.filter(retailed=from_rg)
        for g in all_gear:
            g.retailed.add(to_rg)

        from_rg.delete()

        claimed_gear = Gear.objects.filter(retailed=to_rg).values_list('id', flat=True)

        return HttpResponse(
            simplejson.dumps({
                'success': True,
                'claimed_gear_ids': u','.join(str(x) for x in claimed_gear),
                'claimed_gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
            }),
            content_type='application/javascript')

    return HttpResponse(
        simplejson.dumps({
            'success': False,
            'message': _("You can't merge a product to itself."),
        }),
        content_type='application/javascript')


@login_required
@user_passes_test(lambda u: user_is_retailer(u))
def retailed_products_edit(request, id):
    product = get_object_or_404(RetailedGear, id=id)
    if product.retailer != request.user:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = RetailedGearForm(data=request.POST, instance=product)

        if form.is_valid():
            form.save()
            messages.success(request, _("Form saved. Thank you!"))
            return HttpResponseRedirect('/commercial/products/retailed/edit/%i/' % product.id)
    else:
        form = RetailedGearForm(instance=product)

    return render(request, 'commercial/products/retailed/edit.html', {
        'form': form,
        'product': product,
        'gear': Gear.objects.filter(retailed=product)[0],
    })
