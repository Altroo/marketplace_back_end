from django.urls import path

from .views import CountriesListView, CitiesListView, GetLocalisationNameView, CountryCodesListView

app_name = 'places'

urlpatterns = [
    # GET : countries with autocomplete params : (?all=true&name_fr=Mar)
    path('countries/', CountriesListView.as_view()),
    # GET : all available country codes
    path('country_codes/', CountryCodesListView.as_view()),
    # GET : city of a code country param : (?code=MA)
    path('cities/', CitiesListView.as_view()),
    # GET : localisation street name
    path('localisation/<str:lon>/<str:lat>/', GetLocalisationNameView.as_view()),
]
