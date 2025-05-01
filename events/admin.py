from django.contrib import admin

from .models import Event, Booking, Notification


admin.site.register(Event)
admin.site.register(Booking)
admin.site.register(Notification)