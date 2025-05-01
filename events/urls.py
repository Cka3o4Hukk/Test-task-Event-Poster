from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EventViewSet, BookingViewSet, NotificationViewSet, RatingViewSet


router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'ratings', RatingViewSet, basename='rating')

urlpatterns = [
    path('', include(router.urls)),
]
