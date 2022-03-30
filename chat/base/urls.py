from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BaseMessageModelViewSet, BaseChatUserModelViewSet, BaseArchiveConversationView

app_name = 'chat'

router = DefaultRouter()
# POST : send message
# params : recipient(pk), body
# PATCH : / <int:user_pk>
# params : viewed = True
router.register(r'message', BaseMessageModelViewSet, basename='message-api')
router.register(r'conversations', BaseChatUserModelViewSet, basename='conversation-api')


urlpatterns = [
    path('', include(router.urls)),
    path('archive/', BaseArchiveConversationView.as_view()),
]
