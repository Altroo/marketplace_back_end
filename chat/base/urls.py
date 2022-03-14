from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BaseMessageModelViewSet, BaseChatUserModelViewSet

app_name = 'chat'

router = DefaultRouter()
# POST : send message
# params : recipient(pk), body
router.register(r'message', BaseMessageModelViewSet, basename='message-api')
router.register(r'conversations', BaseChatUserModelViewSet, basename='conversation-api')


urlpatterns = [
    path('', include(router.urls)),
]
