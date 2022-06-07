from django.db import models
from django.db.models import Model
from offer.base.models import Categories, Colors, Sizes, ForWhom, ServiceDays
from models import LonLatValidators, TempShop
from uuid import uuid4
from io import BytesIO
from django.core.files.base import ContentFile
from Qaryb_API_new.settings import API_URL
from offer.base.models import get_shop_offers_path, OfferChoices, OfferTags
from models import City


class TempOffers(Model):
    temp_shop = models.ForeignKey(TempShop, on_delete=models.CASCADE,
                                  verbose_name='Temp Shop', related_name='temp_shop')
    offer_type = models.CharField(verbose_name='Offer Type', max_length=1,
                                  choices=OfferChoices.OFFER_TYPE_CHOICES)
    offer_categories = models.ManyToManyField(Categories, verbose_name='Offer Categories',
                                              related_name='temp_offer_categories')
    title = models.CharField(verbose_name='title', max_length=150, blank=False, null=False)
    picture_1 = models.ImageField(verbose_name='Picture 1', upload_to=get_shop_offers_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_2 = models.ImageField(verbose_name='Picture 2', upload_to=get_shop_offers_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_3 = models.ImageField(verbose_name='Picture 3', upload_to=get_shop_offers_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_1_thumbnail = models.ImageField(verbose_name='Picture 1 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_offers_path, max_length=1000)
    picture_2_thumbnail = models.ImageField(verbose_name='Picture 2 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_offers_path, max_length=1000)
    picture_3_thumbnail = models.ImageField(verbose_name='Picture 3 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_offers_path, max_length=1000)
    description = models.TextField(verbose_name='Description', null=True, blank=True)
    for_whom = models.ManyToManyField(ForWhom, verbose_name='For Whom',
                                      related_name='temp_offer_for_whom')
    price = models.FloatField(verbose_name='Price', default=0.0)
    tags = models.ManyToManyField(OfferTags, verbose_name='Temp Offer Tags', related_name='temp_offer_tags')
    created_date = models.DateTimeField(verbose_name='Created date', editable=False, auto_now_add=True, db_index=True)
    updated_date = models.DateTimeField(verbose_name='Updated date', editable=False, auto_now=True)

    @property
    def property_extra_info(self):
        data = str(self.description)
        return (data[:50] + '..') if len(data) > 50 else data

    def __str__(self):
        return '{} - {} - {}'.format(self.offer_type,
                                     self.title,
                                     self.price)

    class Meta:
        verbose_name = 'Temp Offer'
        verbose_name_plural = 'Temp Offers'
        ordering = ('created_date',)

    @property
    def get_absolute_picture_1_img(self):
        if self.picture_1:
            return "{0}/media{1}".format(API_URL, self.picture_1.url)
        return None

    @property
    def get_absolute_picture_1_thumbnail(self):
        if self.picture_1_thumbnail:
            return "{0}/media{1}".format(API_URL, self.picture_1_thumbnail.url)
        return None

    @property
    def get_absolute_picture_2_img(self):
        if self.picture_2:
            return "{0}/media{1}".format(API_URL, self.picture_2.url)
        return None

    @property
    def get_absolute_picture_2_thumbnail(self):
        if self.picture_2_thumbnail:
            return "{0}/media{1}".format(API_URL, self.picture_2_thumbnail.url)
        return None

    @property
    def get_absolute_picture_3_img(self):
        if self.picture_3:
            return "{0}/media{1}".format(API_URL, self.picture_3.url)
        return None

    @property
    def get_absolute_picture_3_thumbnail(self):
        if self.picture_3_thumbnail:
            return "{0}/media{1}".format(API_URL, self.picture_3_thumbnail.url)
        return None

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.jpg',
                                       ContentFile(image.getvalue()),
                                       save=True)


class TempProducts(Model):
    temp_offer = models.OneToOneField(TempOffers, on_delete=models.CASCADE,
                                      verbose_name='Temp Offer', related_name='temp_offer_products')
    product_colors = models.ManyToManyField(Colors, verbose_name='Product Colors',
                                            related_name='temp_product_colors')
    product_sizes = models.ManyToManyField(Sizes, verbose_name='Product Sizes',
                                           related_name='temp_product_sizes')
    product_quantity = models.PositiveIntegerField(verbose_name='Quantity', default=None, null=True, blank=True)
    product_price_by = models.CharField(verbose_name='Price by', choices=OfferChoices.PRODUCT_PRICE_BY_CHOICES,
                                        max_length=1)
    product_longitude = models.FloatField(verbose_name='Product Longitude', blank=True,
                                          null=True, max_length=10, validators=[LonLatValidators.long_validator],
                                          default=None)
    product_latitude = models.FloatField(verbose_name='Product Latitude', blank=True,
                                         null=True, max_length=10,
                                         validators=[LonLatValidators.lat_validator], default=None)
    product_address = models.CharField(verbose_name='Product Address', max_length=255,
                                       blank=True, null=True, default=None)

    def __str__(self):
        return '{}'.format(self.temp_offer.title)

    class Meta:
        verbose_name = 'Temp Product'
        verbose_name_plural = 'Temp Products'
        ordering = ('-pk',)


class TempServices(Model):
    temp_offer = models.OneToOneField(TempOffers, on_delete=models.CASCADE,
                                      verbose_name='Temp Offer', related_name='temp_offer_services')
    service_availability_days = models.ManyToManyField(ServiceDays, verbose_name='Opening days',
                                                       related_name='temp_service_availability_days')
    service_morning_hour_from = models.TimeField(verbose_name='Morning hour from', blank=True, null=True, default=None)
    service_morning_hour_to = models.TimeField(verbose_name='Morning hour to', blank=True, null=True, default=None)
    service_afternoon_hour_from = models.TimeField(verbose_name='Afternoon hour from', blank=True, null=True,
                                                   default=None)
    service_afternoon_hour_to = models.TimeField(verbose_name='Afternoon hour to', blank=True, null=True, default=None)
    service_zone_by = models.CharField(verbose_name='Zone by', max_length=1, choices=OfferChoices.ZONE_BY_CHOICES,
                                       default='A')
    service_price_by = models.CharField(verbose_name='Price by', choices=OfferChoices.SERVICE_PRICE_BY_CHOICES,
                                        max_length=1)
    service_longitude = models.FloatField(verbose_name='Service Longitude', blank=True,
                                          null=True, max_length=10, validators=[LonLatValidators.long_validator],
                                          default=None)
    service_latitude = models.FloatField(verbose_name='Service Latitude', blank=True,
                                         null=True, max_length=10,
                                         validators=[LonLatValidators.lat_validator], default=None)
    service_address = models.CharField(verbose_name='Service Address', max_length=255,
                                       blank=True, null=True, default=None)
    service_km_radius = models.FloatField(verbose_name='Km radius', blank=True, null=True, default=None)

    def __str__(self):
        return '{}'.format(self.temp_offer.title)

    class Meta:
        verbose_name = 'Temp Service'
        verbose_name_plural = 'Temp Services'
        ordering = ('-pk',)


# class TempDelivery(Model):
#     temp_offer = models.OneToOneField(TempOffers, on_delete=models.CASCADE,
#                                       verbose_name='Temp offer',
#                                       related_name='temp_offer_delivery')
#     temp_delivery_city_1 = models.CharField(verbose_name='Temp Delivery City 1', max_length=300,
#                                             blank=True, null=True, default=None)
#     temp_delivery_price_1 = models.FloatField(verbose_name='Temp delivery Price 1',
#                                               default=0.0, blank=True, null=True)
#     temp_delivery_days_1 = models.PositiveIntegerField(verbose_name='Temp number of Days 1',
#                                                        default=0, blank=True, null=True)
#     temp_delivery_city_2 = models.CharField(verbose_name='Temp Delivery City 2', max_length=300,
#                                             blank=True, null=True, default=None)
#     temp_delivery_price_2 = models.FloatField(verbose_name='Temp delivery Price 2',
#                                               default=0.0, blank=True, null=True)
#     temp_delivery_days_2 = models.PositiveIntegerField(verbose_name='Temp number of Days 2',
#                                                        default=0, blank=True, null=True)
#     temp_delivery_city_3 = models.CharField(verbose_name='Temp Delivery City 3', max_length=300,
#                                             blank=True, null=True, default=None)
#     temp_delivery_price_3 = models.FloatField(verbose_name='Temp delivery Price 3',
#                                               default=0.0, blank=True, null=True)
#     temp_delivery_days_3 = models.PositiveIntegerField(verbose_name='Temp number of Days 3',
#                                                        default=0, blank=True, null=True)
#
#     def __str__(self):
#         return '{} - {} - {} - {}'.format(self.temp_offer.title,
#                                           self.temp_delivery_city_1,
#                                           self.temp_delivery_price_1,
#                                           self.temp_delivery_days_1)
#
#     class Meta:
#         verbose_name = 'Temp Delivery'
#         verbose_name_plural = 'Temp Deliveries'


class TempDelivery(Model):
    temp_offer = models.ForeignKey(TempOffers, on_delete=models.CASCADE,
                                   verbose_name='Temp Offer',
                                   related_name='temp_offer_delivery')
    temp_delivery_city = models.ManyToManyField(City, verbose_name='Temp Delivery City',
                                                related_name='temp_delivery_city')
    temp_delivery_price = models.FloatField(verbose_name='Temp delivery Price', default=0.0)
    temp_delivery_days = models.PositiveIntegerField(verbose_name='Temp number of Days', default=0)

    def __str__(self):
        return '{} - {} - {}'.format(self.temp_offer.pk,
                                     self.temp_delivery_price,
                                     self.temp_delivery_days)

    class Meta:
        verbose_name = 'Temp Delivery'
        verbose_name_plural = 'Temp Deliveries'


class TempSolder(Model):
    temp_offer = models.OneToOneField(TempOffers, on_delete=models.CASCADE,
                                      verbose_name='Temp Offer',
                                      related_name='temp_offer_solder', unique=True)
    temp_solder_type = models.CharField(verbose_name='Temp solder type', choices=OfferChoices.SOLDER_BY_CHOICES,
                                        max_length=1)
    temp_solder_value = models.FloatField(verbose_name='Temp solder value', default=0.0)

    def __str__(self):
        return "{} - {} - {}".format(self.temp_offer.pk,
                                     self.temp_solder_type,
                                     self.temp_solder_value)

    class Meta:
        verbose_name = 'Temp Solder'
        verbose_name_plural = 'Temp Solder'
