import abc
import csv
import io
import logging
import re
import time

import requests

logger = logging.getLogger(__name__)


class OverpassTurboUpdater:
    """
    Updating places from Overpass Turbo
    """

    base_url = 'https://overpass-api.de'
    template_overpass_query = '[out:csv({osm_fields})];{query}'
    overpass_query = None

    model = None

    fields_map = {
        'name': 'name',
        'name_en': 'name:en',
        'name_fr': 'name:fr',
        'name_ar': 'name:ar',
        'latitude': '@lat',
        'longitude': '@lon',
    }

    osm_fields = (
        '::id',
        '::lat',
        '::lon',
        'name',
        'name:en',
        'name:fr',
        'name:ar',
    )
    osm_fields_names_prefixes = (
        'alt', 'official',
    )

    # Requests params
    _retry_attempts = 5
    _retry_start_timeout = 1
    _retry_max_timeout = 30
    _retry_factor = 2

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.common_defaults = {}

    def run(self):
        try:
            self.update()
        except Exception as e:
            logger.error(e)

    def update(self):
        data = self.load_data()
        reader = csv.DictReader(io.StringIO(data), delimiter='\t', quoting=csv.QUOTE_NONE)
        self.create_or_update_data(reader)

    def load_data(self):
        data = None

        # Url
        url = self.construct_url()

        # Limit of requests
        attempt = 0

        # Headers
        headers = self.request_headers()

        # Request
        while attempt < self._retry_attempts:
            try:
                response = requests.get(url, **({'headers': headers} if headers else {}))
                data = response.content.decode('utf-8')
                break
            except requests.RequestException as e:
                logger.warning(f'Failed request at url: {url}. Status code: {e.response.status_code}')
                attempt += 1
                time.sleep(self.__calculate_delay(attempt))
        return data

    def get_overpass_query_string(self):
        return self.template_overpass_query.format(osm_fields=self.get_osm_fields(self.osm_fields),
                                                   query=self.get_overpass_query())

    def get_overpass_query(self):
        return self.overpass_query

    def construct_url(self):
        overpass_query = self.get_overpass_query_string()
        base_url = self.kwargs.get('url', self.base_url)
        query = re.sub(r'[\n\r]', '', overpass_query) if overpass_query else ''
        return f'{base_url}/api/interpreter?data={query.strip()}'

    @abc.abstractmethod
    def request_headers(self):
        return {}

    def __calculate_delay(self, used_attempts=1):
        timeout = self._retry_start_timeout * (self._retry_factor ** (used_attempts - 1))
        return min(timeout, self._retry_max_timeout)

    def create_or_update_data(self, data):
        for item in data:
            self.model.objects.update_or_create(overpass_turbo_id=item.pop('@id'),
                                                defaults=self.get_defaults(item))

    def get_osm_fields(self, osm_fields):
        fields = []
        for field in osm_fields:
            fields.append(field if field.startswith('::') else f'"{field}"')
            if field.startswith('name'):
                fields.extend([f'"{prefix}_{field}"' for prefix in self.osm_fields_names_prefixes])
        return ','.join(fields)

    def get_fields_map(self):
        return self.fields_map

    def get_defaults(self, item):
        defaults = self.common_defaults.copy()
        for db_field, osm_field in self.get_fields_map().items():
            value = self.get_default(osm_field, item)
            if not value:
                continue
            try:
                value = self.model._meta.get_field(db_field).to_python(value)
                if db_field.startswith('name'):
                    value = re.sub(r'(^\W*)|(\W$)', '', value)
                value = str(value).split(',')[0].strip()
                defaults.update({db_field: value})
            except TypeError:
                pass
        return defaults

    def get_default(self, osm_field, item):
        if osm_field.startswith('name'):
            return self._get_first_not_none_value(osm_field, item, self.osm_fields_names_prefixes)
        return item.get(osm_field)

    @staticmethod
    def _get_first_not_none_value(osm_field, item, prefixes, reverse=False):
        with_prefixes = [item.get(reverse and f'{osm_field}:{prefix}' or f'{prefix}_{osm_field}')
                         for prefix in prefixes]
        return next(iter([item.get(osm_field), *with_prefixes]), None)
