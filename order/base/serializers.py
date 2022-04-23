from rest_framework import serializers
from order.base.models import Order, OrderDetails


class BaseNewOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['buyer', 'seller', 'order_number', 'order_date', 'order_status']


# For naming convention
# TODO include services
class BaseTempOrdersListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    avatar = serializers.CharField(source='buyer.get_absolute_avatar_thumbnail')
    first_name = serializers.CharField(source='buyer.first_name')
    last_name = serializers.CharField(source='buyer.last_name')
    offer_name = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    order_status = serializers.CharField()
    order_date = serializers.DateTimeField()
    viewed_buyer = serializers.BooleanField()

    @staticmethod
    def get_offer_name(instance):
        # TODO get offer title if offer was removed
        order_detail = OrderDetails.objects.filter(order=instance.pk)
        if len(order_detail) == 1:
            try:
                return order_detail[0].offer.title
            except AttributeError:
                return "Supprimer par le vendeur"
        return "{} articles".format(len(order_detail))

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
            'order', 'offer',
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
