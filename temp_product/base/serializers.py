from rest_framework import serializers
from temp_product.base.models import TempProduct, TempDelivery
from auth_shop.models import Categories


class BaseTempShopCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ('pk', 'code_category', 'name_category')


class BaseTempShopProductSerializer(serializers.ModelSerializer):
    product_category = BaseTempShopCategorySerializer(many=True, read_only=True)

    class Meta:
        model = TempProduct
        fields = ['temp_shop', 'product_type', 'product_category', 'product_name',
                  'picture_1', 'picture_2', 'picture_3', 'picture_4', 'description',
                  'for_whom', 'product_color', 'product_size', 'quantity', 'price', 'price_by',
                  'shop_longitude', 'shop_latitude', 'shop_address']


class BaseTempShopDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = TempDelivery
        fields = ['temp_product', 'temp_delivery_city', 'temp_delivery_price']


class BaseTempProductClickAndCollectSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempProduct
        fields = ['shop_longitude', 'shop_latitude', 'shop_address']


class BaseTempProductDetailsSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    picture_1 = serializers.CharField(source='get_absolute_picture_1_img')
    picture_1_thumb = serializers.CharField(source='get_absolute_picture_1_thumbnail')
    picture_2 = serializers.CharField(source='get_absolute_picture_2_img')
    picture_2_thumb = serializers.CharField(source='get_absolute_picture_2_thumbnail')
    picture_3 = serializers.CharField(source='get_absolute_picture_3_img')
    picture_3_thumb = serializers.CharField(source='get_absolute_picture_3_thumbnail')
    picture_4 = serializers.CharField(source='get_absolute_picture_4_img')
    picture_4_thumb = serializers.CharField(source='get_absolute_picture_4_thumbnail')
    product_name = serializers.CharField()
    store_name = serializers.CharField(source='temp_shop.shop_name')
    # Product categories
    product_categories = BaseTempShopCategorySerializer(many=True, read_only=True, source='product_category')
    description = serializers.CharField()
    product_color = serializers.CharField()
    product_size = serializers.CharField()
    price = serializers.IntegerField()
    price_by = serializers.CharField()
    # click and collect
    click_and_collect = BaseTempProductClickAndCollectSerializer(source='*')
    # deliveries
    deliveries = BaseTempShopDeliverySerializer(many=True, read_only=True, source='temp_delivery_temp_product')

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseTempProductsListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    thumbnail = serializers.SerializerMethodField()
    product_name = serializers.CharField()
    price = serializers.IntegerField()

    @staticmethod
    def get_thumbnail(instance):
        if instance.picture_1_thumbnail:
            return instance.get_absolute_picture_1_thumbnail
        elif instance.picture_2_thumbnail:
            return instance.get_absolute_picture_2_thumbnail
        elif instance.picture_3_thumbnail:
            return instance.get_absolute_picture_3_thumbnail
        elif instance.picture_4_thumbnail:
            return instance.get_absolute_picture_4_thumbnail
        else:
            return None

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class TempProductPutSerializer(serializers.ModelSerializer):
    picture_1 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)
    picture_2 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)
    picture_3 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)
    picture_4 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)

    class Meta:
        model = TempProduct
        fields = ['product_name', 'picture_1', 'picture_2', 'picture_3', 'picture_4', 'description',
                  'for_whom', 'product_color', 'product_size', 'quantity', 'price', 'price_by',
                  'shop_longitude', 'shop_latitude', 'shop_address']
        extra_kwargs = {
            'picture_1': {'required': False},
            'picture_2': {'required': False},
            'picture_3': {'required': False},
            'picture_4': {'required': False},
        }

    def update(self, instance, validated_data):
        instance.product_name = validated_data.get('product_name', instance.product_name)
        instance.picture_1 = validated_data.get('picture_1', instance.picture_1)
        instance.picture_2 = validated_data.get('picture_2', instance.picture_2)
        instance.picture_3 = validated_data.get('picture_3', instance.picture_3)
        instance.picture_4 = validated_data.get('picture_4', instance.picture_4)
        instance.description = validated_data.get('description', instance.description)
        instance.for_whom = validated_data.get('for_whom', instance.for_whom)
        instance.product_color = validated_data.get('product_color', instance.product_color)
        instance.product_size = validated_data.get('product_size', instance.product_size)
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.price = validated_data.get('price', instance.price)
        instance.price_by = validated_data.get('price_by', instance.price_by)
        instance.shop_longitude = validated_data.get('shop_longitude', instance.shop_longitude)
        instance.shop_latitude = validated_data.get('shop_latitude', instance.shop_latitude)
        instance.shop_address = validated_data.get('shop_address', instance.shop_address)
        instance.save()
        return instance
