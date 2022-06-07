from rest_framework.response import Response
from rest_framework.views import APIView
from models import Cities
from rest_framework import status, permissions
from places.base.serializers import BaseCitiesListSerializer
from places.base.language_cleaner import LanguageCleaner
from places.base.nominatim import NominatimSearch


class CitiesListView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        cities = Cities.objects.all()
        serializer = BaseCitiesListSerializer(instance=cities, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


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
