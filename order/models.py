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


# Left for old migrations
def get_fallback_shop_avatar_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('fallback_shop_avatars/', str(uuid4()) + file_extension)


def get_fallback_avatar_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('fallback_user_avatars/', str(uuid4()) + file_extension)
# ------------------------------------------------------------------------------------


# NEW
def get_buyer_avatar_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('orders/buyers_avatars/', str(uuid4()) + file_extension)


def get_fallback_shop_offers_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('fallback_shop_offers/', str(uuid4()) + file_extension)


class OrderChoices:
    ORDER_STATUS_CHOICES = (
        # Preparation en cours
        ('IP', 'In Progress'),
        # Terminée
        ('CM', 'Completed'),
        # Annuler par le vendeur
        ('CA', 'Canceled'),
    )


class Order(Model):
    seller = models.ForeignKey(AuthShop, on_delete=models.CASCADE, related_name='order_for_auth_shop',
                               blank=True, null=True)
    # buyer details
    # Duplicated in order details but this is used for the order list only.
    first_name = models.CharField(_('first name'), max_length=30, blank=True, null=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True, null=True)
    buyer_avatar_thumbnail = models.ImageField(verbose_name='Buyer Thumb Avatar',
                                               upload_to=get_buyer_avatar_path,
                                               blank=True, null=True, default=None)
    note = models.CharField(verbose_name='Remarque', max_length=300, default=None, null=True, blank=True)
    order_number = models.CharField(verbose_name='Order number', max_length=255, unique=True)
    order_date = models.DateTimeField(verbose_name='Order date',
                                      editable=False,
                                      auto_now_add=True,
                                      db_index=True)
    # 0 = gratuite
    highest_delivery_price = models.FloatField(verbose_name='Delivery price', default=0, blank=True, null=True)
    # offers prices * quantity (deliveries excluded)
    total_price = models.FloatField(verbose_name='Order total price', default=0, blank=True, null=True,
                                    help_text='all offers price (solder & quantity). deliveries excluded')
    order_status = models.CharField(verbose_name='Order Status', max_length=2,
                                    choices=OrderChoices.ORDER_STATUS_CHOICES, default='IP')

    @property
    def get_absolute_buyer_thumbnail(self):
        if self.buyer_avatar_thumbnail:
            return "{0}{1}".format(API_URL, self.buyer_avatar_thumbnail.url)
        return None

    def __str__(self):
        return 'Buyer : {} - Seller : {}'.format(f'{self.first_name} - {self.last_name}', self.seller.shop_name)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ('-order_date',)

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.WEBP',
                                       ContentFile(image.getvalue()),
                                       save=True)


class OrderDetails(Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              verbose_name='Order', related_name='order_details_order',
                              null=True,
                              blank=True)
    # Check if offer edited will show ordered an edited offer which is incorrect
    offer = models.ForeignKey(Offers, on_delete=models.SET_NULL,
                              verbose_name='Offer',
                              related_name='order_details_offer',
                              null=True,
                              blank=True)
    offer_type = models.CharField(verbose_name='Offer Type', max_length=1,
                                  choices=OfferChoices.OFFER_TYPE_CHOICES, default='V')
    offer_title = models.CharField(verbose_name='title', max_length=150, blank=True, null=True)
    offer_thumbnail = models.ImageField(verbose_name='Offer thumbnail', blank=True, null=True,
                                        upload_to=get_fallback_shop_offers_path, max_length=1000)
    # original offer price
    offer_price = models.FloatField(verbose_name='Price', default=0, blank=True, null=True)
    picked_click_and_collect = models.BooleanField(verbose_name='Click and collect', default=False)
    product_longitude = models.FloatField(verbose_name='Product longitude', max_length=10,
                                          validators=[LonLatValidators.long_validator], default=None, blank=True,
                                          null=True)
    product_latitude = models.FloatField(verbose_name='Product latitude', max_length=10,
                                         validators=[LonLatValidators.lat_validator], default=None, blank=True,
                                         null=True)
    product_address = models.CharField(verbose_name='product_address', max_length=255, default=None, blank=True,
                                       null=True)
    picked_delivery = models.BooleanField(verbose_name='Delivery', default=False)
    # prix livraison, 0 = gratuite
    delivery_price = models.FloatField(verbose_name='Delivery price', default=0, blank=True, null=True)
    # Buyer coordinates
    # Products only
    address = models.CharField(verbose_name='Address', max_length=300, blank=True, null=True, default=None)
    city = models.CharField(verbose_name='City', max_length=30, blank=True, null=True, default=None)
    zip_code = models.PositiveIntegerField(verbose_name='Zip code', blank=True, null=True, default=None)
    country = models.CharField(verbose_name='Country', max_length=30, blank=True, null=True, default=None)
    # Global both Products and services (first_name & last_name exist in parent model)
    phone = models.CharField(verbose_name='Phone number', max_length=15, blank=True, null=True, default=None)
    email = models.EmailField(verbose_name='email address', blank=True, null=True, default=None)
    # Product
    picked_color = models.CharField(verbose_name='Picked Color', max_length=255, default=None, null=True, blank=True)
    picked_size = models.CharField(verbose_name='Picked Size', max_length=255, default=None, null=True, blank=True)
    picked_quantity = models.PositiveIntegerField(verbose_name='Quantity', default=1)
    # Service
    picked_date = models.DateField(verbose_name='Picked Date', default=None, null=True, blank=True)
    picked_hour = models.TimeField(verbose_name='Picked Hour', default=None, null=True, blank=True)
    # Original service location
    service_zone_by = models.CharField(verbose_name='Zone by', max_length=1, choices=OfferChoices.ZONE_BY_CHOICES,
                                       default=None, blank=True, null=True)
    service_longitude = models.FloatField(verbose_name='Service Longitude', blank=True,
                                          null=True, max_length=10, validators=[LonLatValidators.long_validator],
                                          default=None)
    service_latitude = models.FloatField(verbose_name='Service Latitude', blank=True,
                                         null=True, max_length=10,
                                         validators=[LonLatValidators.lat_validator], default=None)
    service_address = models.CharField(verbose_name='Service Address', max_length=255,
                                       blank=True, null=True, default=None)
    service_km_radius = models.FloatField(verbose_name='Km radius', blank=True, null=True, default=13)

    def __str__(self):
        buyer_first_name = self.order.first_name
        buyer_last_name = self.order.last_name
        seller_shop_name = self.order.seller.shop_name
        return 'Pk : {} Buyer : {} {} - Seller : {}'.format(self.order.pk, buyer_first_name, buyer_last_name,
                                                            seller_shop_name)

    @property
    def get_absolute_offer_thumbnail(self):
        if self.offer_thumbnail:
            return "{0}{1}".format(API_URL, self.offer_thumbnail.url)
        return None

    class Meta:
        verbose_name = 'Order Details'
        verbose_name_plural = 'Order Details'
        ordering = ('-order__order_date',)

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.WEBP',
                                       ContentFile(image.getvalue()),
                                       save=True)
