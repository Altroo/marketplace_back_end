from django.db import models
from django.db.models import Model
from account.models import CustomUser
from auth_shop.base.models import AuthShop, LonLatValidators
from offer.base.models import Offers, OfferChoices, get_shop_products_path
from Qaryb_API_new.settings import API_URL


class Order(Model):
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                              verbose_name='Buyer', related_name='order_buyer')
    seller = models.ForeignKey(AuthShop, on_delete=models.CASCADE,
                               verbose_name='Seller', related_name='order_seller')
    # TIMESTAMP[0:4]-UID
    # 4566-MQ
    order_number = models.CharField(verbose_name='Order number', max_length=255, unique=True)
    order_date = models.DateTimeField(verbose_name='Order date', editable=False,
                                      auto_now_add=True, db_index=True)
    ORDER_STATUS_CHOICES = (
        ('TC', 'To confirm'),
        ('OG', 'On-going'),
        ('SH', 'Shipped'),
        ('RD', 'Ready'),
        ('TE', 'To evaluate'),
        ('CM', 'Completed'),
        ('CB', 'Canceled by buyer'),
        ('CS', 'Canceled by seller'),
    )
    order_status = models.CharField(verbose_name='Order Status', max_length=2,
                                    choices=ORDER_STATUS_CHOICES, default='TC')
    viewed = models.BooleanField(default=False)
    viewed_seller = models.BooleanField(default=False)

    def __str__(self):
        return 'Buyer : {} - Seller : {}'.format(self.buyer.email, self.seller.shop_name)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ('-order_date',)


class OrderDetails(Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL,
                              verbose_name='Order', related_name='order_details_order', null=True, blank=True)
    offer = models.ForeignKey(Offers, on_delete=models.SET_NULL,
                              verbose_name='Offer', related_name='order_details_offer', null=True, blank=True)
    title = models.CharField(verbose_name='title', max_length=150, blank=False, null=False)
    offer_thumbnail = models.ImageField(verbose_name='Offer thumbnail', blank=True, null=True,
                                            upload_to=get_shop_products_path, max_length=1000)
    offer_type = models.CharField(verbose_name='Offer Type', max_length=1,
                                  choices=OfferChoices.OFFER_TYPE_CHOICES)
    # Seller offer details
    picked_click_and_collect = models.BooleanField(verbose_name='Click and collect', default=False)
    product_longitude = models.FloatField(verbose_name='Product longitude', max_length=10,
                                          validators=[LonLatValidators.long_validator], default=False)
    product_latitude = models.FloatField(verbose_name='Product latitude', max_length=10,
                                         validators=[LonLatValidators.lat_validator], default=False)
    product_address = models.CharField(verbose_name='product_address', max_length=255, default=False)
    picked_delivery = models.BooleanField(verbose_name='Delivery', default=False)
    delivery_city = models.CharField(verbose_name='Delivery city', max_length=255)
    delivery_price = models.FloatField(verbose_name='Delivery price')
    delivery_days = models.PositiveIntegerField(verbose_name='Number of Days', default=0)
    # Buyer coordinates
    first_name = models.CharField(verbose_name='First name', max_length=30)
    last_name = models.CharField(verbose_name='Last name', max_length=30)
    address = models.CharField(verbose_name='Address', max_length=300)
    city = models.CharField(verbose_name='City', max_length=30)
    zip_code = models.PositiveIntegerField(verbose_name='Zip code')
    country = models.CharField(verbose_name='Country', max_length=30)
    phone = models.CharField(verbose_name='Phone number', max_length=15)
    # Both product & service
    note = models.CharField(verbose_name='Note', max_length=300, default=None, null=True, blank=True)
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
    total_self_price = models.FloatField(verbose_name='Total self price', default=0.0)
    OFFER_CANCELED_STATUS_CHOICES = (
        ('CB', 'Canceled by buyer'),
        ('CS', 'Canceled by seller'),
    )
    offer_canceled = models.CharField(verbose_name='Offer Canceled', max_length=2,
                                      choices=OFFER_CANCELED_STATUS_CHOICES, default=None,
                                      null=True, blank=True)

    def __str__(self):
        return 'Pk : {} Order : {} - Seller : {}'.format(self.order.pk, self.order.buyer.email,
                                                         self.order.seller.shop_name)

    @property
    def get_absolute_offer_thumbnail(self):
        if self.offer_thumbnail:
            return "{0}/media{1}".format(API_URL, self.offer_thumbnail.url)
        return None

    class Meta:
        verbose_name = 'Order details'
        verbose_name_plural = 'Orders details'
        ordering = ('-order__order_date',)
