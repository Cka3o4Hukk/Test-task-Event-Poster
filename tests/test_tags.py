from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Event, Tag


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        password='testpassword',
    )


@pytest.fixture
def tag_concert():
    return Tag.objects.create(name='concert')


@pytest.fixture
def tag_exhibition():
    return Tag.objects.create(name='exhibition')


@pytest.fixture
def event_with_tags(user, tag_concert, tag_exhibition):
    event = Event.objects.create(
        title='Tagged Event',
        description='Event with tags',
        start_time=timezone.now() + timedelta(days=1),
        location='Test City',
        seats=100,
        status='planned',
        organizer=user,
    )
    event.tags.add(tag_concert, tag_exhibition)
    return event


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_filter_events_by_tags(client, event_with_tags,
                               tag_concert, tag_exhibition):
    client.login(username='testuser', password='testpassword')
    response = client.get(
        f'/api/events/?tags={tag_concert.id}&tags={tag_exhibition.id}')
    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert len(data) == 1
    assert data[0]['id'] == event_with_tags.id


@pytest.mark.django_db
def test_create_event_with_tags(client, user, tag_concert, tag_exhibition):
    client.login(username='testuser', password='testpassword')
    url = '/api/events/'
    data = {
        'title': 'New Event',
        'description': 'Event description',
        'start_time': (timezone.now() + timedelta(days=2)).isoformat(),
        'location': 'Test City',
        'seats': 50,
        'status': 'planned',
        'organizer_id': user.id,
        'tag_ids': [tag_concert.id, tag_exhibition.id],
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    event = Event.objects.get(id=response.data['id'])
    assert set(event.tags.values_list('id', flat=True)) == {
        tag_concert.id, tag_exhibition.id}


@pytest.mark.django_db
def test_update_event_tags(client, event_with_tags, tag_concert):
    client.login(username='testuser', password='testpassword')
    url = f'/api/events/{event_with_tags.id}/'
    data = {
        'title': event_with_tags.title,
        'description': event_with_tags.description,
        'start_time': event_with_tags.start_time.isoformat(),
        'location': event_with_tags.location,
        'seats': event_with_tags.seats,
        'status': event_with_tags.status,
        'tag_ids': [tag_concert.id],
    }
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    event = Event.objects.get(id=event_with_tags.id)
    assert set(event.tags.values_list('id', flat=True)) == {tag_concert.id}
