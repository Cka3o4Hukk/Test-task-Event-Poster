from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets

from events.api.filters.filters import EventFilter
from events.api.serializers import EventSerializer
from events.domain.repositories.event import EventRepository


class EventViewSet(viewsets.ModelViewSet):
    """Управление событиями (только CRUD операции)."""
    queryset = EventRepository.get_annotated_events()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_destroy(self, instance):
        """Удаление события с валидацией."""
        from events.domain.services.event import EventService
        EventService.validate_organizer(self.request.user, instance)
        EventService.validate_deletion_time(instance)
        super().perform_destroy(instance)
