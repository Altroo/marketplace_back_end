import os
# # Avoid daphne apps not loaded yet
# import django
# django.setup()
from django.core.asgi import get_asgi_application
from chat.jwt_middleware import SimpleJwtTokenAuthMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import websocket_urlpatterns
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Qaryb_API.settings")
#
# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": SimpleJwtTokenAuthMiddleware(
#         URLRouter(
#             websocket_urlpatterns
#         )
#     ),
# })

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Qaryb_API.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": SimpleJwtTokenAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
