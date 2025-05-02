from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.db.models import Avg, Count, F
from django.utils import timezone

from events.models import Booking, Event, Rating


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


@pytest.fixture
def booked_event(user):
    event = Event.objects.create(
        title='Booked Event',
        description='Booked description',
        start_time=timezone.now() + timedelta(days=1),
        location='Test City',
        seats=2,
        status='planned',
        organizer=user,
    )
    Booking.objects.create(user=user, event=event)
    return event


@pytest.fixture
def rated_event(user):
    event = Event.objects.create(
        title='Rated Event',
        description='Rated description',
        start_time=timezone.now() - timedelta(days=1),
        location='Test City',
        seats=50,
        status='completed',
        organizer=user,
    )
    Booking.objects.create(user=user, event=event)
    Rating.objects.create(user=user, event=event, score=4)
    return event


@pytest.mark.django_db
def test_event_filter_by_location(event):
    events = Event.objects.filter(location='Test City')
    assert len(events) > 0
    assert event in events


@pytest.mark.django_db
def test_event_filter_by_date(event):
    events = Event.objects.filter(start_time__gte=timezone.now())
    assert len(events) > 0
    assert event in events


@pytest.mark.django_db
def test_event_filter_by_status(event):
    events = Event.objects.filter(status='planned')
    assert len(events) > 0
    assert event in events


@pytest.mark.django_db
def test_event_filter_by_free_seats(event):
    events = Event.objects.annotate(booked=Count('bookings')).filter(
        booked__lt=F('seats'))
    assert len(events) > 0
    assert event in events


@pytest.mark.django_db
def test_event_filter_by_booked_seats(booked_event):
    events = Event.objects.annotate(booked=Count('bookings')).filter(
        booked__gte=F('seats'))
    assert len(events) == 0
    events = Event.objects.annotate(booked=Count('bookings')).filter(
        booked__lt=F('seats'))
    assert booked_event in events


@pytest.mark.django_db
def test_event_filter_by_rating(rated_event, user):
    events = Event.objects.annotate(avg_rating=Avg('ratings__score')).filter(
        avg_rating__gte=3)
    assert len(events) > 0
    assert rated_event in events
