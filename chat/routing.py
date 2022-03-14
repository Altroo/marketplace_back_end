from . import consumers
from django.urls import path

websocket_urlpatterns = [
    path('chatws', consumers.ChatConsumer.as_asgi()),
]
