from django.db.models import Avg, Count, Case, When, Value, IntegerField, Q
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers

from .filters import EventFilter
from .mixins import ErrorHandlingMixin
from .models import Event, Booking, Notification, Rating
from .serializers import EventSerializer, BookingSerializer, NotificationSerializer, RatingSerializer
from .services import EventService
from .tasks import notify_user


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFilter

    def get_event_service(self):
        return EventService()

    def get_queryset(self):
        """Возвращает отсортированный queryset событий с аннотацией."""
        now = timezone.now()
        queryset = Event.objects.annotate(
            avg_rating=Avg('ratings__score'),
            booked=Count('bookings'),
            sort_order=Case(
                When(status='planned', start_time__gte=now, then=Value(1)),
                When(~Q(status='planned'), then=Value(2)),
                default=Value(3),
                output_field=IntegerField()
            )
        ).order_by('sort_order', 'start_time')
        return queryset

    def destroy(self, request, *args, **kwargs):
        """Удаляет событие с проверкой прав и времени."""
        event = self.get_object()
        event_service = self.get_event_service()
        error = event_service.deny_delete(request, event)
        if error:
            return error
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_status(self, request, pk=None):
        """Обновляет статус события, доступно только организатору."""
        event = self.get_object()
        new_status = request.data.get('status')
        event_service = self.get_event_service()

        error = event_service.deny_if_not_organizer(request, event)
        if error:
            return error

        if new_status not in dict(Event.STATUS_CHOICES).keys():
            return event_service.create_error_response(
                "Недопустимый статус.",
                status.HTTP_400_BAD_REQUEST
            )

        event.status = new_status
        event.save()
        return Response({"status": event.status}, status=status.HTTP_200_OK)


class RatingViewSet(viewsets.ModelViewSet):
    """Управление оценками событий."""
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Возвращает оценки текущего пользователя."""
        return Rating.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Создает оценку с проверкой прав."""
        event = serializer.validated_data['event']
        if event.status != 'completed':
            raise serializers.ValidationError(
                "Можно оценивать только завершенные события."
            )
        if not Booking.objects.filter(user=self.request.user, event=event).exists():
            raise serializers.ValidationError(
                "Можно оценивать только свои посещенные события."
            )
        serializer.save(user=self.request.user)
    

class BookingViewSet(ErrorHandlingMixin, viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        event = serializer.validated_data['event']

        if Booking.objects.filter(user=self.request.user, event=event).exists():
            return self.create_error_response(
                "Вы уже забронировали место на это мероприятие.",
                status.HTTP_400_BAD_REQUEST
            )

        if not event.can_book():
            return self.create_error_response(
                "Бронирование невозможно, так как до события осталось менее 30 минут.",
                status.HTTP_400_BAD_REQUEST
            )

        booked_seats = Booking.objects.filter(event=event).count()
        if booked_seats >= event.seats:
            return self.create_error_response(
                "Нет доступных мест.",
                status.HTTP_400_BAD_REQUEST
            )

        booking = serializer.save(user=self.request.user)

        # Уведомление после создания брони
        notify_user.delay(
            booking.user.id,
            booking.event.id,
            f"Вы забронировали мероприятие: {booking.event.title}"
        )

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def cancel_booking(self, request, pk=None):
        booking = self.get_object()
        event = booking.event

        if booking.user != request.user:
            return self.create_error_response(
                "Вы не можете отменить бронирование другого пользователя.",
                status.HTTP_403_FORBIDDEN
            )

        # Уведомление перед удалением брони
        print(f"Booking {booking.id} deleted, notifying user {booking.user.id}")
        notify_user.delay(
            booking.user.id,
            booking.event.id,
            f"Вы отменили бронирование для мероприятия: {booking.event.title}"
        )

        booking.delete()
        return Response({"detail": "Бронирование успешно отменено."}, status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)