from django_filters import CharFilter, FilterSet
from persistent_messages.models import Message


class NotificationFilter(FilterSet):
    context_search = CharFilter(method='search_context')
    message = CharFilter(lookup_expr='icontains')

    def search_context(self, queryset, name, value):
        return queryset.filter(extra_tags__contains=f'"context": "{value}"')

    class Meta:
        model = Message
        fields = ('read', 'context_search', 'message',)
