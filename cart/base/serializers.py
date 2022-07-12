from rest_framework import serializers
from cart.models import Cart
from cart.base.utils import GetCartPrices
from places.models import City
from offers.models import Delivery, Products
from order.models import Order, OrderDetails
from account.models import CustomUser


class BaseNewOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['buyer', 'seller',
                  # Buyer fallback if deleted
                  'first_name', 'last_name', 'buyer_avatar_thumbnail',
                  # Seller fallback if deleted
                  'shop_name', 'seller_avatar_thumbnail', 'note',
                  'order_number', 'order_date', 'order_status', 'highest_delivery_price']


class BaseNewOrderHighestDeliveryPrice(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['highest_delivery_price']

    def update(self, instance, validated_data):
        instance.highest_delivery_price = validated_data.get('highest_delivery_price', instance.highest_delivery_price)
        instance.save()
        return instance


class BaseOferDetailsProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = [
            'order',
            # Order Fallback if deleted
            # 'order_number', 'order_date', 'order_status', 'viewed_buyer', 'viewed_seller',
            # 'offer',
            # Offer Fallback if deleted
            'offer_type', 'title', 'offer_thumbnail',
            # Seller offer details
            # Picked click and collect
            'picked_click_and_collect',
            'product_longitude', 'product_latitude', 'product_address',
            # Picked delivery
            'picked_delivery',
            # 'delivery_city', 'delivery_price', 'delivery_days',
            'delivery_price',
            # Buyer coordinates
            'first_name', 'last_name', 'address', 'city', 'zip_code', 'country', 'phone', 'email',
            # Product
            'picked_color', 'picked_size', 'picked_quantity',
            'total_self_price'
        ]


class BaseOfferDetailsServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = [
            'order',
            # Offer Fallback if deleted
            'offer_type', 'title', 'offer_thumbnail',
            'service_zone_by',
            'service_longitude',
            'service_latitude',
            'service_address',
            'service_km_radius',
            # Buyer coordinates
            'first_name', 'last_name',
            # 'address', 'city', 'zip_code', 'country',
            'phone', 'email',
            # Srvices
            'picked_date', 'picked_hour',
            'total_self_price'
        ]


class BaseCartClickAndCollectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ['product_longitude', 'product_latitude', 'product_address']


class BaseShopCityOriginalKeysSerializer(serializers.ModelSerializer):
    city_fr = serializers.CharField(source='name_fr')

    class Meta:
        model = City
        fields = ['pk', 'city_fr']


class BaseCartDeliverySerializer(serializers.ModelSerializer):
    delivery_city = serializers.SerializerMethodField()

    @staticmethod
    def get_delivery_city(instance):
        return instance.delivery_city.values_list('name_fr', flat=True).all()

    class Meta:
        model = Delivery
        fields = ['delivery_city', 'delivery_price', 'delivery_days']


class BaseCartDetailsProductSerializer(serializers.Serializer):
    offer_max_quantity = serializers.IntegerField(source='offer.offer_products.product_quantity')
    picked_color = serializers.CharField()
    picked_size = serializers.CharField()
    picked_quantity = serializers.IntegerField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseCartDetailsServiceSerializer(serializers.Serializer):
    picked_date = serializers.DateField()
    picked_hour = serializers.TimeField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# Used in cart pagination
class BaseCartDetailsListSerializer(serializers.Serializer):
    cart_pk = serializers.IntegerField(source='pk')
    offer_pk = serializers.IntegerField(source='offer.pk')
    offer_picture = serializers.CharField(source='offer.get_absolute_picture_1_thumbnail')
    offer_title = serializers.CharField(source='offer.title')
    offer_price = serializers.SerializerMethodField()
    offer_details = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    @staticmethod
    def get_offer_details(instance):
        # Product
        if instance.offer.offer_type == 'V':
            details_product = BaseCartDetailsProductSerializer(instance)
            return details_product.data
        if instance.offer.offer_type == 'S':
            details_service = BaseCartDetailsServiceSerializer(instance)
            return details_service.data

    @staticmethod
    def get_offer_price(instance):
        return GetCartPrices().get_offer_price(instance)


class BaseCartDetailsProductDeliveriesSerializer(serializers.Serializer):
    offer_max_quantity = serializers.IntegerField(source='offer.offer_products.product_quantity')
    picked_color = serializers.CharField()
    picked_size = serializers.CharField()
    picked_quantity = serializers.IntegerField()
    click_and_collect = serializers.SerializerMethodField()
    deliveries = serializers.SerializerMethodField()

    @staticmethod
    def get_deliveries(instance):
        delivery_instance = Delivery.objects.filter(offer=instance.offer.pk)
        deliveries = BaseCartDeliverySerializer(delivery_instance, many=True)
        return deliveries.data

    @staticmethod
    def get_click_and_collect(instance):
        try:
            click_and_collect_instance = Products.objects.get(offer=instance.offer.pk)
            click_and_collect = BaseCartClickAndCollectSerializer(click_and_collect_instance)
            return click_and_collect.data
        except Products.DoesNotExist:
            return {}

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# class BaseCartOffersDetailsSerializer(serializers.Serializer):
#     cart_pk = serializers.IntegerField(source='pk')
#     offer_pk = serializers.IntegerField(source='offer.pk')
#     offer_picture = serializers.CharField(source='offer.get_absolute_picture_1_thumbnail')
#     offer_title = serializers.CharField(source='offer.title')
#     offer_price = serializers.SerializerMethodField()
#     offer_details = serializers.SerializerMethodField()
#
#     @staticmethod
#     def get_offer_details(instance):
#         # Product
#         if instance.offer.offer_type == 'V':
#             details_product = BaseCartDetailsProductDeliveriesSerializer(instance)
#             return details_product.data
#         if instance.offer.offer_type == 'S':
#             details_service = BaseCartDetailsServiceSerializer(instance)
#             return details_service.data
#
#     def update(self, instance, validated_data):
#         pass
#
#     def create(self, validated_data):
#         pass
#
#     @staticmethod
#     def get_offer_price(instance):
#         return GetCartPrices().get_offer_price(instance)


class BaseSingleCartOneOrMultiOffersSerializer(serializers.Serializer):
    total_price = serializers.SerializerMethodField()
    cart_details = serializers.SerializerMethodField()
    click_and_collect = serializers.SerializerMethodField()
    deliveries = serializers.SerializerMethodField()

    @staticmethod
    def get_deliveries(instance):
        delivery_instance = Delivery.objects.filter(offer=instance.offer.pk)
        deliveries = BaseCartDeliverySerializer(delivery_instance, many=True)
        return deliveries.data

    @staticmethod
    def get_click_and_collect(instance):
        try:
            click_and_collect_instance = Products.objects.get(offer=instance.offer.pk)
            click_and_collect = BaseCartClickAndCollectSerializer(click_and_collect_instance)
            return click_and_collect.data
        except Products.DoesNotExist:
            return {}

    def get_total_price(self, instance):
        return self.context.get("total_price")

    @staticmethod
    def get_cart_details(instance):
        cart_details = BaseCartDetailsListSerializer(instance)
        return cart_details.data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseCartOfferSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cart
        fields = ['pk', 'user', 'offer', 'picked_color',
                  'picked_size', 'picked_quantity', 'picked_date', 'picked_hour']


class BaseCartOfferPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['picked_color', 'picked_size', 'picked_quantity', 'picked_date', 'picked_hour']

    # def update(self, instance, validated_data):
    #     instance.picked_color = validated_data.get('picked_color', instance.picked_color)
    #     instance.picked_size = validated_data.get('picked_size', instance.picked_size)
    #     instance.picked_quantity = validated_data.get('picked_quantity', instance.picked_quantity)
    #     instance.picked_date = validated_data.get('picked_date', instance.picked_date)
    #     instance.picked_hour = validated_data.get('picked_hour', instance.picked_hour)
    #     instance.save()
    #     return instance


class BaseGetServicesCoordinatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'email']
