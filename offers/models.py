from os import path
from django.db import models
from django.db.models import Model
from places.base.choices import PlaceType
from shop.models import AuthShop, LonLatValidators
from Qaryb_API.settings import API_URL
from uuid import uuid4
from io import BytesIO
from django.core.files.base import ContentFile
from places.models import City, Country


def get_shop_offers_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('shop_offers/', str(uuid4()) + file_extension)


def get_fallback_shop_offers_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('fallback_shop_offers/', str(uuid4()) + file_extension)


class OfferChoices:
    """
    Type of shop choices
    """

    ZONE_BY_CHOICES = (
        ('A', 'Address'),
        ('S', 'Sector')
    )

    OFFER_TYPE_CHOICES = (
        ('V', 'Sell'),
        ('S', 'Service'),
        ('L', 'Location')
    )

    PRODUCT_PRICE_BY_CHOICES = (
        ('U', 'Unity'),
        ('K', 'Kilogram'),
        ('L', 'Liter'),
    )

    SERVICE_PRICE_BY_CHOICES = (
        ('H', 'Heur'),
        ('J', 'Jour'),
        ('S', 'Semaine'),
        ('M', 'Mois'),
        ('P', 'Prestation'),
    )

    SOLDER_BY_CHOICES = (
        ('F', 'Prix fix'),
        ('P', 'Pourcentage'),
    )


class Categories(Model):
    code_category = models.CharField(max_length=2, blank=True, null=True, default=None, unique=True)
    name_category = models.CharField(max_length=255, verbose_name='Category Name', unique=True)

    def __str__(self):
        return '{} - {}'.format(self.code_category, self.name_category)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class OfferTags(Model):
    name_tag = models.CharField(max_length=255, verbose_name='Tag name', unique=True)

    def __str__(self):
        return '{}'.format(self.name_tag)

    class Meta:
        verbose_name = 'Offer Tag'
        verbose_name_plural = 'Offer Tags'


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


class ServiceDays(Model):
    code_day = models.CharField(max_length=2, blank=True, null=True, default=None, unique=True)
    name_day = models.CharField(max_length=255, verbose_name='Day name', unique=True)

    def __str__(self):
        return '{} - {}'.format(self.code_day, self.name_day)

    class Meta:
        verbose_name = 'Day'
        verbose_name_plural = 'Days'


class Offers(Model):
    auth_shop = models.ForeignKey(AuthShop, on_delete=models.CASCADE,
                                  verbose_name='Auth Shop', related_name='auth_shop_offers')
    offer_type = models.CharField(verbose_name='Offer Type', max_length=1,
                                  choices=OfferChoices.OFFER_TYPE_CHOICES)
    offer_categories = models.ManyToManyField(Categories, verbose_name='Offer Categories',
                                              related_name='offer_categories')
    title = models.CharField(verbose_name='title', max_length=150, blank=False, null=False)
    picture_1 = models.ImageField(verbose_name='Picture 1', upload_to=get_shop_offers_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_2 = models.ImageField(verbose_name='Picture 2', upload_to=get_shop_offers_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_3 = models.ImageField(verbose_name='Picture 3', upload_to=get_shop_offers_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_4 = models.ImageField(verbose_name='Picture 4', upload_to=get_shop_offers_path, blank=True, null=True,
                                  default=None, max_length=1000)
    picture_1_thumbnail = models.ImageField(verbose_name='Picture 1 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_offers_path, max_length=1000)
    picture_2_thumbnail = models.ImageField(verbose_name='Picture 2 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_offers_path, max_length=1000)
    picture_3_thumbnail = models.ImageField(verbose_name='Picture 3 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_offers_path, max_length=1000)
    picture_4_thumbnail = models.ImageField(verbose_name='Picture 4 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_offers_path, max_length=1000)
    description = models.TextField(verbose_name='Description', null=True, blank=True)
    for_whom = models.ManyToManyField(ForWhom, verbose_name='For Whom',
                                      related_name='product_for_whom')
    creator_label = models.BooleanField(verbose_name='Creator label', default=False, blank=True, null=True)
    made_in_label = models.ForeignKey(Country, verbose_name='Made in', blank=True, null=True,
                                      related_name='country_offer',
                                      on_delete=models.SET_NULL, limit_choices_to={'type': PlaceType.COUNTRY})
    # made_in_label = models.CharField(verbose_name='Made in', max_length=150, default=None, blank=True, null=True)
    tags = models.ManyToManyField(OfferTags, verbose_name='Offer Tags', related_name='offer_tags', blank=True)
    price = models.FloatField(verbose_name='Price', default=0.0)
    pinned = models.BooleanField(verbose_name='Pinned ?', default=False)
    created_date = models.DateTimeField(verbose_name='Created date', editable=False, auto_now_add=True, db_index=True)
    updated_date = models.DateTimeField(verbose_name='Updated date', editable=False, auto_now=True)

    @property
    def property_extra_info(self):
        data = str(self.description)
        return (data[:50] + '..') if len(data) > 50 else data

    def __str__(self):
        offer_type = self.get_offer_type_display()
        if offer_type == 'Sell':
            offer_type = 'Produit'
        else:
            offer_type = 'Service'
        return '{} - {} - {}'.format(offer_type,
                                     self.title,
                                     self.price)

    class Meta:
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
        ordering = ('created_date',)

    @property
    def get_absolute_picture_1_img(self):
        if self.picture_1:
            return "{0}/media{1}".format(API_URL, self.picture_1.url)
        return None

    # @property
    # def get_absolute_picture_1_img_base64(self):
    #     if self.picture_1:
    #         try:
    #             _, file_extension = path.splitext(self.picture_1.path)
    #             encoded_string = b64encode(self.picture_1.file.read())
    #             return 'data:image/{};base64,{}'.format(str(file_extension).replace('.', ''),
    #                                                     str(encoded_string).lstrip("b'").rstrip("'"))
    #         except FileNotFoundError:
    #             return None
    #     return None

    @property
    def get_absolute_picture_1_thumbnail(self):
        if self.picture_1_thumbnail:
            return "{0}/media{1}".format(API_URL, self.picture_1_thumbnail.url)
        return None

    # @property
    # def get_absolute_picture_1_thumbnail_base64(self):
    #     if self.picture_1_thumbnail:
    #         try:
    #             _, file_extension = path.splitext(self.picture_1_thumbnail.path)
    #             encoded_string = b64encode(self.picture_1_thumbnail.file.read())
    #             return 'data:image/{};base64,{}'.format(str(file_extension).replace('.', ''),
    #                                                     str(encoded_string).lstrip("b'").rstrip("'"))
    #         except FileNotFoundError:
    #             return None
    #     return None

    @property
    def get_absolute_picture_2_img(self):
        if self.picture_2:
            return "{0}/media{1}".format(API_URL, self.picture_2.url)
        return None

    # @property
    # def get_absolute_picture_2_img_base64(self):
    #     if self.picture_2:
    #         try:
    #             _, file_extension = path.splitext(self.picture_2.path)
    #             encoded_string = b64encode(self.picture_2.file.read())
    #             return 'data:image/{};base64,{}'.format(str(file_extension).replace('.', ''),
    #                                                     str(encoded_string).lstrip("b'").rstrip("'"))
    #         except FileNotFoundError:
    #             return None
    #     return None

    @property
    def get_absolute_picture_2_thumbnail(self):
        if self.picture_2_thumbnail:
            return "{0}/media{1}".format(API_URL, self.picture_2_thumbnail.url)
        return None

    # @property
    # def get_absolute_picture_2_thumbnail_base64(self):
    #     if self.picture_2_thumbnail:
    #         try:
    #             _, file_extension = path.splitext(self.picture_2_thumbnail.path)
    #             encoded_string = b64encode(self.picture_2_thumbnail.file.read())
    #             return 'data:image/{};base64,{}'.format(str(file_extension).replace('.', ''),
    #                                                     str(encoded_string).lstrip("b'").rstrip("'"))
    #         except FileNotFoundError:
    #             return None
    #     return None

    @property
    def get_absolute_picture_3_img(self):
        if self.picture_3:
            return "{0}/media{1}".format(API_URL, self.picture_3.url)
        return None

    # @property
    # def get_absolute_picture_3_img_base64(self):
    #     if self.picture_3:
    #         try:
    #             _, file_extension = path.splitext(self.picture_3.path)
    #             encoded_string = b64encode(self.picture_3.file.read())
    #             return 'data:image/{};base64,{}'.format(str(file_extension).replace('.', ''),
    #                                                     str(encoded_string).lstrip("b'").rstrip("'"))
    #         except FileNotFoundError:
    #             return None
    #     return None

    @property
    def get_absolute_picture_3_thumbnail(self):
        if self.picture_3_thumbnail:
            return "{0}/media{1}".format(API_URL, self.picture_3_thumbnail.url)
        return None

    # @property
    # def get_absolute_picture_3_thumbnail_base64(self):
    #     if self.picture_3_thumbnail:
    #         try:
    #             _, file_extension = path.splitext(self.picture_3_thumbnail.path)
    #             encoded_string = b64encode(self.picture_3_thumbnail.file.read())
    #             return 'data:image/{};base64,{}'.format(str(file_extension).replace('.', ''),
    #                                                     str(encoded_string).lstrip("b'").rstrip("'"))
    #         except FileNotFoundError:
    #             return None
    #     return None

    @property
    def get_absolute_picture_4_img(self):
        if self.picture_4:
            return "{0}/media{1}".format(API_URL, self.picture_4.url)
        return None

    # @property
    # def get_absolute_picture_4_img_base64(self):
    #     if self.picture_4:
    #         try:
    #             _, file_extension = path.splitext(self.picture_4.path)
    #             encoded_string = b64encode(self.picture_4.file.read())
    #             return 'data:image/{};base64,{}'.format(str(file_extension).replace('.', ''),
    #                                                     str(encoded_string).lstrip("b'").rstrip("'"))
    #         except FileNotFoundError:
    #             return None
    #     return None

    @property
    def get_absolute_picture_4_thumbnail(self):
        if self.picture_4_thumbnail:
            return "{0}/media{1}".format(API_URL, self.picture_4_thumbnail.url)
        return None

    # @property
    # def get_absolute_picture_4_thumbnail_base64(self):
    #     if self.picture_4_thumbnail:
    #         try:
    #             _, file_extension = path.splitext(self.picture_4_thumbnail.path)
    #             encoded_string = b64encode(self.picture_4_thumbnail.file.read())
    #             return 'data:image/{};base64,{}'.format(str(file_extension).replace('.', ''),
    #                                                     str(encoded_string).lstrip("b'").rstrip("'"))
    #         except FileNotFoundError:
    #             return None
    #     return None

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.WEBP',
                                       ContentFile(image.getvalue()),
                                       save=True)


class Products(Model):
    offer = models.OneToOneField(Offers, on_delete=models.CASCADE,
                                 verbose_name='Offer', related_name='offer_products')
    product_colors = models.ManyToManyField(Colors, verbose_name='Product Colors',
                                            related_name='product_colors')
    product_sizes = models.ManyToManyField(Sizes, verbose_name='Product Sizes',
                                           related_name='product_sizes')
    product_quantity = models.PositiveIntegerField(verbose_name='Quantity', default=None, blank=True, null=True)
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
        return '{}'.format(self.offer.title)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ('-pk',)


class Services(Model):
    offer = models.OneToOneField(Offers, on_delete=models.CASCADE,
                                 verbose_name='Offer', related_name='offer_services')
    service_availability_days = models.ManyToManyField(ServiceDays, verbose_name='Opening days',
                                                       related_name='service_availability_days')
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
        return '{}'.format(self.offer.title)

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ('-pk',)


class Delivery(Model):
    offer = models.ForeignKey(Offers, on_delete=models.CASCADE,
                              verbose_name='Offer',
                              related_name='offer_delivery')
    delivery_city = models.ManyToManyField(City, verbose_name='Delivery City',
                                           related_name='delivery_city')
    all_cities = models.BooleanField(verbose_name='Tout le maroc ?', default=False)
    delivery_price = models.FloatField(verbose_name='Delivery Price', default=0.0)
    delivery_days = models.PositiveIntegerField(verbose_name='Number of Days', default=0)

    def __str__(self):
        return '{} - {} - {}'.format(self.offer.pk,
                                     self.delivery_price,
                                     self.delivery_days)

    class Meta:
        verbose_name = 'Delivery'
        verbose_name_plural = 'Deliveries'


class Solder(Model):
    offer = models.OneToOneField(Offers, on_delete=models.CASCADE,
                                 verbose_name='Offer',
                                 related_name='offer_solder', unique=True)
    solder_type = models.CharField(verbose_name='Solder type', choices=OfferChoices.SOLDER_BY_CHOICES,
                                   max_length=1)
    solder_value = models.FloatField(verbose_name='Solder value', default=0.0)

    def __str__(self):
        return "{} - {} - {}".format(self.offer.pk,
                                     self.solder_type,
                                     self.solder_value)

    class Meta:
        verbose_name = 'Solder'
        verbose_name_plural = 'Solder'


class OfferVue(Model):
    offer = models.OneToOneField(Offers, on_delete=models.SET_NULL,
                                 verbose_name='Offer',
                                 related_name='offer_vues', null=True)
    thumbnail = models.ImageField(verbose_name='Thumbnail', blank=True, null=True,
                                  upload_to=get_fallback_shop_offers_path, max_length=1000)
    title = models.CharField(verbose_name='title', max_length=150, blank=True, null=True, default=None)
    nbr_total_vue = models.PositiveIntegerField(verbose_name='Nbr Total Vue', default=0)

    def __str__(self):
        return "{} - {} - {}".format(self.offer.pk, self.title, self.nbr_total_vue)

    @property
    def get_absolute_thumbnail(self):
        if self.thumbnail:
            return "{0}/media{1}".format(API_URL, self.thumbnail.url)
        return None

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.WEBP',
                                       ContentFile(image.getvalue()),
                                       save=True)

    class Meta:
        verbose_name = 'Offer Vue'
        verbose_name_plural = 'Offers Vues'


class OffersTotalVues(Model):
    auth_shop = models.ForeignKey(AuthShop, on_delete=models.CASCADE,
                                  verbose_name='AuthShop',
                                  related_name='authshop_total_vues')
    MONTH_CHOICES = (
        ('1', 'Janvier'),
        ('2', 'Février'),
        ('3', 'Mars'),
        ('4', 'Avril'),
        ('5', 'Mai'),
        ('6', 'Juin'),
        ('7', 'Juillet'),
        ('8', 'Août'),
        ('9', 'Septembre'),
        ('10', 'Octobre'),
        ('11', 'Novembre'),
        ('12', 'Décembre')
    )
    date = models.CharField(verbose_name='Date', max_length=2, choices=MONTH_CHOICES,
                            null=True, blank=True, default=None)
    nbr_total_vue = models.PositiveIntegerField(verbose_name='Nbr Total Vue', default=0)

    def __str__(self):
        return "{} - {} - {}".format(self.auth_shop.pk, self.nbr_total_vue,
                                     self.date)

    class Meta:
        verbose_name = 'Offer Total Vue'
        verbose_name_plural = 'Offers Total Vues'
        unique_together = (('auth_shop', 'date'),)
