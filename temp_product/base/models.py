from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Model
from os import path
from auth_shop.models import Categories, Colors, Sizes
from places.base.models import Cities
from uuid import uuid4
from io import BytesIO
from django.core.files.base import ContentFile
from Qaryb_API_new.settings import API_URL
from temp_shop.base.models import TempShop


def get_shop_products_path(instance, filename):
    return path.join('shop_products/', filename)


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

    PRODUCT_TYPE_CHOICES = (
        ('V', 'Sell'),
        ('S', 'Service'),
        ('L', 'Location')
    )

    FOR_WHOM_CHOICES = (
        ('A', 'All'),
        ('K', 'Kid'),
        ('F', 'Female'),
        ('M', 'Man'),
    )

    COLOR_CHOICES = (
        ('BK', 'Black'),
        ('WT', 'White'),
        ('BR', 'Brown'),
        ('BL', 'Blue'),
        ('GN', 'Green'),
        ('PR', 'Purple'),
        ('OR', 'Orange'),
        ('PI', 'Pink'),
        ('YE', 'Yellow'),
        ('GR', 'Gray'),
        ('MC', 'MultiColor'),
        ('RD', 'Red'),
    )

    SIZE_CHOICES = (
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('X', 'XLarge'),
    )

    PRICE_BY_CHOICES = (
        ('U', 'Unity'),
        ('K', 'Kilogram'),
        ('L', 'Liter'),

    )


class ShopValidators:
    lat_validator = RegexValidator(r'^(\+|-)?(?:90(?:(?:\.0{1,6})?)|(?:[0-9]|[1-8][0-9])(?:(?:\.[0-9]{1,6})?))$',
                                   'Only Geo numbers are allowed.')
    long_validator = RegexValidator(r'^(\+|-)?(?:180(?:(?:\.0{1,6})?)|(?:[0-9]|[1-9][0-9]|1[0-7][0-9])'
                                    r'(?:(?:\.[0-9]{1,6})?))$',
                                    'Only Geo numbers are allowed.')


class TempProduct(Model):
    temp_shop = models.ForeignKey(TempShop, on_delete=models.CASCADE,
                                  verbose_name='Temp Shop', related_name='temp_shop')
    product_type = models.CharField(verbose_name='Product Type', max_length=1,
                                    choices=ShopChoices.PRODUCT_TYPE_CHOICES)
    product_category = models.ManyToManyField(Categories, verbose_name='Product Categories',
                                              related_name='temp_product_categories')
    product_name = models.CharField(verbose_name='Product Name', max_length=150, blank=False, null=False)
    picture_1 = models.ImageField(verbose_name='Picture 1', upload_to=get_shop_products_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_2 = models.ImageField(verbose_name='Picture 2', upload_to=get_shop_products_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_3 = models.ImageField(verbose_name='Picture 3', upload_to=get_shop_products_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_4 = models.ImageField(verbose_name='Picture 4', upload_to=get_shop_products_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_1_thumbnail = models.ImageField(verbose_name='Picture 1 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_products_path, max_length=1000)
    picture_2_thumbnail = models.ImageField(verbose_name='Picture 2 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_products_path, max_length=1000)
    picture_3_thumbnail = models.ImageField(verbose_name='Picture 3 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_products_path, max_length=1000)
    picture_4_thumbnail = models.ImageField(verbose_name='Picture 4 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_products_path, max_length=1000)
    description = models.TextField(verbose_name='Description', null=True, blank=True)
    for_whom = models.CharField(verbose_name='For Whom', max_length=1,
                                choices=ShopChoices.FOR_WHOM_CHOICES)
    product_color = models.ManyToManyField(Colors, verbose_name='Product Colors',
                                           related_name='temp_product_colors')
    product_size = models.ManyToManyField(Sizes, verbose_name='Product Sizes',
                                          related_name='temp_product_sizes')
    quantity = models.PositiveIntegerField(verbose_name='Quantity', default=0)
    price = models.PositiveIntegerField(verbose_name='Price', default=0)
    price_by = models.CharField(verbose_name='Price by', choices=ShopChoices.PRICE_BY_CHOICES, max_length=1)
    shop_longitude = models.FloatField(verbose_name='Shop Longitude', blank=True,
                                       null=True, max_length=10, validators=[ShopValidators.long_validator],
                                       default=None)
    shop_latitude = models.FloatField(verbose_name='Shop Latitude', blank=True,
                                      null=True, max_length=10, validators=[ShopValidators.lat_validator], default=None)
    shop_address = models.CharField(verbose_name='Shop Address', max_length=255,
                                    blank=True, null=True, default=None)
    created_date = models.DateTimeField(editable=False, auto_now=True)

    @property
    def property_extra_info(self):
        data = str(self.description)
        return (data[:50] + '..') if len(data) > 50 else data

    def __str__(self):
        return '{} - {} - {}'.format(self.product_type,
                                     self.product_name,
                                     self.price)

    class Meta:
        verbose_name = 'Temp Product'
        verbose_name_plural = 'Temp Products'
        ordering = ('created_date',)

    @property
    def get_absolute_picture_1_img(self):
        if self.picture_1:
            return "{0}{1}".format(API_URL, self.picture_1.url)
        return None

    @property
    def get_absolute_picture_1_thumbnail(self):
        if self.picture_1_thumbnail:
            return "{0}{1}".format(API_URL, self.picture_1_thumbnail.url)
        return None

    @property
    def get_absolute_picture_2_img(self):
        if self.picture_2:
            return "{0}{1}".format(API_URL, self.picture_2.url)
        return None

    @property
    def get_absolute_picture_2_thumbnail(self):
        if self.picture_2_thumbnail:
            return "{0}{1}".format(API_URL, self.picture_2_thumbnail.url)
        return None

    @property
    def get_absolute_picture_3_img(self):
        if self.picture_3:
            return "{0}{1}".format(API_URL, self.picture_3.url)
        return None

    @property
    def get_absolute_picture_3_thumbnail(self):
        if self.picture_3_thumbnail:
            return "{0}{1}".format(API_URL, self.picture_3_thumbnail.url)
        return None

    @property
    def get_absolute_picture_4_img(self):
        if self.picture_4:
            return "{0}{1}".format(API_URL, self.picture_4.url)
        return None

    @property
    def get_absolute_picture_4_thumbnail(self):
        if self.picture_4_thumbnail:
            return "{0}{1}".format(API_URL, self.picture_4_thumbnail.url)
        return None

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.jpg',
                                       ContentFile(image.getvalue()),
                                       save=True)


class TempDelivery(Model):
    temp_product = models.ForeignKey(TempProduct, on_delete=models.CASCADE,
                                     verbose_name='Temp product',
                                     related_name='temp_delivery_temp_product')
    temp_delivery_city = models.ManyToManyField(Cities, verbose_name='Temp Delivery City',
                                                related_name='temp_delivery_city')
    temp_delivery_price = models.PositiveIntegerField(verbose_name='Temp delivery Price', default=0)
    temp_delivery_days = models.PositiveIntegerField(verbose_name='Temp number of Days', default=0)

    def __str__(self):
        return '{} - {} - {}'.format(self.temp_product.pk,
                                     self.temp_delivery_price,
                                     self.temp_delivery_days)

    class Meta:
        verbose_name = 'Temp Delivery'
        verbose_name_plural = 'Temp Deliveries'
