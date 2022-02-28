from django.urls import path

from .views import CountriesListView, CitiesListView

app_name = 'places'

urlpatterns = [
    path('countries/', CountriesListView.as_view()),
    path('cities/', CitiesListView.as_view()),
]
