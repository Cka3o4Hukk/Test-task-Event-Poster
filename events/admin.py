from django.contrib import admin

from events.models import Booking, Event, Notification

admin.site.register(Event)
admin.site.register(Booking)
admin.site.register(Notification)
