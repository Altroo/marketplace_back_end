from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PlacesConfig(AppConfig):
    name = 'places'
    verbose_name = _('Countries and Cities')
