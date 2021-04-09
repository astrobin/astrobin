from django.conf import settings
from rest_framework import pagination


class QueuePagination(pagination.PageNumberPagination):
    page_size = settings.IOTD_QUEUES_PAGE_SIZE
