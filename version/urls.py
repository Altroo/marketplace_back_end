from django.urls import path
from .views import GetVersionView, GetAdminVirementData

app_name = 'version'

urlpatterns = [
    # GET : Return the current VERSION
    path('', GetVersionView.as_view()),
    # Get virement data
    path('virement_data/', GetAdminVirementData.as_view()),
]
