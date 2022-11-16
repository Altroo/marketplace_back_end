from django.urls import path
from .views import NotificationView

app_name = 'notifications'

urlpatterns = [
    path('', NotificationView.as_view()),
]
