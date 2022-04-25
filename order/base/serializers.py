from rest_framework import serializers
from offer.base.models import Solder
from order.base.models import Order, OrderDetails


class BaseNewOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['buyer', 'seller', 'order_number', 'order_date', 'order_status', 'unique_id']


# For naming convention
# TODO include services
class BaseTempOrdersListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    # TODO Avatar needs to be dynamic between buyer and seller
    avatar = serializers.CharField(source='buyer.get_absolute_avatar_thumbnail')
    first_name = serializers.CharField(source='buyer.first_name')
    last_name = serializers.CharField(source='buyer.last_name')
    title = serializers.CharField()
    total_price = serializers.SerializerMethodField()
    order_status = serializers.CharField()
    order_date = serializers.DateTimeField()
    viewed_buyer = serializers.BooleanField()

    # @staticmethod
    # def get_offer_name(instance):
    #     order_detail = OrderDetails.objects.filter(order=instance.pk)
    #     if len(order_detail) == 1:
    #         try:
    #             return order_detail[0].offer.title
    #         except AttributeError:
    #             return "Supprimer par le vendeur"
    #     return "{} articles".format(len(order_detail))

    @staticmethod
    def get_total_price(instance):
        order_detail = OrderDetails.objects.filter(order=instance.pk)
        if len(order_detail) == 1:
            return order_detail[0].total_self_price
        price = 0
        for i in order_detail:
            price += i.total_self_price
        return price

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseOferDetailsProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = [
            'order', 'offer', 'title',
            # Seller offer details
            # Picked click and collect
            'picked_click_and_collect',
            'product_longitude', 'product_latitude', 'product_address',
            # Picked delivery
            'picked_delivery',
            'delivery_city', 'delivery_price', 'delivery_days',
            # Buyer coordinates
            'first_name', 'last_name', 'address', 'city', 'zip_code', 'country', 'phone',
            # Both product & service
            'note',
            # Product
            'picked_color', 'picked_size', 'picked_quantity',
            # Service
            'picked_date', 'picked_hour',
            'total_self_price'
        ]


class BaseOfferDetailsServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = [
            'order',
            'offer',
            'title',
            'service_zone_by',
            'service_longitude',
            'service_latitude',
            'service_address',
            'service_km_radius',
            # Buyer coordinates
            'first_name', 'last_name', 'address', 'city', 'zip_code', 'country', 'phone',
            # Srvices
            'note',
            'picked_date', 'picked_hour',
            'total_self_price'
        ]


class BaseDetailsOrderProductSerializer(serializers.Serializer):
    title = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseDetailsOrderServiceSerializer(serializers.Serializer):
    title = serializers.CharField()
    price = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    # TODO check if price might include x quantity
    @staticmethod
    def get_price(instance):
        try:
            solder = Solder.objects.get(offer=instance.offer.pk)
            # Réduction fix
            if solder.solder_type == 'F':
                offer_price = instance.offer.price - solder.solder_value
            # Réduction Pourcentage
            else:
                offer_price = instance.offer.price - (instance.offer.price * solder.solder_value / 100)
            return offer_price * instance.picked_quantity
        except Solder.DoesNotExist:
            return instance.offer.price * instance.picked_quantity

    # TODO include thumbnail offer may gets null
    @staticmethod
    def get_thumbnail(instance):
        return instance.offer.get_absolute_picture_1_img

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseOrderDetailsTypeListSerializer(serializers.Serializer):
    # Can include multiple products / multiple services / mixed products + services
    order_details = serializers.SerializerMethodField()

    # TODO offer might get null and won't return offer_type
    @staticmethod
    def get_order_details(instance):
        # order product details
        if instance.offer.offer_type == 'V':
            details_product = BaseDetailsOrderProductSerializer(instance)
            return details_product.data
        # order service details
        if instance.offer.offer_type == 'S':
            details_service = BaseDetailsOrderServiceSerializer(instance)
            return details_service.data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# Include mixed multiple orders (Products + Services)
class BaseOrderDetailsListSerializer(serializers.Serializer):
    # From Order model :
    # Buer name or seller shop name (check order type)
    order_initiator_name = serializers.SerializerMethodField()
    order_number = serializers.SerializerMethodField()
    order_date = serializers.SerializerMethodField()
    order_status = serializers.SerializerMethodField()
    # From Order details model :
    order_details = BaseOrderDetailsTypeListSerializer(many=True)
    # Order details ID
    # Title
    # If product show :
    # Offer thumbnail 1
    # Price by quantity - solder ?
    # Picked color
    # Picked size
    # Picked quantity
    # If service show :
    # picked date
    # picked hour
    # Note
    # Check picked_click and collect if true show only :
    # Show product longitude
    # Show product_latitude
    # Show product_address
    # If service show :
    # Price - solder ?
    # service by sector, address
    # if sector add km range
    # else add service longitude + service latitde + service_address
    # else show buyer coordinates:
    # Fist_name
    # Last_name
    # address
    # city
    # zip_code
    # country
    # phone
    # Total needs to be calculated separately

    def get_order_initiator_name(self, instance):
        if self.context.get("order_type") == "buy":
            return instance.order.seller.shop_name
        return instance.order.buyer.first_name + ' ' + instance.order.buyer.last_name

    @staticmethod
    def get_order_number(instance):
        return instance.order.order_number

    @staticmethod
    def get_order_date(instance):
        return instance.order.order_date

    @staticmethod
    def get_order_status(instance):
        return instance.order.order_status

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

