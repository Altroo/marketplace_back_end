from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Model
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .managers import CustomUserManager
from os import path
from Qaryb_API_new.settings import API_URL
from colorfield.fields import ColorField


def get_avatar_path(instance, filename):
    # filename, file_extension = path.splitext(filename)
    # return path.join('media/photos/', str(instance.id) + file_extension)
    return path.join('avatar/', filename)


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


class ShopValidators:
    lat_validator = RegexValidator(r'^(\+|-)?(?:90(?:(?:\.0{1,6})?)|(?:[0-9]|[1-8][0-9])(?:(?:\.[0-9]{1,6})?))$',
                                   'Only Geo numbers are allowed.')
    long_validator = RegexValidator(r'^(\+|-)?(?:180(?:(?:\.0{1,6})?)|(?:[0-9]|[1-9][0-9]|1[0-7][0-9])'
                                    r'(?:(?:\.[0-9]{1,6})?))$',
                                    'Only Geo numbers are allowed.')


class AuthShop(AbstractBaseUser, PermissionsMixin):
    # Password (hidden)
    email = models.EmailField(_('email address'), unique=True)
    shop_name = models.CharField(verbose_name='Shop name', max_length=150, blank=False, null=False)
    avatar = models.ImageField(verbose_name='Avatar', upload_to=get_avatar_path, blank=True, null=True,
                                   default=None, max_length=1000)
    color_code = ColorField(verbose_name='Color code', default='#FFFFFF')
    font_name = models.CharField(verbose_name='Font name', max_length=2, choices=ShopChoices.FONT_CHOICES, default='L')
    bio = models.TextField(verbose_name='Bio', null=True, blank=True)
    opening_days = models.CharField(verbose_name='Opening days', max_length=13, blank=False, null=False,
                                    default='0,0,0,0,0,0,0')
    morning_hour_from = models.TimeField(verbose_name='Morning hour from', blank=True, null=True, default=None)
    morning_hour_to = models.TimeField(verbose_name='Morning hour to', blank=True, null=True, default=None)
    afternoon_hour_from = models.TimeField(verbose_name='Afternoon hour from', blank=True, null=True, default=None)
    afternoon_hour_to = models.TimeField(verbose_name='Afternoon hour to', blank=True, null=True, default=None)
    phone = models.CharField(verbose_name='Phone number', max_length=15, blank=True, null=True, default=None)
    contact_email = models.EmailField(verbose_name='Contact Email', blank=True, null=True, default=None)
    website_link = models.URLField(verbose_name='Website', blank=True, null=True, default=None)
    facebook_link = models.URLField(verbose_name='Facebook', blank=True, null=True, default=None)
    twitter_link = models.URLField(verbose_name='Twitter', blank=True, null=True, default=None)
    instagram_link = models.URLField(verbose_name='Instagram', blank=True, null=True, default=None)
    whatsapp = models.CharField(verbose_name='Whatsapp number', max_length=15, blank=True, null=True, default=None)
    zone_by = models.CharField(verbose_name='Zone by', max_length=1, choices=ShopChoices.ZONE_BY_CHOICES, default='A')
    longitude = models.FloatField(verbose_name='Longitude', blank=True,
                                  null=True, max_length=10, validators=[ShopValidators.long_validator], default=None)
    latitude = models.FloatField(verbose_name='Latitude', blank=True,
                                 null=True, max_length=10, validators=[ShopValidators.lat_validator], default=None)
    address_name = models.CharField(verbose_name='Address name', max_length=255,
                                    blank=True, null=True, default=None)
    km_radius = models.FloatField(verbose_name='Km radius', blank=True, null=True, default=None)
    qaryb_link = models.URLField(verbose_name='Qaryb link', max_length=200, blank=False, null=False, unique=True)
    # permissions
    is_staff = models.BooleanField(_('staff status'),
                                   default=False,
                                   help_text=_('Designates whether the user can log into this admin site.'), )
    is_active = models.BooleanField(_('active'),
                                    default=False,
                                    help_text=_(
                                        'Designates whether this user should be treated as active. '
                                        'Unselect this instead of deleting accounts.'
                                    ), )
    # DATES
    created_date = models.DateTimeField(_('date joined'), default=timezone.now)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def get_absolute_avatar(self):
        if self.avatar:
            return "{0}{1}".format(API_URL, self.avatar.url)
        return None

    class Meta:
        verbose_name = 'Auth Shop'
        verbose_name_plural = 'Auth Shops'
        ordering = ('created_date',)
        # unique_together = (('email', 'phone'),)


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
