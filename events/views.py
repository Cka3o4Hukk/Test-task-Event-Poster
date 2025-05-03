from django.core.exceptions import PermissionDenied
from django.db.models.query import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from events.filters.filters import EventFilter
from events.mixins.error_handling import ErrorHandlingMixin
from events.models import Booking, Event, Notification, Rating
from events.repositories.booking import BookingRepository
from events.repositories.event import EventRepository
from events.repositories.rating import RatingRepository
from events.serializers import (
    BookingSerializer,
    EventSerializer,
    NotificationSerializer,
    RatingSerializer,
)
from events.services.booking import BookingService
from events.services.event import EventService
from events.services.rating import RatingService


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFilter

    def get_queryset(self) -> QuerySet[Event]:
        return EventRepository.get_annotated_events()

    def destroy(self, request, *args, **kwargs) -> Response:
        """Удаляет событие с валидацией."""
        event = self.get_object()
        try:
            EventService.validate_organizer(request.user, event)
            EventService.validate_deletion_time(event)
            EventRepository.delete_event(event)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (PermissionDenied, ValidationError) as e:
            return self.create_error_response(
                str(e), status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['patch'],
            permission_classes=[permissions.IsAuthenticated])
    def update_status(self, request, pk=None) -> Response:
        """Обновляет статус события."""
        event = self.get_object()
        new_status = request.data.get('status')

        try:
            updated_event = EventService.update_event_status(
                event=event,
                user=request.user,
                new_status=new_status)
            return Response(
                {"status": updated_event.status},
                status=status.HTTP_200_OK)

        except (PermissionDenied, ValidationError) as e:
            return self.create_error_response(
                str(e), status.HTTP_400_BAD_REQUEST)


class RatingViewSet(viewsets.ModelViewSet):
    """Управление оценками событий."""
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self) -> QuerySet[Rating]:
        """Возвращает оценки текущего пользователя."""
        return RatingRepository.get_user_ratings(self.request.user)

    def perform_create(self, serializer: RatingSerializer) -> None:
        """Создает оценку с валидацией через сервис."""
        event = serializer.validated_data['event']
        score = serializer.validated_data['score']

        try:
            RatingService.validate_rating(self.request.user, event)
            RatingRepository.create_rating(
                user=self.request.user,
                event=event,
                score=score)
        except ValidationError as e:
            raise serializers.ValidationError(e.detail) from e


class BookingViewSet(ErrorHandlingMixin, viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self) -> QuerySet[Booking]:
        """Возвращает бронирования текущего пользователя."""
        return BookingRepository.get_user_bookings(self.request.user)

    def perform_create(self, serializer: BookingSerializer) -> None:
        """Создает бронирование через сервис."""
        try:
            event = serializer.validated_data['event']
            BookingService.create_booking(self.request.user, event)
        except ValidationError as e:
            raise serializers.ValidationError(e.detail) from e


    @action(detail=True, methods=['delete'])
    def cancel_booking(self, request, pk=None) -> Response:
        """Отменяет бронирование."""
        booking = self.get_object()

        if booking.user != request.user:
            return self.create_error_response(
                "Нельзя отменить чужое бронирование.",
                status.HTTP_403_FORBIDDEN            )

        try:
            BookingService.cancel_booking(booking)
            return Response(
                {"detail": "Бронирование отменено."},
                status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return self.create_error_response(
                str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self) -> QuerySet[Notification]:
        return Notification.objects.filter(user=self.request.user)
