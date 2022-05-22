from colorfield.fields import ColorField
from django.db import models
from django.db.models import Model
from auth_shop.base.models import get_shop_avatar_path, ShopChoices, LonLatValidators
from auth_shop.base.models import AuthShopDays
from Qaryb_API_new.settings import API_URL
from uuid import uuid4
from io import BytesIO
from django.core.files.base import ContentFile


class TempShop(Model):
    shop_name = models.CharField(verbose_name='Shop name', max_length=150, blank=False, null=False)
    avatar = models.ImageField(verbose_name='Avatar', upload_to=get_shop_avatar_path, blank=False, null=False,
                               default=None)
    avatar_thumbnail = models.ImageField(verbose_name='Avatar', upload_to=get_shop_avatar_path, blank=True, null=True,
                                         default=None)
    color_code = ColorField(verbose_name='Color code', default='#FFFFFF')
    bg_color_code = ColorField(verbose_name='Color code', default='#FFFFFF')
    font_name = models.CharField(verbose_name='Font name', max_length=2,
                                 choices=ShopChoices.FONT_CHOICES, default='L')
    bio = models.TextField(verbose_name='Bio', null=True, blank=True)
    opening_days = models.ManyToManyField(AuthShopDays, verbose_name='Opening days',
                                          related_name='temp_shop_opening_days', blank=True)
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
                                  null=True, max_length=10, validators=[LonLatValidators.long_validator], default=None)
    latitude = models.FloatField(verbose_name='Latitude', blank=True,
                                 null=True, max_length=10, validators=[LonLatValidators.lat_validator], default=None)
    address_name = models.CharField(verbose_name='Address name', max_length=255,
                                    blank=True, null=True, default=None)
    km_radius = models.FloatField(verbose_name='Km radius', blank=True, null=True, default=None)
    qaryb_link = models.SlugField(verbose_name='Qaryb link', max_length=200, blank=True, null=True, unique=True,
                                  default=None)
    unique_id = models.CharField(verbose_name='Unique ID', unique=True, max_length=40)
    task_id = models.CharField(verbose_name='Task ID', max_length=40, default=None, null=True, blank=True)
    created_date = models.DateTimeField(verbose_name='Created date', editable=False, auto_now_add=True, db_index=True)
    updated_date = models.DateTimeField(verbose_name='Updated date', editable=False, auto_now=True)

    @property
    def property_extra_info(self):
        data = str(self.bio)
        return (data[:50] + '..') if len(data) > 50 else data

    def __str__(self):
        return '{} - {} - {}'.format(self.shop_name,
                                     self.phone,
                                     self.contact_email)

    class Meta:
        verbose_name = 'Temp Shop'
        verbose_name_plural = 'Temp Shops'
        ordering = ('created_date',)

    @property
    def get_absolute_avatar_img(self):
        if self.avatar:
            return "{0}/media{1}".format(API_URL, self.avatar.url)
        return None

    @property
    def get_absolute_avatar_thumbnail(self):
        if self.avatar_thumbnail:
            return "{0}/media{1}".format(API_URL, self.avatar_thumbnail.url)
        return None

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.jpg',
                                       ContentFile(image.getvalue()),
                                       save=True)
