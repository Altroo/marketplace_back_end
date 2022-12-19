from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from places.base.choices import PlaceType


class AbstractCoordinates(models.Model):
    """
    Abstract model "Coordinates"
    """

    latitude = models.FloatField(verbose_name=_('Latitude'), blank=True, null=True)
    longitude = models.FloatField(verbose_name=_('Longitude'), blank=True, null=True)

    class Meta:
        abstract = True


class AbstractInternationalization(models.Model):
    """
    Abstract model "Internationalization of the name"
    """

    name = models.CharField(verbose_name=_('Name'), max_length=1000, blank=True)
    name_en = models.CharField(verbose_name=_('English name'), max_length=1000, blank=True)
    name_fr = models.CharField(verbose_name=_('French name'), max_length=1000, blank=True)
    name_ar = models.CharField(verbose_name=_('Arabic name'), max_length=1000, blank=True)

    class Meta:
        abstract = True


class AbstractOverpassTurbo(models.Model):
    """
    Abstract model "Overpass Turbo"
    """

    overpass_turbo_id = models.BigIntegerField(verbose_name=_('Overpass turbo ID'), blank=True, null=True)

    class Meta:
        abstract = True


class AbstractPlaceCode(models.Model):
    """
    Abstract model "Place code"
    """

    code = models.CharField(verbose_name=_('Code'), max_length=10, blank=True)

    class Meta:
        abstract = True


class Country(AbstractPlaceCode, AbstractOverpassTurbo, AbstractCoordinates, AbstractInternationalization):
    """
    Model "Place"
    """

    type = models.CharField(verbose_name=_('Type of country'), max_length=20, choices=PlaceType.CHOICES,
                            default=PlaceType.COUNTRY)
    parent = models.ForeignKey('self', verbose_name=_('Belong'), related_name='children', blank=True,
                               null=True, on_delete=models.CASCADE)
    currency = models.CharField(verbose_name=_('Currency'), max_length=20, blank=True, null=True)
    currency_ar = models.CharField(verbose_name=_('Currency AR'), max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ('-pk',)

    def __str__(self):
        return next(iter([self.name_en, self.name_fr, self.name_ar, self.name]))

    @cached_property
    def display_name(self):
        name = str(self)
        children = self.children.all()
        if children.exists():
            name += f' ({", ".join([str(child) for child in children])})'
        return name

    @property
    def is_country(self):
        return self.type == PlaceType.COUNTRY

    def clean(self):
        super().clean()
        if self.parent and self.type == PlaceType.COUNTRY:
            raise ValidationError('The country cannot belong to another country')


class City(AbstractOverpassTurbo, AbstractCoordinates, AbstractInternationalization):
    """
    Model "City"
    """

    country = models.ForeignKey(Country, verbose_name=_('Country'), related_name='cities', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
        ordering = ('-pk',)

    def __str__(self):
        return next(iter([self.name_en, self.name_fr, self.name_ar, self.name]))
