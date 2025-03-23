import hashlib
import os
import re

import simplejson
from avatar.utils import get_default_avatar_url
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import TrigramDistance
from django.db.models import Q, QuerySet
from django.db.models.functions import Concat, Lower
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from pybb.models import Post
from rest_framework.authtoken.models import Token

from astrobin.models import Image, UserProfile
from astrobin_apps_images.services import ImageService
from astrobin_apps_users.services import UserService
from nested_comments.models import NestedComment


@login_required
@require_GET
def autocomplete_private_message_recipients(request):
    if 'q' not in request.GET:
        return HttpResponse(simplejson.dumps([]))

    q = str(request.GET['q']).replace(chr(160), ' ')
    limit = 10
    results = []

    users = list(
        UserProfile.objects.filter(
            Q(user__username__icontains=q) | Q(real_name__icontains=q)
        ).distinct()[:limit]
    )

    for user in users:
        results.append(
            {
                'id': user.user.username,
                'realName': user.user.userprofile.real_name,
                'displayName': user.user.userprofile.real_name if user.user.userprofile.real_name else user.user.username,
            }
        )

    return HttpResponse(simplejson.dumps(results))


@require_GET
def autocomplete_usernames(request):
    if 'q' not in request.GET:
        return HttpResponse(simplejson.dumps([]))

    if request.user.is_anonymous:
        if 'token' not in request.GET:
            return HttpResponse(simplejson.dumps([]))

        try:
            Token.objects.get(key=request.GET.get('token'))
        except Token.DoesNotExist:
            return HttpResponse(simplejson.dumps([]))

    from common.services.caching_service import CachingService, JSON_CACHE
    from django.db.models import Q, Value, F, Case, When, FloatField

    q = request.GET['q']
    limit = 20
    referer_header = request.META.get('HTTP_REFERER', '')
    from_forums = '/forum' in referer_header
    from_image_page = re.match(r'%s\/?([a-zA-Z0-9]{6})\/.*' % settings.BASE_URL, referer_header)
    context_aware_users = UserProfile.objects.none()
    all_users = UserProfile.objects.none()
    ids = []
    results = []

    # Replace non-breaking space with regular space
    q = q.replace(chr(160), ' ')

    if len(q) > 15:
        q = q[:15]

    def filter_by_distance(queryset: QuerySet, q: str) -> QuerySet:
        if 'postgresql' in settings.DATABASES['default']['ENGINE']:
            return queryset.annotate(
                # Create separate fields for name variations
                full_name=Lower(F('real_name')),
                username_lower=Lower(F('user__username')),
                combined_name=Lower(Concat('real_name', Value(' '), 'user__username'))
            ).annotate(
                # Add direct match indicators with priority
                exact_match=Case(
                    When(real_name__iexact=q, then=Value(0.0)),
                    default=Value(1.0),
                    output_field=FloatField()
                ),
                # Use multiple distance metrics for better matching
                name_distance=TrigramDistance('full_name', q.lower()),
                combined_distance=TrigramDistance('combined_name', q.lower())
            ).filter(
                # Keep the original filter conditions
                Q(name_distance__lte=0.7) |
                Q(combined_distance__lte=0.7) |
                Q(user__username__icontains=q) |
                Q(real_name__icontains=q)
            ).order_by(
                # Order by exact match first, then by distances
                'exact_match',
                'name_distance',
                'combined_distance'
            )
        else:
            return queryset.annotate(
                name=Lower(Concat('real_name', Value(' '), 'user__username'))
            ).filter(
                name__icontains=q
            )

    query_hash = hashlib.md5(q.encode('utf-8')).hexdigest()
    cache_key = f'astrobin_autocomplete_usernames_{query_hash}_{from_forums}_{from_image_page}'
    cache_value = CachingService.get(cache_key, cache_name=JSON_CACHE)

    if cache_value is not None:
        return HttpResponse(cache_value)

    if from_forums:
        if '?' in referer_header:
            slug = os.path.basename(os.path.normpath(referer_header.rsplit('/', 1)[0]))
        else:
            slug = os.path.basename(os.path.normpath(referer_header))
        posters = Post.objects.filter(topic__slug=slug).only('poster').values_list('user', flat=True).distinct()
        ids = list(posters)
        context_aware_users = filter_by_distance(UserProfile.objects.filter(user__id__in=ids), q)[:limit]
        results += list(context_aware_users)
    elif from_image_page:
        image_id = from_image_page.group(1)
        image = ImageService.get_object(image_id, Image.objects_including_wip.all())
        image_ct = ContentType.objects.get_for_model(image)
        image_owner = [image.user.id]
        collaborators = [x.id for x in image.collaborators.all()]
        commenters = list(
            NestedComment.objects.filter(
                object_id=image.id, content_type_id=image_ct.id
            ).only(
                'author'
            ).values_list(
                'author__id', flat=True
            ).distinct()
        )
        ids = image_owner + collaborators + commenters
        context_aware_users = filter_by_distance(UserProfile.objects.filter(user__id__in=ids), q)[:limit]
        results += list(context_aware_users)

    if len(results) < limit:
        all_users = filter_by_distance(UserProfile.objects.exclude(user__id__in=ids), q)[:limit - len(results)]

    context_aware_users = context_aware_users.values_list('user__id', 'user__username', 'real_name')
    all_users = all_users.values_list('user__id', 'user__username', 'real_name')

    ret = []
    for user in list(context_aware_users) + list(all_users):
        user_id = user[0]
        username = user[1]
        real_name = user[2]

        avatar = UserService(User.objects.get(id=user_id)).get_primary_avatar(64)
        if avatar is None:
            avatar_url = get_default_avatar_url()
        else:
            avatar_url = avatar.get_absolute_url()

        ret.append(
            {
                'id': str(user_id),
                'username': username,
                'realName': real_name,
                'displayName': real_name if real_name else username,
                'avatar': avatar_url,
            }
        )

    cache_value = simplejson.dumps(ret)
    CachingService.set(cache_key, cache_value, 600, cache_name=JSON_CACHE)

    return HttpResponse(cache_value)


@require_GET
def autocomplete_images(request):
    if 'q' not in request.GET:
        HttpResponse(simplejson.dumps([]))

    if request.user.is_anonymous:
        if 'token' not in request.GET:
            return HttpResponse(simplejson.dumps([]))

        try:
            token = Token.objects.get(key=request.GET.get('token'))
            user = token.user
        except Token.DoesNotExist:
            return HttpResponse(simplejson.dumps([]))
    else:
        user = request.user

    q = request.GET['q']

    # Replace non-breaking space with regular space
    q = q.replace(chr(160), ' ')

    images = Image.objects_including_wip.filter(user=user, title__icontains=q)[:10]

    results = []

    for image in images:
        results.append(
            {
                'id': image.get_id(),
                'title': image.title,
                'thumbnail': image.thumbnail('gallery', None, sync=True),
                'url': image.get_absolute_url(),
            }
        )

    return HttpResponse(simplejson.dumps(results))
