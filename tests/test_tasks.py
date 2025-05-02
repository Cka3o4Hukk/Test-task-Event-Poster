from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from events.models import Event, Notification, User
from events.tasks import complete_old_events, notify_user


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        password='testpassword',
    )


@pytest.fixture
def event(user):
    return Event.objects.create(
        title='Test Event',
        description='Test description',
        start_time=timezone.now() + timedelta(days=1),
        location='Test City',
        seats=100,
        status='planned',
        organizer=user,
    )


@pytest.mark.django_db
def test_notify_user(user, event):
    notify_user(user.id, event.id, 'Test message')

    notification = Notification.objects.get(user=user, event=event)
    assert notification.message == 'Test message'
    assert notification.user.username == 'testuser'
    assert notification.event.title == 'Test Event'


@pytest.mark.django_db
def test_complete_old_events(event):
    event.start_time = timezone.now() - timedelta(hours=3)
    event.save()

    with patch('events.tasks.complete_old_events'):
        complete_old_events()
        event.refresh_from_db()
        assert event.status == 'completed'
