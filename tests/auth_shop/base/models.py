from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Model
from os import path
from uuid import uuid4
from colorfield.fields import ColorField
from Qaryb_API_new.settings import API_URL
from io import BytesIO
from django.core.files.base import ContentFile
from account.models import CustomUser


def get_shop_avatar_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('shop_avatars/', str(uuid4()) + file_extension)


def get_shop_qr_code_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('shop_qrcodes/', str(uuid4()) + file_extension)


class ShopChoices:
    """
    Type of shop choices
    """

    # FONT_CHOICES = (
    #     ('LI', 'Light'),
    #     ('BO', 'Boldy'),
    #     ('CL', 'Classic'),
    #     ('MA', 'Magazine'),
    #     ('PO', 'Pop'),
    #     ('SA', 'Sans'),
    #     ('PA', 'Pacifico'),
    #     ('FI', 'Fira'),
    # )
    FONT_CHOICES = (
        ('L', 'Light'),
        ('R', 'Regular'),
        ('S', 'Semi-bold'),
        ('B', 'Black'),
    )

    ZONE_BY_CHOICES = (
        ('A', 'Address'),
        ('S', 'Sector')
    )

    CREATOR_STATUS_CHOICES = (
        ('A', 'En attente de confirmation'),
        ('R', 'Rejeté'),
        ('C', 'Confirmé'),
    )


class LonLatValidators:
    lat_validator = RegexValidator(r'^(\+|-)?(?:90(?:(?:\.0{1,6})?)|(?:[0-9]|[1-8][0-9])(?:(?:\.[0-9]{1,6})?))$',
                                   'Only Geo numbers are allowed.')
    long_validator = RegexValidator(r'^(\+|-)?(?:180(?:(?:\.0{1,6})?)|(?:[0-9]|[1-9][0-9]|1[0-7][0-9])'
                                    r'(?:(?:\.[0-9]{1,6})?))$',
                                    'Only Geo numbers are allowed.')


class AuthShopDays(Model):
    code_day = models.CharField(max_length=2, blank=True, null=True, default=None, unique=True)
    name_day = models.CharField(max_length=255, verbose_name='Day name', unique=True)

    def __str__(self):
        return '{} - {}'.format(self.code_day, self.name_day)

    class Meta:
        verbose_name = 'Day'
        verbose_name_plural = 'Days'


class AuthShop(Model):
    user = models.OneToOneField(CustomUser, verbose_name='User', on_delete=models.CASCADE,
                                related_name='user_authshop')
    shop_name = models.CharField(verbose_name='Shop name', max_length=150, blank=False, null=False)
    avatar = models.ImageField(verbose_name='Avatar', upload_to=get_shop_avatar_path, blank=False, null=False,
                               default=None)
    avatar_thumbnail = models.ImageField(verbose_name='Avatar thumbnail', upload_to=get_shop_avatar_path, blank=True,
                                         null=True, default=None)
    color_code = ColorField(verbose_name='Color code', default='#FFFFFF')
    bg_color_code = ColorField(verbose_name='Color code', default='#FFFFFF')
    # font_name = models.CharField(verbose_name='Font name', max_length=2,
    #                              choices=ShopChoices.FONT_CHOICES, default='L')
    font_name = models.CharField(verbose_name='Font name', max_length=1,
                                 choices=ShopChoices.FONT_CHOICES, default='L')
    bio = models.TextField(verbose_name='Bio', null=True, blank=True)
    opening_days = models.ManyToManyField(AuthShopDays, verbose_name='Opening days',
                                          related_name='authshop_opening_days', blank=True)
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
    qr_code_img = models.ImageField(verbose_name='QR code image', upload_to=get_shop_qr_code_path, blank=True,
                                    null=True, default=None)
    creator = models.BooleanField(verbose_name='Creator ?', default=False)
    mode_vacance_task_id = models.CharField(verbose_name='Mode Vacance Task ID', max_length=40, default=None,
                                            null=True, blank=True)
    # Dates
    created_date = models.DateTimeField(verbose_name='Created date', editable=False, auto_now_add=True, db_index=True)
    updated_date = models.DateTimeField(verbose_name='Updated date', editable=False, auto_now=True)

    @property
    def property_extra_info(self):
        data = str(self.bio)
        return (data[:50] + '..') if len(data) > 50 else data

    def __str__(self):
        return '{} - {}'.format(self.shop_name, self.user.email)

    class Meta:
        verbose_name = 'Auth Shop'
        verbose_name_plural = 'Auth Shops'
        ordering = ('-created_date',)

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

    @property
    def get_absolute_qr_code_img(self):
        if self.qr_code_img:
            return "{0}/media{1}".format(API_URL, self.qr_code_img.url)
        return None

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.jpg',
                                       ContentFile(image.getvalue()),
                                       save=True)

    def save_qr_code(self, field_name, image, uid):
        if not isinstance(image, BytesIO):
            return
        getattr(self, field_name).save(f'{str(uid)}.jpg',
                                       ContentFile(image.getvalue()),
                                       save=True)


class PhoneCodes(Model):
    phone_code = models.CharField(max_length=255, verbose_name='Phone code', unique=True)

    def __str__(self):
        return '{}'.format(self.phone_code)

    class Meta:
        verbose_name = 'Phone code'
        verbose_name_plural = 'Phone codes'


class AskForCreatorLabel(Model):
    auth_shop = models.OneToOneField(AuthShop, on_delete=models.CASCADE,
                                     verbose_name='Boutique',
                                     related_name='auth_shop_creator')
    status = models.CharField(verbose_name='Status', max_length=1,
                              choices=ShopChoices.CREATOR_STATUS_CHOICES, default='A')
    asked_counter = models.PositiveIntegerField(verbose_name='Fois demandé', default=1)
    # Dates
    created_date = models.DateTimeField(verbose_name='Date Création', editable=False, auto_now_add=True, db_index=True)
    updated_date = models.DateTimeField(verbose_name='Date mise à jour', editable=False, auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.auth_shop.shop_name, self.status)

    class Meta:
        verbose_name = 'Demande Créateur'
        verbose_name_plural = 'Demandes Créateur'


class ModeVacance(Model):
    auth_shop = models.OneToOneField(AuthShop, on_delete=models.CASCADE,
                                     verbose_name='Auth shop',
                                     related_name='auth_shop_mode_vacance')
    date_from = models.DateField(verbose_name="Date from", blank=True, null=True)
    date_to = models.DateField(verbose_name="Date to", blank=True, null=True)

    def __str__(self):
        return '{} - {} - {}'.format(self.auth_shop.shop_name, self.date_from, self.date_to)

    class Meta:
        verbose_name = 'Mode Vacance'
        verbose_name_plural = 'Mode Vacances'


class DeletedAuthShops(Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                             verbose_name='User', related_name='user_deleted_auth_shops')
    REASON_CHOICES = (
        ('', 'Unset'),
        ('A', 'Je cesse mon activité'),
        ('B', 'Je cesse mon activité 2'),
    )
    reason_choice = models.CharField(max_length=1, choices=REASON_CHOICES, default='', blank=True, null=True)
    typed_reason = models.CharField(max_length=140, null=True, blank=True, default='')

    def __str__(self):
        return '{} - {}'.format(self.user.email, self.reason_choice)

    class Meta:
        verbose_name = 'Deleted Store'
        verbose_name_plural = 'Deleted Stores'
