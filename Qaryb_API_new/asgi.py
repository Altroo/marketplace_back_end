# # Altroo old
# # import os
# # import django
# # from channels.layers import get_channel_layer
# # from channels.routing import get_default_application
# #
# # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Qaryb_API.settings")
# # django.setup()
# # channel_layer = get_channel_layer()
# # application = get_default_application()
#
# # Altroo new
# import os
# import django
# django.setup()
#
# from django.core.asgi import get_asgi_application
# from chat.auth.jwt_auth_middleware import SimpleJwtTokenAuthMiddleware
# from channels.routing import ProtocolTypeRouter, URLRouter
# from chat.routing import websocket_urlpatterns
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Qaryb_API.settings')
#
# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": SimpleJwtTokenAuthMiddleware(
#         URLRouter(
#             websocket_urlpatterns
#         )
#     ),
# })
