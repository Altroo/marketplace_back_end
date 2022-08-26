from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Model
from account.models import CustomUser
from shop.models import AuthShop, LonLatValidators
from offers.models import OfferChoices, Offers
from Qaryb_API.settings import API_URL
from django.utils.translation import gettext_lazy as _
from os import path
from uuid import uuid4
from io import BytesIO


def get_fallback_shop_avatar_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('media/fallback_shop_avatars/', str(uuid4()) + file_extension)


def get_fallback_shop_offers_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('media/fallback_shop_offers/', str(uuid4()) + file_extension)


def get_fallback_avatar_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('media/fallback_user_avatars/', str(uuid4()) + file_extension)


class Order(Model):
    buyer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                              verbose_name='Buyer', related_name='order_buyer', null=True, blank=True)
    seller = models.ForeignKey(AuthShop, on_delete=models.SET_NULL,
                               verbose_name='Seller', related_name='order_seller', null=True, blank=True)
    # Fallback needed + add avatar thumbnail
    # Buyer
    first_name = models.CharField(_('first name'), max_length=30, blank=True, null=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True, null=True)
    buyer_avatar_thumbnail = models.ImageField(verbose_name='Buyer Thumb Avatar', upload_to=get_fallback_avatar_path,
                                               blank=True, null=True, default=None)
    # Seller
    shop_name = models.CharField(verbose_name='Shop name', max_length=150, blank=True, null=True)
    seller_avatar_thumbnail = models.ImageField(verbose_name='Avatar thumbnail',
                                                upload_to=get_fallback_shop_avatar_path, blank=True, null=True,
                                                default=None)
    note = models.CharField(verbose_name='Note', max_length=300, default=None, null=True, blank=True)
    # TODO 1 Add highest delivery price
    # TIMESTAMP[0:4]-UID
    # 4566-MQ
    order_number = models.CharField(verbose_name='Order number', max_length=255, unique=True)
    order_date = models.DateTimeField(verbose_name='Order date', editable=False,
                                      auto_now_add=True, db_index=True)
    # ORDER_STATUS_CHOICES = (
    #     ('TC', 'To confirm'),
    #     ('OG', 'On-going'),
    #     ('SH', 'Shipped'),
    #     ('RD', 'Ready'),
    #     ('TE', 'To evaluate'),
    #     ('CM', 'Completed'),
    #     ('CB', 'Canceled by buyer'),
    #     ('CS', 'Canceled by seller'),
    # )
    # order_status = models.CharField(verbose_name='Order Status', max_length=2,
    #                                 choices=ORDER_STATUS_CHOICES, default='TC')
    highest_delivery_price = models.FloatField(verbose_name='Highest delivery price', blank=True, null=True)
    viewed_buyer = models.BooleanField(default=False)
    viewed_seller = models.BooleanField(default=False)

    def get_absolute_order_thumbnail(self, order_type):
        if order_type == 'buy':
            if self.buyer_avatar_thumbnail:
                return "{0}/media{1}".format(API_URL, self.buyer_avatar_thumbnail.url)
        else:
            if self.buyer_avatar_thumbnail:
                return "{0}/media{1}".format(API_URL, self.buyer_avatar_thumbnail.url)
        return None

    def __str__(self):
        return 'Buyer : {} - Seller : {}'.format(self.buyer.email, self.seller.shop_name)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ('-order_date',)

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.jpg',
                                       ContentFile(image.getvalue()),
                                       save=True)


class OrderDetails(Model):
    # Even if cascade API doesn't offer The possibility to delete the order
    # But it offers to delete account
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              verbose_name='Order', related_name='order_details_order', null=True, blank=True)
    offer = models.ForeignKey(Offers, on_delete=models.SET_NULL,
                              verbose_name='Offer', related_name='order_details_offer', null=True, blank=True)
    # Offer fallback if deleted
    offer_type = models.CharField(verbose_name='Offer Type', max_length=1,
                                  choices=OfferChoices.OFFER_TYPE_CHOICES, blank=True, null=True)
    title = models.CharField(verbose_name='title', max_length=150, blank=True, null=True)
    offer_thumbnail = models.ImageField(verbose_name='Offer thumbnail', blank=True, null=True,
                                        upload_to=get_fallback_shop_offers_path, max_length=1000)
    # Seller offer details
    picked_click_and_collect = models.BooleanField(verbose_name='Click and collect', default=False)
    product_longitude = models.FloatField(verbose_name='Product longitude', max_length=10,
                                          validators=[LonLatValidators.long_validator], default=False)
    product_latitude = models.FloatField(verbose_name='Product latitude', max_length=10,
                                         validators=[LonLatValidators.lat_validator], default=False)
    product_address = models.CharField(verbose_name='product_address', max_length=255, default=False)
    picked_delivery = models.BooleanField(verbose_name='Delivery', default=False)
    delivery_price = models.FloatField(verbose_name='Delivery price', blank=True, null=True)
    new_delivery_price = models.FloatField(verbose_name='New Delivery price', blank=True, null=True)
    NEW_DELIVERY_PRICE_REASON_CHOICES = (
        ('P', 'Weight is greater'),
        # Get from body text (new_delivery_price_body)
        ('O', 'Other'),
        ('', 'Unset'),
    )
    new_delivery_price_reason = models.CharField(verbose_name='New delivery price reason', max_length=1,
                                                 choices=NEW_DELIVERY_PRICE_REASON_CHOICES, default='',
                                                 null=True, blank=True)
    new_delivery_price_body = models.CharField(verbose_name='New delivery price body', max_length=255,
                                               blank=True, null=True, default=None)
    # Buyer coordinates
    # Products only
    address = models.CharField(verbose_name='Address', max_length=300, blank=True, null=True)
    city = models.CharField(verbose_name='City', max_length=30, blank=True, null=True)
    zip_code = models.PositiveIntegerField(verbose_name='Zip code', blank=True, null=True)
    country = models.CharField(verbose_name='Country', max_length=30, blank=True, null=True)
    # Global both Products and services
    first_name = models.CharField(verbose_name='First name', max_length=30, blank=True, null=True)
    last_name = models.CharField(verbose_name='Last name', max_length=30, blank=True, null=True)
    phone = models.CharField(verbose_name='Phone number', max_length=15, blank=True, null=True)
    email = models.EmailField(verbose_name='email address', blank=True, null=True)
    # Product
    picked_color = models.CharField(verbose_name='Picked Color', max_length=255, default=None, null=True, blank=True)
    picked_size = models.CharField(verbose_name='Picked Size', max_length=255, default=None, null=True, blank=True)
    picked_quantity = models.PositiveIntegerField(verbose_name='Quantity', default=1)
    # Service
    picked_date = models.DateField(verbose_name='Picked Date', default=None, null=True, blank=True)
    picked_hour = models.TimeField(verbose_name='Picked Hour', default=None, null=True, blank=True)
    # Original service location
    service_zone_by = models.CharField(verbose_name='Zone by', max_length=1, choices=OfferChoices.ZONE_BY_CHOICES,
                                       default='A')
    # service_price_by = models.CharField(verbose_name='Price by', choices=OfferChoices.SERVICE_PRICE_BY_CHOICES,
    #                                     max_length=1)
    service_longitude = models.FloatField(verbose_name='Service Longitude', blank=True,
                                          null=True, max_length=10, validators=[LonLatValidators.long_validator],
                                          default=None)
    service_latitude = models.FloatField(verbose_name='Service Latitude', blank=True,
                                         null=True, max_length=10,
                                         validators=[LonLatValidators.lat_validator], default=None)
    service_address = models.CharField(verbose_name='Service Address', max_length=255,
                                       blank=True, null=True, default=None)
    service_km_radius = models.FloatField(verbose_name='Km radius', blank=True, null=True, default=None)
    total_self_price = models.FloatField(verbose_name='Total self price', default=0.0)

    ORDER_STATUS_CHOICES = (
        # A confirmer
        ('TC', 'To confirm'),
        # Delivery price adjusted
        ('DP', 'Delivery price'),
        # Preparation en cours
        ('OG', 'On-going'),
        # Expidée
        ('SH', 'Shipped'),
        # Prête
        ('RD', 'Ready'),
        # A évaluer
        ('TE', 'To evaluate'),
        # Terminée
        ('CM', 'Completed'),
        # Annuler par le vendeur
        ('CB', 'Canceled by buyer'),
        # Annuler par l'acheteur
        ('CS', 'Canceled by seller'),
    )
    order_status = models.CharField(verbose_name='Order Status', max_length=2,
                                    choices=ORDER_STATUS_CHOICES, default='TC')

    SELLER_CANCELED_REASON_CHOICES = (
        ('S', 'No more stock'),
        ('I', 'Not available'),
        # Get from body text (seller_cancel_body)
        ('O', 'Other'),
        ('', 'Unset'),
    )
    seller_canceled_reason = models.CharField(verbose_name='Seller canceled', max_length=1,
                                              choices=SELLER_CANCELED_REASON_CHOICES, default='',
                                              null=True, blank=True)
    seller_cancel_body = models.CharField(verbose_name='Seller cancel body', max_length=255,
                                          blank=True, null=True, default=None)
    # TODO need to know if this is applied to each order detail
    # or to a grouped orders.
    has_buyer_rating = models.BooleanField(default=False)
    has_seller_rating = models.BooleanField(default=False)

    def __str__(self):
        try:
            buyer_first_name = self.order.buyer.first_name
        except AttributeError:
            buyer_first_name = self.order.first_name
        try:
            buyer_last_name = self.order.buyer.last_name
        except AttributeError:
            buyer_last_name = self.order.last_name
        try:
            seller_shop_name = self.order.seller.shop_name
        except AttributeError:
            seller_shop_name = self.order.shop_name
        return 'Pk : {} Buyer : {} {} - Seller : {}'.format(self.order.pk, buyer_first_name, buyer_last_name,
                                                            seller_shop_name)

    @property
    def get_absolute_offer_thumbnail(self):
        if self.offer_thumbnail:
            return "{0}/media{1}".format(API_URL, self.offer_thumbnail.url)
        return None

    class Meta:
        verbose_name = 'Order Details'
        verbose_name_plural = 'Order Details'
        ordering = ('-order__order_date',)

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.jpg',
                                       ContentFile(image.getvalue()),
                                       save=True)
