from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/search_progress/', consumers.SearchProgressConsumer.as_asgi()),
]
