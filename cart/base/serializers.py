from rest_framework import serializers
from cart.models import Cart
from cart.base.utils import GetCartPrices
from places.models import City
from offers.models import Delivery, Products
from account.models import CustomUser
from offers.base.serializers import BaseShopCitySerializer


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
    delivery_city = BaseShopCitySerializer(many=True, read_only=True)

    class Meta:
        model = Delivery
        fields = ['pk', 'delivery_city', 'delivery_price', 'delivery_days']


class BaseCartDetailsProductSerializer(serializers.Serializer):
    offer_max_quantity = serializers.IntegerField(source='offer.offer_products.product_quantity', allow_null=True)
    picked_color = serializers.CharField()
    picked_size = serializers.CharField()
    picked_quantity = serializers.IntegerField(allow_null=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseCartDetailsServiceSerializer(serializers.Serializer):
    picked_date = serializers.DateField()
    picked_hour = serializers.TimeField(format='%H:%M')

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# Used in cart pagination
class BaseCartDetailsListSerializer(serializers.Serializer):
    cart_pk = serializers.IntegerField(source='pk')
    offer_pk = serializers.IntegerField(source='offer.pk')
    offer_type = serializers.CharField(source='offer.offer_type')
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
    offer_max_quantity = serializers.IntegerField(source='offer.offer_products.product_quantity', allow_null=True)
    picked_color = serializers.CharField()
    picked_size = serializers.CharField()
    picked_quantity = serializers.IntegerField(allow_null=True)
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


class BaseSingleCartOneOrMultiOffersSerializer(serializers.Serializer):
    shop_pk = serializers.IntegerField(source='offer.auth_shop.pk')
    desktop_shop_name = serializers.CharField(source='offer.auth_shop.shop_name')
    shop_picture = serializers.CharField(source='offer.auth_shop.get_absolute_avatar_thumbnail')
    shop_link = serializers.CharField(source='offer.auth_shop.qaryb_link')
    offers_total_price = serializers.SerializerMethodField()
    cart_details = serializers.SerializerMethodField()
    click_and_collect = serializers.SerializerMethodField()
    deliveries = serializers.SerializerMethodField()

    @staticmethod
    def get_deliveries(instance):
        delivery_instance = Delivery.objects.filter(offer=instance.offer.pk)
        deliveries = BaseCartDeliverySerializer(delivery_instance, many=True)
        if len(deliveries.data) == 0:
            return []
        return deliveries.data

    @staticmethod
    def get_click_and_collect(instance):
        try:
            click_and_collect_instance = Products.objects.get(offer=instance.offer.pk)
            click_and_collect = BaseCartClickAndCollectSerializer(click_and_collect_instance)
            product_longitude = click_and_collect.data.get('product_longitude', None)
            product_latitude = click_and_collect.data.get('product_latitude', None)
            product_address = click_and_collect.data.get('product_address', None)
            if product_longitude and product_latitude and product_address:
                return click_and_collect.data
            else:
                return {}
        except Products.DoesNotExist:
            return None

    def get_offers_total_price(self, instance):
        return self.context.get("total_price")

    @staticmethod
    def get_cart_details(instance):
        cart_details = BaseCartDetailsListSerializer(instance)
        return cart_details.data

    @staticmethod
    def get_offers_count(instance):
        shops = Cart.objects.filter(offer__auth_shop__pk=instance.offer.auth_shop.pk)
        return shops.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.offer.offer_type == 'S':
            del data['deliveries']
            del data['click_and_collect']
        return data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseCartOfferSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cart
        fields = ['pk', 'unique_id', 'offer', 'picked_color',
                  'picked_size', 'picked_quantity',
                  'picked_date', 'picked_hour']


# class BaseCartOfferPatchSerializer(serializers.ModelSerializer):
#     total_price = serializers.SerializerMethodField()
#
#     @staticmethod
#     def get_total_price(instance):
#         return GetCartPrices().get_offer_price(instance)
#
#     class Meta:
#         model = Cart
#         fields = [
#             'pk',
#             'picked_color',
#             'picked_size',
#             'picked_quantity',
#             'picked_date',
#             'picked_hour',
#             'total_price']
#         extra_kwargs = {
#             'total_price': {'read_only': True},
#         }


class BaseGetServicesCoordinatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'email']
