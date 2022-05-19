from django.urls import path
from .views import GetVersionView

app_name = 'version'

urlpatterns = [
    # GET : Return the current VERSION
    path('', GetVersionView.as_view()),
]
