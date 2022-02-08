from django.urls import path
from places.base.views import CitiesListView, GetLocalisationNameView

app_name = 'places'

urlpatterns = [
    # Auth shop
    # GET : get list of cities
    path('cities', CitiesListView.as_view()),
    path('localisation/<str:lon>/<str:lat>', GetLocalisationNameView.as_view()),
]
