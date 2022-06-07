from django.db.models.functions import Coalesce
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from places.base.filters import UserLanguageMixin, CountryFilterSet, CityFilterSet, BaseAllCountryFilter
from places.base.serializers import BaseCountrySerializer, BaseCitySerializer, BaseCountriesSerializer
from places.base.choices import PlaceType
from places.models import Country, City

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from places.base.language_cleaner import LanguageCleaner
from places.base.nominatim import NominatimSearch


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

    def get_queryset(self):
        if not self.request.GET.get('all'):
            return super().get_queryset()
        else:
            self.filter_class = BaseAllCountryFilter
            self.serializer_class = BaseCountriesSerializer
            return Country.objects.all()


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


class GetLocalisationNameView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        lang = 'FR'
        port = '7079'
        long = float(kwargs.get('lon'))
        lat = float(kwargs.get('lat'))
        try:
            clean_result = NominatimSearch(language=lang, port=port) \
                .get_name_of_place(lat=lat, long=long, additional_info=True)[0].get('address')
            needed_keys = ['commercial', 'road', 'industrial', 'neighbourhood', 'suburb',
                           'city_district', 'hamlet', 'town', 'village',
                           'county', 'residential', 'city']

            final_result = None
            for i in needed_keys:
                result = clean_result.get(i)
                if result is not None:
                    final_result = result
                    break

            if final_result is None:
                data = {'errors': 'The given geo is not a valid road!'}
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

            clean_result = LanguageCleaner().clear_string(final_result, 'tifinagh',
                                                          {'tifinagh': {'start': 'u2d30', 'end': 'u2d7f'}})

            data = {'localisation_name': clean_result}
            return Response(data=data, status=status.HTTP_200_OK)

        except (IndexError, AttributeError):
            data = {'errors': 'The given geo is not a valid road!'}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

