from datetime import timedelta

from annoying.functions import get_object_or_None
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from common.models import AbuseReport, ABUSE_REPORT_DECISION_CONFIRMED, ABUSE_REPORT_DECISION_OVERRULED
from .models import NestedComment
from .permissions import IsOwnerOrReadOnly
from .serializers import NestedCommentSerializer
from .services import CommentNotificationsService


class NestedCommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that represents a list of nested comments.
    """
    model = NestedComment
    queryset = NestedComment.objects.order_by('pk')
    serializer_class = NestedCommentSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('content_type', 'object_id',)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.deleted and self.request.POST.get('deleted') == 'False':
            if AbuseReport.objects.filter(
                    content_type=ContentType.objects.get_for_model(NestedComment),
                    object_id=comment.pk,
            ).exclude(
                decision=ABUSE_REPORT_DECISION_CONFIRMED
            ).exists():
                raise ValidationError(
                    _('You cannot undeleted this comment: a confirmed or pending abuse reports exists for it. '
                      'If you believe that your comment was reported unfairly please contact us.')
                )

        return super(NestedCommentViewSet, self).update(request, args, kwargs)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk):
        comment = get_object_or_404(self.get_queryset(), pk=pk)  # type: NestedComment
        content_type = comment.content_type

        if not comment.pending_moderation:
            raise ValidationError('Comment already moderated')

        try:
            target = content_type.get_object_for_this_type(pk=comment.object_id)
        except content_type.model_class().DoesNotExist:
            raise Http404

        if content_type.model == 'image':
            user = target.user
            if request.user != user:
                raise PermissionDenied()
        else:
            raise ValidationError('Unsupported content object model')

        CommentNotificationsService.approve_comments(
            self.get_queryset().filter(pk=pk),
            request.user
        )

        return Response(status=200)

    @action(detail=True, methods=['post'], url_path='report-abuse')
    def report_abuse(self, request, pk):
        comment = get_object_or_404(self.get_queryset(), pk=pk)  # type: NestedComment
        content_type = ContentType.objects.get_for_model(NestedComment)

        if AbuseReport.objects.filter(
                user=request.user,
                created__gt=timezone.now() - timedelta(hours=24)
        ).count() >= 5:
            raise ValidationError(_('You have reached your abuse report quota.'))

        if AbuseReport.objects.filter(
                content_type=content_type,
                object_id=pk,
                created__gt=comment.updated,
                decision=ABUSE_REPORT_DECISION_OVERRULED
        ):
            raise ValidationError(_('This item cannot be reported again because it was approved by a moderator.'))

        if get_object_or_None(
                AbuseReport,
                user=request.user,
                content_type=content_type,
                object_id=pk,
                created__gt=comment.updated
        ):
            raise ValidationError(
                _('You many not report the same item more than once.')
            )

        self.get_queryset().filter(pk=pk).update(
            pending_moderation=False,
            deleted=True,
            moderator=request.user,
        )

        AbuseReport.objects.create(
            content_type=content_type,
            object_id=pk,
            content_owner=comment.author,
            user=request.user,
            reason=request.POST.get('reason'),
            additional_information=request.POST.get('additional_information'),
        )

        return Response(status=200)
