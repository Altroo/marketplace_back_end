import asyncio
import json
import logging
from collections import namedtuple
from json import JSONDecodeError
from urllib.parse import urlencode
from Qaryb_API_new.settings import NOMINATIM_PROTOCOL, MAP_DOMAIN
from places.base.utils import RequestMixin


logger = logging.getLogger(__file__)


class NominatimSearch(RequestMixin):
    """
    Class: Nominatim
    Search for place names

    :lat: latitude of point for search -> float;
    :long: longitude of point for search -> float;
    :kwargs: Extra named options
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initializing other variables (settings etc.)
        self.kwargs = kwargs
        self.error_response = dict(error=self.kwargs.get('error', 'No results were found for your request'))

    def _url(self, key: str = 'reverse', queryparams: dict = {}):
        """
        Get url for search
        """
        url = f"{NOMINATIM_PROTOCOL}://{MAP_DOMAIN}:{self.kwargs.get('port')}/{key}"
        queryparams.update({'accept-language': self.kwargs.get('language', 'en')})
        return f'{url}?{urlencode(queryparams)}'

    async def reverse(self, queryparams: dict = {}, session=None):
        """
        Search for a place by coordinate
        """
        queryparams.update(format='geojson', addressdetails=1)
        url = self._url(key='reverse', queryparams=queryparams)
        return await self._request(url, session=session)

    @staticmethod
    def __construct_point(lat: float, long: float):
        """
        Dynamically construct point for search
        :param lat: float;
        :param long: float;
        :return: Point(lat=lat, long=long)
        """
        return namedtuple('Point', ['lat', 'lon'])(lat, long)

    async def _get_name_of_place(self, lat, long, session=None, additional_info=False, coordinates=False):
        """
        Getting place name
        """
        point = self.__construct_point(lat, long)

        if not session:
            _session = self._get_session()
            async with _session as session:
                data = await self.reverse(point._asdict(), session=session)
        else:
            data = await self.reverse(point._asdict(), session=session)

        try:
            data = json.loads(data)
        except JSONDecodeError:
            return self.error_response

        if not data or not (data and isinstance(data, dict) and 'features' in data):
            return self.error_response

        feature = data.get('features')
        if len(feature) == 0 or not feature[0].get('properties'):
            return self.error_response

        keys = ('name', 'display_name',)
        if additional_info:
            keys += ('category', 'type', 'address',)

        information = {key: value for key, value in feature[0].get('properties').items() if key in keys}
        if coordinates:
            information.update(dict(coordinates=point._asdict()))
        return information

    async def _get_names_of_places(self, points, additional_info=False, coordinates=False):
        """
        Getting place`s names
        :param points: [dict(lat=..., long=...), ...]
        :return:
        """
        _session = self._get_session()
        _places = []
        async with _session as session:
            _places = await asyncio.gather(
                *[self._get_name_of_place(**point, session=session,
                                          additional_info=additional_info, coordinates=coordinates)
                  for point in points])
        return _places

    def get_names_of_places(self, points, only_display_name=True, coordinates=False):
        """
        Getting place`s names
        :param coordinates:
        :param points: [dict(lat=..., long=...), ...]
        :param only_display_name: return list of display_names, else list of dicts
        :return: list
        """
        loop = self._get_event_loop()
        places = loop.run_until_complete(self._get_names_of_places(points, additional_info=not only_display_name,
                                                                   coordinates=coordinates))

        if only_display_name:
            if coordinates:
                return [dict(display_name=place.get('display_name'), coordinates=place.get('coordinates'))
                        for place in places]
            return [place.get('display_name') for place in places]
        return places

    def get_name_of_place(self, lat, long, additional_info=False, coordinates=False):
        """
        Getting place name
        """
        loop = self._get_event_loop()
        place = loop.run_until_complete(
            asyncio.gather(self._get_name_of_place(lat, long, additional_info=additional_info, coordinates=coordinates))
        )
        return place


# def main():
#     """
#     Response Examples
#     Short response (Without additional information)
#     {
#         'name': ...,
#         'display_name': ...
#     }
#
#     # Full response (With additional information)
#     {
#         'name': ...,
#         'display_name': ...,
#         'category': ...,
#         'type': ...,
#         'address': {
#             'city': ...,
#             'city_district': ...,
#             'country': ...,
#             'country_code': ...,
#             'county': ...,
#             'mobile_phone': ...,
#             'postcode': ...,
#             'region': ...,
#             'road': ...,
#             'state_district': ...,
#             'suburb': ...
#         }
#     }
#     """
#     # If authorization is needed, you need to specify a token
#     # search = NominatimSearch(auth_token='UGF2ZWw6NGE2MjRsMks4UGNpMw==')
#     search = NominatimSearch(language='hu')
#
#     # Without additional information (only Name and Display Name)
#     search.get_name_of_place(lat=34.018180, long=-6.828690)
#
#     # With additional information (Name, Display Name, Category, Type, Address)
#     search.get_name_of_place(lat=34.018180, long=-6.828690, additional_info=True)
#
#     # Single line call
#     NominatimSearch(language='hu').get_name_of_place(lat=34.018180, long=-6.828690)
#
#     # Get names of places
#     # Name and Display name and coordinates
#     search.get_names_of_places([
#         dict(lat=34.018180, long=-6.828690),
#         dict(lat=34.018180, long=-6.828690),
#         dict(lat=34.018180, long=-6.828690),
#         dict(lat=34.018180, long=-6.828690),
#         dict(lat=34.018180, long=-6.828690),
#         dict(lat=34.018180, long=-6.828690)
#     ], only_display_name=False, coordinates=True)
#
#     # Only Display name
#     search.get_names_of_places([
#         dict(lat=34.018180, long=-6.828690),
#         dict(lat=34.018180, long=-6.828690),
#         dict(lat=34.018180, long=-6.828690),
#         dict(lat=34.018180, long=-6.828690),
#         dict(lat=34.018180, long=-6.828690),
#         dict(lat=34.018180, long=-6.828690)
#     ])
#
#
# if __name__ == '__main__':
#     main()
