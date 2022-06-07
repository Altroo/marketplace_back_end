from rest_framework import serializers
from order.models import OrderDetails


# Model = Order
class BaseOrdersListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    avatar = serializers.SerializerMethodField()
    initiator_name = serializers.SerializerMethodField()
    offer_title = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    order_status = serializers.CharField()
    order_date = serializers.DateTimeField()
    viewed = serializers.SerializerMethodField()

    def get_avatar(self, instance):
        if self.context.get('order_type') == 'buy':
            try:
                return instance.buyer.get_absolute_avatar_thumbnail
            except AttributeError:
                return instance.get_absolute_order_thumbnail('buy')
        try:
            return instance.seller.get_absolute_avatar_thumbnail
        except AttributeError:
            return instance.get_absolute_order_thumbnail('sell')

    def get_initiator_name(self, instance):
        if self.context.get('order_type') == 'buy':
            try:
                return instance.buyer.first_name + ' ' + instance.buyer.last_name
            except AttributeError:
                return instance.first_name + ' ' + instance.last_name
        try:
            return instance.seller.shop_name
        except AttributeError:
            return instance.shop_name

    @staticmethod
    def get_offer_title(instance):
        order_detail = OrderDetails.objects.filter(order=instance.pk)
        orders_len = len(order_detail)
        if orders_len == 1:
            title = order_detail[0].title
            return (title[:30] + '..') if len(title) > 30 else title
        return "{} articles".format(orders_len)

    @staticmethod
    def get_total_price(instance):
        order_detail = OrderDetails.objects.filter(order=instance.pk)
        if len(order_detail) == 1:
            return order_detail[0].total_self_price
        price = 0
        for i in order_detail:
            price += i.total_self_price
        return price

    def get_viewed(self, instance):
        if self.context.get("order_type") == "buy":
            return instance.viewed_buyer
        return instance.viewed_seller

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseClickAndCollectSerializer(serializers.Serializer):
    longitude = serializers.FloatField(source='product_longitude')
    latitude = serializers.FloatField(source='product_latitude')
    address = serializers.CharField(source='product_address')

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseDeliverySerializer(serializers.Serializer):
    price = serializers.FloatField(source='delivery_price')

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# Dynamic for BaseOrderDetailsTypeListSerializer
class BaseDetailsOrderProductSerializer(serializers.Serializer):
    thumbnail = serializers.CharField(source='get_absolute_offer_thumbnail')
    title = serializers.CharField()
    price = serializers.FloatField(source='total_self_price')
    picked_color = serializers.CharField()
    picked_size = serializers.CharField()
    picked_quantity = serializers.IntegerField()
    click_and_collect = serializers.SerializerMethodField()
    delivery = serializers.SerializerMethodField()

    @staticmethod
    def get_click_and_collect(instance):
        if instance.picked_click_and_collect:
            click_and_collect = BaseClickAndCollectSerializer(instance)
            return click_and_collect.data
        return None

    @staticmethod
    def get_delivery(instance):
        if instance.picked_delivery:
            delivery = BaseDeliverySerializer(instance)
            return delivery.data
        return None

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# Dynamic for BaseOrderDetailsTypeListSerializer
class BaseDetailsOrderServiceSerializer(serializers.Serializer):
    thumbnail = serializers.CharField(source='get_absolute_offer_thumbnail')
    title = serializers.CharField()
    price = serializers.FloatField(source='total_self_price')
    picked_date = serializers.DateField()
    picked_hour = serializers.TimeField()
    zone_by = serializers.CharField(source='service_zone_by')
    longitude = serializers.FloatField(source='service_longitude')
    latitude = serializers.FloatField(source='service_latitude')
    address = serializers.CharField(source='service_address')
    km_radius = serializers.FloatField(source='service_km_radius')

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# Dynamic for BaseOrderDetailsListSerializer
class BaseOrderDetailsTypeListSerializer(serializers.Serializer):
    # Can include multiple products / multiple services / mixed products + services
    order_details = serializers.SerializerMethodField()

    @staticmethod
    def get_order_details(instance):
        # We get from original offer_type case owner changed it
        # Order product details
        if instance.offer_type == 'V':
            details_product = BaseDetailsOrderProductSerializer(instance)
            return details_product.data
        # order service details
        if instance.offer_type == 'S':
            details_service = BaseDetailsOrderServiceSerializer(instance)
            return details_service.data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseBuyerCoordinatesSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    zip_code = serializers.IntegerField()
    country = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.EmailField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# Model = OrderDetails
class BaseOrderDetailsListSerializer(serializers.Serializer):
    # From Order model :
    # Buyer name or seller shop name (check order type)
    initiator_name = serializers.SerializerMethodField()
    order_number = serializers.SerializerMethodField()
    order_date = serializers.SerializerMethodField()
    order_status = serializers.SerializerMethodField()
    note = serializers.SerializerMethodField()
    # From Order details model :
    order_details = BaseOrderDetailsTypeListSerializer(many=True)
    buyer_coordinates = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    offer_canceled = serializers.CharField()

    def get_initiator_name(self, instance):
        if self.context.get("order_type") == "buy":
            try:
                return instance.order.seller.shop_name
            except AttributeError:
                return instance.order.shop_name
        try:
            return instance.order.buyer.first_name + ' ' + instance.order.buyer.last_name
        except AttributeError:
            return instance.order.first_name + ' ' + instance.order.last_name

    @staticmethod
    def get_order_number(instance):
        return instance.order.order_number

    @staticmethod
    def get_order_date(instance):
        return instance.order.order_date

    @staticmethod
    def get_order_status(instance):
        return instance.order.order_status

    @staticmethod
    def get_note(instance):
        return instance.order.note

    @staticmethod
    def get_total_price(instance):
        order_detail = OrderDetails.objects.filter(order=instance.order.pk)
        price = 0
        for i in order_detail:
            price += i.total_self_price
        return price

    @staticmethod
    def get_buyer_coordinates(instance):
        buyer_address = BaseBuyerCoordinatesSerializer(instance)
        return buyer_address.data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
