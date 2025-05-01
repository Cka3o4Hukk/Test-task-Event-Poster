from datetime import timedelta
import pytest

from django.contrib.auth.models import User
from django.utils import timezone

from events.models import Event, Booking

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='testpassword')

@pytest.fixture
def event(user):
    return Event.objects.create(
        title='Test Event',
        description='Test description',
        start_time=timezone.now() + timedelta(days=1),
        location='Test City',
        seats=100,
        status='planned',
        organizer=user
    )

@pytest.mark.django_db
def test_event_creation(event):
    assert event.title == 'Test Event'
    assert event.status == 'planned'

@pytest.mark.django_db
def test_booking_creation(user, event):
    booking = Booking.objects.create(user=user, event=event)
    assert booking.user == user
    assert booking.event == event
