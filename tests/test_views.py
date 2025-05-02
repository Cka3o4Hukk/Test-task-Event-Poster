from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Booking, Event, Rating


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        password='testpassword',
    )


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin',
        password='adminpassword',
        email='admin@example.com',
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
def past_event(user):
    return Event.objects.create(
        title='Past Event',
        description='Past description',
        start_time=timezone.now() - timedelta(days=1),
        location='Test City',
        seats=50,
        status='completed',
        organizer=user,
    )


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_event_list(client, event, past_event):
    client.login(username='testuser', password='testpassword')
    response = client.get('/api/events/')
    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert len(data) == 2
    assert data[0]['id'] == event.id
    assert data[1]['id'] == past_event.id


@pytest.mark.django_db
def test_create_booking(client, user, event):
    client.login(username='testuser', password='testpassword')
    url = '/api/bookings/'
    data = {'event': event.id}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert Booking.objects.filter(user=user, event=event).exists()


@pytest.mark.django_db
def test_cancel_booking(client, user, event):
    booking = Booking.objects.create(user=user, event=event)
    client.login(username='testuser', password='testpassword')
    url = f'/api/bookings/{booking.id}/'
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Booking.objects.filter(id=booking.id).exists()


@pytest.mark.django_db
def test_create_rating(client, user, past_event):
    Booking.objects.create(user=user, event=past_event)
    client.login(username='testuser', password='testpassword')
    url = '/api/ratings/'
    data = {'event': past_event.id, 'score': 4}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert Rating.objects.filter(user=user, event=past_event, score=4).exists()


@pytest.mark.django_db
def test_rating_rejected_for_planned_event(client, user, event):
    client.login(username='testuser', password='testpassword')
    url = '/api/ratings/'
    data = {'event': event.id, 'score': 4}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'Можно оценивать только завершенные события' in str(response.data)


@pytest.mark.django_db
def test_rating_rejected_for_non_participant(client, user, past_event):
    client.login(username='testuser', password='testpassword')
    url = '/api/ratings/'
    data = {'event': past_event.id, 'score': 4}
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'Можно оценивать только свои посещенные события' in str(
        response.data)


@pytest.mark.django_db
def test_event_list_sorted_by_rating(client, user, past_event):
    client.login(username='testuser', password='testpassword')
    Booking.objects.create(user=user, event=past_event)
    Rating.objects.create(user=user, event=past_event, score=5)
    response = client.get('/api/events/?ordering=-avg_rating')
    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert len(data) >= 1
    assert data[0]['id'] == past_event.id
