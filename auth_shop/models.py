from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Model
from os import path
from uuid import uuid4


def get_avatar_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('avatar/', str(uuid4()) + file_extension)


class ShopChoices:
    """
    Type of shop choices
    """

    FONT_CHOICES = (
        ('LI', 'Light'),
        ('BO', 'Boldy'),
        ('CL', 'Classic'),
        ('MA', 'Magazine'),
        ('PO', 'Pop'),
        ('SA', 'Sans'),
        ('PA', 'Pacifico'),
        ('FI', 'Fira'),
    )

    ZONE_BY_CHOICES = (
        ('A', 'Address'),
        ('S', 'Sector')
    )


class LonLatValidators:
    lat_validator = RegexValidator(r'^(\+|-)?(?:90(?:(?:\.0{1,6})?)|(?:[0-9]|[1-8][0-9])(?:(?:\.[0-9]{1,6})?))$',
                                   'Only Geo numbers are allowed.')
    long_validator = RegexValidator(r'^(\+|-)?(?:180(?:(?:\.0{1,6})?)|(?:[0-9]|[1-9][0-9]|1[0-7][0-9])'
                                    r'(?:(?:\.[0-9]{1,6})?))$',
                                    'Only Geo numbers are allowed.')


class Categories(Model):
    code_category = models.CharField(max_length=2, blank=True, null=True, default=None, unique=True)
    name_category = models.CharField(max_length=255, verbose_name='Category Name', unique=True)

    def __str__(self):
        return '{} - {}'.format(self.code_category, self.name_category)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class Colors(Model):
    code_color = models.CharField(max_length=2, blank=True, null=True, default=None, unique=True)
    name_color = models.CharField(max_length=255, verbose_name='Color Name', unique=True)

    def __str__(self):
        return '{} - {}'.format(self.code_color, self.name_color)

    class Meta:
        verbose_name = 'Color'
        verbose_name_plural = 'Colors'


class Sizes(Model):
    code_size = models.CharField(max_length=2, blank=True, null=True, default=None, unique=True)
    name_size = models.CharField(max_length=255, verbose_name='Size Name', unique=True)

    def __str__(self):
        return '{} - {}'.format(self.code_size, self.name_size)

    class Meta:
        verbose_name = 'Size'
        verbose_name_plural = 'Sizes'


class ForWhom(Model):
    code_for_whom = models.CharField(max_length=2, blank=True, null=True, default=None, unique=True)
    name_for_whom = models.CharField(max_length=255, verbose_name='For whom Name', unique=True)

    def __str__(self):
        return '{} - {}'.format(self.code_for_whom, self.name_for_whom)

    class Meta:
        verbose_name = 'For Whom'
        verbose_name_plural = 'For Whom'


class Days(Model):
    code_day = models.CharField(max_length=2, blank=True, null=True, default=None, unique=True)
    name_day = models.CharField(max_length=255, verbose_name='Day name', unique=True)

    def __str__(self):
        return '{} - {}'.format(self.code_day, self.name_day)

    class Meta:
        verbose_name = 'Day'
        verbose_name_plural = 'Days'
