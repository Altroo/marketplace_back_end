from rest_framework import serializers
from temp_offer.base.models import TempOffers, TempDelivery, \
    TempSolder, TempProducts, TempServices
from auth_shop.models import Categories, Colors, Sizes, ForWhom, Days
from places.base.models import Cities


class BaseTempOfferCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['pk', 'code_category', 'name_category']


class BaseTempProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colors
        fields = ['pk', 'code_color', 'name_color']


class BaseTempProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sizes
        fields = ['pk', 'code_size', 'name_size']


class BaseTempServiceAvailabilityDaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Days
        fields = ['pk', 'code_day', 'name_day']


class BaseTempOfferForWhomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForWhom
        fields = ['pk', 'code_for_whom', 'name_for_whom']


# Offer serializer for Duplicate
class BaseTempShopOfferDuplicateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempOffers
        fields = ['temp_shop', 'offer_type', 'title',
                  'picture_1', 'picture_2', 'picture_3', 'picture_4',
                  'picture_1_thumbnail', 'picture_2_thumbnail', 'picture_3_thumbnail',
                  'picture_4_thumbnail', 'description', 'price']

    def save(self):
        temp_offer = TempOffers(
            temp_shop=self.validated_data['temp_shop'],
            offer_type=self.validated_data['offer_type'],
            title=self.validated_data['title'],
            picture_1=self.validated_data['picture_1'],
            picture_2=self.validated_data['picture_2'],
            picture_3=self.validated_data['picture_3'],
            picture_4=self.validated_data['picture_4'],
            picture_1_thumbnail=self.validated_data['picture_1_thumbnail'],
            picture_2_thumbnail=self.validated_data['picture_2_thumbnail'],
            picture_3_thumbnail=self.validated_data['picture_3_thumbnail'],
            picture_4_thumbnail=self.validated_data['picture_4_thumbnail'],
            description=self.validated_data['description'],
            price=self.validated_data['price'],
        )
        temp_offer.save()
        return temp_offer


# Global Offer serializer
class BaseTempShopOfferSerializer(serializers.ModelSerializer):
    offer_categories = BaseTempOfferCategoriesSerializer(many=True, read_only=True)
    for_whom = BaseTempOfferForWhomSerializer(many=True, read_only=True)

    class Meta:
        model = TempOffers
        fields = ['temp_shop', 'offer_type', 'offer_categories', 'title',
                  'picture_1', 'picture_2', 'picture_3', 'picture_4',
                  'description', 'for_whom', 'price']


# Global Product serializer
class BaseTempShopProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = TempProducts
        fields = ['temp_offer', 'product_quantity', 'product_price_by', 'product_longitude',
                  'product_latitude', 'product_address']


# Global Service serializer
class BaseTempShopServiceSerializer(serializers.ModelSerializer):
    service_availability_days = BaseTempServiceAvailabilityDaysSerializer(many=True, read_only=True)

    class Meta:
        model = TempServices
        fields = ['temp_offer', 'service_availability_days',
                  'service_morning_hour_from', 'service_morning_hour_to',
                  'service_afternoon_hour_from', 'service_afternoon_hour_to',
                  'service_zone_by', 'service_price_by',
                  'service_longitude', 'service_latitude', 'service_address']


class BaseTempShopCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Cities
        fields = ['pk', 'city_en', 'city_fr', 'city_ar']


class BaseTempShopDeliverySerializer(serializers.ModelSerializer):
    temp_delivery_city = BaseTempShopCitySerializer(many=True, read_only=True)

    class Meta:
        model = TempDelivery
        fields = ['temp_offer', 'temp_delivery_city', 'temp_delivery_price', 'temp_delivery_days']


class BaseDetailsTempProductSerializer(serializers.Serializer):
    # Details Product
    product_quantity = serializers.IntegerField()
    product_price_by = serializers.FloatField()
    product_longitude = serializers.CharField()
    product_latitude = serializers.CharField()
    product_address = serializers.CharField()
    product_colors = BaseTempProductColorSerializer(many=True, read_only=True)
    product_sizes = BaseTempProductSizeSerializer(many=True, read_only=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseDetailsTempServiceSerializer(serializers.Serializer):
    # Details Product
    service_availability_days = BaseTempServiceAvailabilityDaysSerializer(many=True, read_only=True)
    service_morning_hour_from = serializers.TimeField()
    service_morning_hour_to = serializers.TimeField()
    service_afternoon_hour_from = serializers.TimeField()
    service_afternoon_hour_to = serializers.TimeField()
    service_zone_by = serializers.CharField()
    service_price_by = serializers.CharField()
    service_longitude = serializers.CharField()
    service_latitude = serializers.CharField()
    service_address = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseTempOfferDetailsSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    title = serializers.CharField()
    categories = BaseTempOfferCategoriesSerializer(many=True, read_only=True)
    # Store_name
    store_name = serializers.CharField(source='temp_shop.shop_name')
    picture_1 = serializers.CharField(source='get_absolute_picture_1_img')
    picture_1_thumb = serializers.CharField(source='get_absolute_picture_1_thumbnail')
    picture_2 = serializers.CharField(source='get_absolute_picture_2_img')
    picture_2_thumb = serializers.CharField(source='get_absolute_picture_2_thumbnail')
    picture_3 = serializers.CharField(source='get_absolute_picture_3_img')
    picture_3_thumb = serializers.CharField(source='get_absolute_picture_3_thumbnail')
    picture_4 = serializers.CharField(source='get_absolute_picture_4_img')
    picture_4_thumb = serializers.CharField(source='get_absolute_picture_4_thumbnail')
    description = serializers.CharField()
    for_whom = BaseTempOfferForWhomSerializer(many=True, read_only=True)
    price = serializers.FloatField()
    # details product or details service
    details_offer = serializers.SerializerMethodField()
    deliveries = BaseTempShopDeliverySerializer(many=True, read_only=True)

    @staticmethod
    def get_details_offer(instance):
        if instance.offer_type == 'V':
            details_product = BaseDetailsTempProductSerializer(instance.temp_offer_products)
            return details_product.data
        if instance.offer_type == 'S':
            details_service = BaseDetailsTempServiceSerializer(instance.temp_offer_services)
            return details_service.data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseTempOfferssListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    thumbnail = serializers.SerializerMethodField()
    product_name = serializers.CharField()
    price = serializers.FloatField()
    temp_solder_type = serializers.CharField(source='temp_product_solder.temp_solder_type')
    temp_solder_value = serializers.FloatField(source='temp_product_solder.temp_solder_value')

    details_offer = serializers.SerializerMethodField()

    @staticmethod
    def get_details_offer(instance):
        if instance.offer_type == 'V':
            details_product = BaseDetailsTempProductSerializer(instance.temp_offer_products)
            return details_product.data
        if instance.offer_type == 'S':
            details_service = BaseDetailsTempServiceSerializer(instance.temp_offer_services)
            return details_service.data

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


class BaseTempOfferPutSerializer(serializers.ModelSerializer):
    picture_1 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)
    picture_2 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)
    picture_3 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)
    picture_4 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)

    class Meta:
        model = TempOffers
        fields = ['title', 'picture_1', 'picture_2', 'picture_3', 'picture_4',
                  'description', 'price']
        extra_kwargs = {
            'picture_1': {'required': False},
            'picture_2': {'required': False},
            'picture_3': {'required': False},
            'picture_4': {'required': False},
        }

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.picture_1 = validated_data.get('picture_1', instance.picture_1)
        instance.picture_2 = validated_data.get('picture_2', instance.picture_2)
        instance.picture_3 = validated_data.get('picture_3', instance.picture_3)
        instance.picture_4 = validated_data.get('picture_4', instance.picture_4)
        instance.description = validated_data.get('description', instance.description)
        instance.price = validated_data.get('price', instance.price)
        instance.save()
        return instance


class BaseTempProductPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempProducts
        fields = ['product_quantity', 'product_price_by', 'product_longitude', 'product_latitude', 'product_address']

    def update(self, instance, validated_data):
        instance.product_quantity = validated_data.get('product_quantity', instance.product_quantity)
        instance.product_price_by = validated_data.get('product_price_by', instance.product_price_by)
        instance.product_longitude = validated_data.get('product_longitude', instance.product_longitude)
        instance.product_latitude = validated_data.get('product_latitude', instance.product_latitude)
        instance.product_address = validated_data.get('product_address', instance.product_address)
        instance.save()
        return instance


class BaseTempServicePutSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempServices
        fields = ['service_morning_hour_from', 'service_morning_hour_to',
                  'service_afternoon_hour_from', 'service_afternoon_hour_to',
                  'service_zone_by', 'service_price_by',
                  'service_longitude', 'service_latitude', 'service_address']

    def update(self, instance, validated_data):
        instance.service_morning_hour_from = validated_data.get('service_morning_hour_from',
                                                                instance.service_morning_hour_from)
        instance.service_morning_hour_to = validated_data.get('service_morning_hour_to',
                                                              instance.service_morning_hour_to)
        instance.service_afternoon_hour_from = validated_data.get('service_afternoon_hour_from',
                                                                  instance.service_afternoon_hour_from)
        instance.service_afternoon_hour_to = validated_data.get('service_afternoon_hour_to',
                                                                instance.service_afternoon_hour_to)
        instance.service_zone_by = validated_data.get('service_zone_by', instance.service_zone_by)
        instance.service_price_by = validated_data.get('service_price_by', instance.service_price_by)
        instance.service_longitude = validated_data.get('service_longitude', instance.service_longitude)
        instance.service_latitude = validated_data.get('service_latitude', instance.service_latitude)
        instance.service_address = validated_data.get('service_address', instance.service_address)
        instance.save()
        return instance


class BaseTempShopOfferSolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempSolder
        fields = ['temp_offer', 'temp_solder_type', 'temp_solder_value']

    def save(self):
        temp_solder = TempSolder(
            temp_offer=self.validated_data['temp_offer'],
            temp_solder_type=self.validated_data['temp_solder_type'],
            temp_solder_value=self.validated_data['temp_solder_value'],
        )
        temp_solder.save()
        return temp_solder


class BaseTempShopOfferSolderPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempSolder
        fields = ['temp_solder_type', 'temp_solder_value']

    def update(self, instance, validated_data):
        instance.temp_solder_type = validated_data.get('temp_solder_type', instance.temp_solder_type)
        instance.temp_solder_value = validated_data.get('temp_solder_value', instance.temp_solder_value)
        instance.save()
        return instance
