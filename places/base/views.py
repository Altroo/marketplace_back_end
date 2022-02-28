from django.db.models.functions import Coalesce
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from places.base.filters import UserLanguageMixin, CountryFilterSet, CityFilterSet
from places.base.serializers import BaseCountrySerializer, BaseCitySerializer
from places.base.choices import PlaceType
from places.base.models import Country, City


class PlaceLanguageMixin(UserLanguageMixin):
    """
    Mixin of places
    """

    permission_classes = (AllowAny,)

    def get_queryset(self):
        return super().get_queryset() \
            .annotate(language_name=Coalesce(f'name_{self.user_language.lower()}', 'name')) \
            .defer('name').exclude(language_name__exact='').order_by('language_name')


class CountriesListView(PlaceLanguageMixin, ListAPIView):
    """
    List of countries
    """

    permission_classes = (AllowAny,)
    queryset = Country.objects.filter(cities__isnull=False, type=PlaceType.COUNTRY).distinct()
    serializer_class = BaseCountrySerializer
    filter_class = CountryFilterSet
    pagination_class = None


class CitiesListView(PlaceLanguageMixin, ListAPIView):
    """
    List of countries
    """

    queryset = City.objects.all()
    serializer_class = BaseCitySerializer
    filter_class = CityFilterSet
    pagination_class = None

    def get_queryset(self):
        if not self.request.GET.get('code'):
            return self.queryset.model.objects.none()
        return super().get_queryset()
