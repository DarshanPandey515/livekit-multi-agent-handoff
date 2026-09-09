from django.urls import path

from .views import get_token, list_rooms

urlpatterns = [
    path("token", get_token),
    path("rooms", list_rooms),
]