from datetime import timedelta

from django.utils import timezone
from rest_framework import status

from events.mixins import ErrorHandlingMixin


class EventService(ErrorHandlingMixin):
    def deny_if_not_organizer(self, request, event):
        """Проверка, является ли пользователь организатором события."""
        if event.organizer != request.user:
            return self.create_error_response(
                "Доступно только организатору.",
                status.HTTP_403_FORBIDDEN)
        return None

    def deny_if_too_late_to_delete(self, event):
        """Проверка, не слишком ли поздно для удаления события."""
        if timezone.now() - event.created_at > timedelta(hours=1):
            return self.create_error_response(
                "Удаление доступно только в течение 1 часа после создания.",
                status.HTTP_400_BAD_REQUEST)
        return None

    def deny_delete(self, request, event):
        """Проверки для удаления события."""
        return (
            self.deny_if_not_organizer(request, event)
            or self.deny_if_too_late_to_delete(event)
        )
