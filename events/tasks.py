from celery import shared_task
from django.utils import timezone
from .models import Event, Notification, Booking
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

@shared_task
def notify_user(user_id, event_id, message):
    print(f"[STARTING TASK] Notify user {user_id} for event {event_id}")
    try:
        user = User.objects.get(pk=user_id)
        event = Event.objects.get(pk=event_id)
        Notification.objects.create(user=user, event=event, message=message)
        print(f"[NOTIFY] {user.username}: {message}")
    except ObjectDoesNotExist as e:
        print(f"[ERROR] Object not found: {e}")
        return

@shared_task
def complete_old_events():
    now = timezone.now()
    outdated_events = Event.objects.filter(
        status='planned',
        start_time__lt=now - timezone.timedelta(hours=2)
    )
    if outdated_events.exists():
        for event in outdated_events:
            event.status = 'completed'
            event.save()
        print(f"[COMPLETE EVENTS] {len(outdated_events)} events marked as completed.")
    else:
        print("[COMPLETE EVENTS] No outdated events found.")
