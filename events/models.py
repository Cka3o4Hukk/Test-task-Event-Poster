from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Event(models.Model):
    STATUS_CHOICES = (
        ('planned', 'Ожидается'),
        ('canceled', 'Отменено'),
        ('completed', 'Завершено'),
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    location = models.CharField(max_length=100)
    seats = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='planned'
    )
    organizer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='organized_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField('Tag', related_name='events', blank=True)

    def can_book(self):
        """Проверка, можно ли забронировать место на событие."""
        time_left = self.start_time - timezone.now()
        return time_left > timedelta(minutes=30)

    def __str__(self):
        return self.title


class Booking(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Notification(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"


class Rating(models.Model):
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='ratings'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='ratings'
    )
    score = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user') 

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.score})"