from django.urls import path

from .views import CountriesListView, CitiesListView, GetLocalisationNameView

app_name = 'places'

urlpatterns = [
    path('countries/', CountriesListView.as_view()),
    path('cities/', CitiesListView.as_view()),
    path('localisation/<str:lon>/<str:lat>/', GetLocalisationNameView.as_view()),
]
