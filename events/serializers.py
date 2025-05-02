import logging
from typing import Any, Dict

from django.contrib.auth.models import User
from rest_framework import serializers

from events.models import Booking, Event, Notification, Rating, Tag

logger = logging.getLogger(__name__)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')


class EventSerializer(serializers.ModelSerializer):
    organizer = serializers.ReadOnlyField(source='organizer.username')
    organizer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='organizer',
        write_only=True,
        required=False)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source='tags',
        write_only=True,
        required=False)

    class Meta:
        model = Event
        fields = (
            'id', 'title', 'description', 'start_time', 'location', 'seats',
            'status', 'organizer', 'organizer_id', 'created_at', 'tags',
            'tag_ids')
        read_only_fields = ('id', 'created_at', 'organizer')

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"Validated data: {data}")
        return super().validate(data)

    def create(self, validated_data: Dict[str, Any]) -> Event:
        validated_data['organizer'] = self.context['request'].user
        event = Event.objects.create(**validated_data)
        return event

    def update(self, instance: Event, validated_data: Dict[str, Any]) -> Event:
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)
        return instance


class BookingSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        model = Booking
        fields = ('id', 'user', 'event', 'created_at')
        read_only_fields = ('id', 'created_at', 'user')


class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Notification
        fields = ('id', 'user', 'event', 'message', 'created_at')
        read_only_fields = ('id', 'created_at', 'user', 'event', 'message')


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ('id', 'event', 'user', 'score', 'created_at')
        read_only_fields = ('user', 'created_at')
