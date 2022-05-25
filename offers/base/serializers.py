from rest_framework import serializers
from cart.base.models import Cart
from offers.base.models import Offers, Solder, Products, Services, \
    Categories, Colors, Sizes, ForWhom, ServiceDays, Delivery, OfferTags, \
    TempOffers, TempSolder, TempProducts, TempServices, TempDelivery
from places.base.models import City


class BaseOfferCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['pk', 'code_category', 'name_category']


class BaseOfferTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferTags
        fields = ['pk', 'name_tag']


class BaseProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colors
        fields = ['pk', 'code_color', 'name_color']


class BaseProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sizes
        fields = ['pk', 'code_size', 'name_size']


class BaseServiceAvailabilityDaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceDays
        fields = ['pk', 'code_day', 'name_day']


class BaseOfferForWhomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForWhom
        fields = ['pk', 'code_for_whom', 'name_for_whom']


# Offer serializer for Duplicate
class BaseShopOfferDuplicateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offers
        fields = ['auth_shop', 'offer_type', 'title',
                  'picture_1', 'picture_2', 'picture_3', 'picture_4',
                  'picture_1_thumbnail', 'picture_2_thumbnail', 'picture_3_thumbnail', 'picture_4_thumbnail',
                  'description', 'price']

    def save(self):
        offer = Offers(
            auth_shop=self.validated_data['auth_shop'],
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
        offer.save()
        return offer


# Global Offer serializer
class BaseShopOfferSerializer(serializers.ModelSerializer):
    offer_categories = BaseOfferCategoriesSerializer(many=True, read_only=True)
    for_whom = BaseOfferForWhomSerializer(many=True, read_only=True)
    tags = BaseOfferTagsSerializer(many=True, read_only=True)

    class Meta:
        model = Offers
        fields = ['auth_shop', 'offer_type', 'offer_categories', 'title',
                  'picture_1', 'picture_2', 'picture_3', 'picture_4',
                  'description', 'for_whom', 'creator_label', 'made_in_label',
                  'tags', 'price']


# Global Product serializer
class BaseShopProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Products
        fields = ['offer', 'product_quantity', 'product_price_by', 'product_longitude',
                  'product_latitude', 'product_address']


# Global Service serializer
class BaseShopServiceSerializer(serializers.ModelSerializer):
    service_availability_days = BaseServiceAvailabilityDaysSerializer(many=True, read_only=True)

    class Meta:
        model = Services
        fields = ['offer', 'service_availability_days',
                  'service_morning_hour_from', 'service_morning_hour_to',
                  'service_afternoon_hour_from', 'service_afternoon_hour_to',
                  'service_zone_by', 'service_price_by',
                  'service_longitude', 'service_latitude', 'service_address', 'service_km_radius']


class BaseShopCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        # Keept for the views output key names
        fields = ['pk', 'city_en', 'city_fr', 'city_ar']


class BaseShopOriginalCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        # Keept for the views output key names
        fields = ['pk', 'name_en', 'name_fr', 'name_ar']


class BaseShopDeliverySerializer(serializers.ModelSerializer):
    delivery_city = BaseShopCitySerializer(many=True, read_only=True)

    class Meta:
        model = Delivery
        fields = ['offer', 'delivery_city', 'delivery_price', 'delivery_days']


class BaseShopOriginalDeliverySerializer(serializers.ModelSerializer):
    delivery_city = BaseShopOriginalCitySerializer(many=True, read_only=True)

    class Meta:
        model = Delivery
        fields = ['pk', 'delivery_city', 'delivery_price', 'delivery_days']


class BaseDetailsProductSerializer(serializers.Serializer):
    # Details Product
    product_quantity = serializers.IntegerField()
    product_price_by = serializers.CharField()
    product_longitude = serializers.CharField()
    product_latitude = serializers.CharField()
    product_address = serializers.CharField()
    product_colors = BaseProductColorSerializer(many=True, read_only=True)
    product_sizes = BaseProductSizeSerializer(many=True, read_only=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseDetailsServiceSerializer(serializers.Serializer):
    # Details Product
    service_availability_days = BaseServiceAvailabilityDaysSerializer(many=True, read_only=True)
    service_morning_hour_from = serializers.TimeField()
    service_morning_hour_to = serializers.TimeField()
    service_afternoon_hour_from = serializers.TimeField()
    service_afternoon_hour_to = serializers.TimeField()
    service_zone_by = serializers.CharField()
    service_price_by = serializers.CharField()
    service_longitude = serializers.CharField()
    service_latitude = serializers.CharField()
    service_address = serializers.CharField()
    service_km_radius = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseOfferDetailsSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    title = serializers.CharField()
    categories = BaseOfferCategoriesSerializer(many=True, read_only=True)
    # shop_name
    shop_name = serializers.CharField(source='auth_shop.shop_name')
    picture_1 = serializers.CharField(source='get_absolute_picture_1_img')
    picture_1_thumb = serializers.CharField(source='get_absolute_picture_1_thumbnail')
    picture_2 = serializers.CharField(source='get_absolute_picture_2_img')
    picture_2_thumb = serializers.CharField(source='get_absolute_picture_2_thumbnail')
    picture_3 = serializers.CharField(source='get_absolute_picture_3_img')
    picture_3_thumb = serializers.CharField(source='get_absolute_picture_3_thumbnail')
    picture_4 = serializers.CharField(source='get_absolute_picture_4_img')
    picture_4_thumb = serializers.CharField(source='get_absolute_picture_4_thumbnail')
    description = serializers.CharField()
    for_whom = BaseOfferForWhomSerializer(many=True, read_only=True)
    # tags = BaseOfferTagsSerializer(many=True, read_only=True)
    creator_label = serializers.BooleanField()
    made_in_label = serializers.CharField()
    price = serializers.FloatField()
    # details product or details service
    details_offer = serializers.SerializerMethodField()
    offer_delivery = BaseShopOriginalDeliverySerializer(many=True)
    exist_in_cart = serializers.SerializerMethodField()

    def get_exist_in_cart(self, instance):
        user = self.context.get("user")
        try:
            if user.is_anonymous:
                return False
            Cart.objects.get(user=user, offer=instance.pk)
            return True
        except Cart.DoesNotExist:
            return False

    @staticmethod
    def get_details_offer(instance):
        if instance.offer_type == 'V':
            details_product = BaseDetailsProductSerializer(instance.offer_products)
            return details_product.data
        if instance.offer_type == 'S':
            details_service = BaseDetailsServiceSerializer(instance.offer_services)
            return details_service.data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseOffersListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    thumbnail = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='*')
    price = serializers.FloatField()
    solder_type = serializers.CharField(source='offer_solder.solder_type')
    solder_value = serializers.FloatField(source='offer_solder.solder_value')
    creator_label = serializers.BooleanField()
    details_offer = serializers.SerializerMethodField()

    @staticmethod
    def get_details_offer(instance):
        if instance.offer_type == 'V':
            details_product = BaseDetailsProductSerializer(instance.offer_products)
            return details_product.data
        if instance.offer_type == 'S':
            details_service = BaseDetailsServiceSerializer(instance.offer_services)
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


class BaseOfferPutSerializer(serializers.ModelSerializer):
    picture_1 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)
    picture_2 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)
    picture_3 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)
    picture_4 = serializers.ImageField(required=False, allow_empty_file=True,
                                       default=None, max_length=None, allow_null=True)

    class Meta:
        model = Offers
        fields = ['title', 'picture_1', 'picture_2', 'picture_3', 'picture_4',
                  'description', 'creator_label', 'made_in_label', 'price']
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
        instance.creator_label = validated_data.get('creator_label', instance.creator_label)
        instance.made_in_label = validated_data.get('made_in_label', instance.made_in_label)
        instance.price = validated_data.get('price', instance.price)
        instance.save()
        return instance


class BaseProductPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ['product_quantity', 'product_price_by', 'product_longitude', 'product_latitude', 'product_address']

    def update(self, instance, validated_data):
        instance.product_quantity = validated_data.get('product_quantity', instance.product_quantity)
        instance.product_price_by = validated_data.get('product_price_by', instance.product_price_by)
        instance.product_longitude = validated_data.get('product_longitude', instance.product_longitude)
        instance.product_latitude = validated_data.get('product_latitude', instance.product_latitude)
        instance.product_address = validated_data.get('product_address', instance.product_address)
        instance.save()
        return instance


class BaseServicePutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ['service_morning_hour_from', 'service_morning_hour_to',
                  'service_afternoon_hour_from', 'service_afternoon_hour_to',
                  'service_zone_by', 'service_price_by',
                  'service_longitude', 'service_latitude', 'service_address', 'service_km_radius']

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


class BaseShopOfferSolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solder
        fields = ['offer', 'solder_type', 'solder_value']

    def save(self):
        solder = Solder(
            offer=self.validated_data['offer'],
            solder_type=self.validated_data['solder_type'],
            solder_value=self.validated_data['solder_value'],
        )
        solder.save()
        return solder


class BaseShopOfferSolderPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solder
        fields = ['solder_type', 'solder_value']

    def update(self, instance, validated_data):
        instance.solder_type = validated_data.get('solder_type', instance.solder_type)
        instance.solder_value = validated_data.get('solder_value', instance.solder_value)
        instance.save()
        return instance


class BaseOffersVuesListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    thumbnail = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    nbr_total_vue = serializers.IntegerField(source='offer_vues.nbr_total_vue')

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
            return instance.offer_vues.get_absolute_thumbnail

    @staticmethod
    def get_title(instance):
        if instance.title:
            return instance.title
        else:
            return instance.offer_vues.title

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# Offer serializer for Duplicate
class BaseTempShopOfferDuplicateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempOffers
        fields = ['temp_shop', 'offer_type', 'title',
                  'picture_1', 'picture_2', 'picture_3', 'picture_4',
                  'picture_1_thumbnail', 'picture_2_thumbnail', 'picture_3_thumbnail', 'picture_4_thumbnail',
                  'description', 'price']

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
    offer_categories = BaseOfferCategoriesSerializer(many=True, read_only=True)
    for_whom = BaseOfferForWhomSerializer(many=True, read_only=True)
    tags = BaseOfferTagsSerializer(many=True, read_only=True)

    class Meta:
        model = TempOffers
        fields = ['temp_shop', 'offer_type', 'offer_categories', 'title',
                  'picture_1', 'picture_2', 'picture_3', 'picture_4',
                  'description', 'for_whom', 'tags', 'price']


# Global Product serializer
class BaseTempShopProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = TempProducts
        fields = ['temp_offer', 'product_quantity', 'product_price_by', 'product_longitude',
                  'product_latitude', 'product_address']


# Global Service serializer
class BaseTempShopServiceSerializer(serializers.ModelSerializer):
    service_availability_days = BaseServiceAvailabilityDaysSerializer(many=True, read_only=True)

    class Meta:
        model = TempServices
        fields = ['temp_offer', 'service_availability_days',
                  'service_morning_hour_from', 'service_morning_hour_to',
                  'service_afternoon_hour_from', 'service_afternoon_hour_to',
                  'service_zone_by', 'service_price_by',
                  'service_longitude', 'service_latitude', 'service_address', 'service_km_radius']


class BaseTempShopCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['pk', 'city_en', 'city_fr', 'city_ar']


class BaseTempShopDeliverySerializer(serializers.ModelSerializer):
    temp_delivery_city = BaseTempShopCitySerializer(many=True, read_only=True)

    class Meta:
        model = TempDelivery
        fields = ['temp_offer', 'temp_delivery_city', 'temp_delivery_price', 'temp_delivery_days']


# class BaseTempShopDeliveryPUTSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TempDelivery
#         fields = ['temp_delivery_city_1', 'temp_delivery_price_1', 'temp_delivery_days_1',
#                   'temp_delivery_city_2', 'temp_delivery_price_2', 'temp_delivery_days_2',
#                   'temp_delivery_city_3', 'temp_delivery_price_3', 'temp_delivery_days_3']
#
#     def update(self, instance, validated_data):
#         instance.temp_delivery_city_1 = validated_data.get('temp_delivery_city_1', instance.temp_delivery_city_1)
#         instance.temp_delivery_price_1 = validated_data.get('temp_delivery_price_1', instance.temp_delivery_price_1)
#         instance.temp_delivery_days_1 = validated_data.get('temp_delivery_days_1', instance.temp_delivery_days_1)
#         instance.temp_delivery_city_2 = validated_data.get('temp_delivery_city_2', instance.temp_delivery_city_2)
#         instance.temp_delivery_price_2 = validated_data.get('temp_delivery_price_2', instance.temp_delivery_price_2)
#         instance.temp_delivery_days_2 = validated_data.get('temp_delivery_days_2', instance.temp_delivery_days_2)
#         instance.temp_delivery_city_3 = validated_data.get('temp_delivery_city_3', instance.temp_delivery_city_3)
#         instance.temp_delivery_price_3 = validated_data.get('temp_delivery_price_3', instance.temp_delivery_price_3)
#         instance.temp_delivery_days_3 = validated_data.get('temp_delivery_days_3', instance.temp_delivery_days_3)
#         instance.save()
#         return instance


class BaseDetailsTempProductSerializer(serializers.Serializer):
    # Details Product
    product_quantity = serializers.IntegerField()
    product_price_by = serializers.CharField()
    product_longitude = serializers.CharField()
    product_latitude = serializers.CharField()
    product_address = serializers.CharField()
    product_colors = BaseProductColorSerializer(many=True, read_only=True)
    product_sizes = BaseProductSizeSerializer(many=True, read_only=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseDetailsTempServiceSerializer(serializers.Serializer):
    # Details Product
    service_availability_days = BaseServiceAvailabilityDaysSerializer(many=True, read_only=True)
    service_morning_hour_from = serializers.TimeField()
    service_morning_hour_to = serializers.TimeField()
    service_afternoon_hour_from = serializers.TimeField()
    service_afternoon_hour_to = serializers.TimeField()
    service_zone_by = serializers.CharField()
    service_price_by = serializers.CharField()
    service_longitude = serializers.CharField()
    service_latitude = serializers.CharField()
    service_address = serializers.CharField()
    service_km_radius = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseTempOfferDetailsSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    title = serializers.CharField()
    categories = BaseOfferCategoriesSerializer(many=True, read_only=True)
    # Shop_name
    shop_name = serializers.CharField(source='temp_shop.shop_name')
    picture_1 = serializers.CharField(source='get_absolute_picture_1_img')
    picture_1_thumb = serializers.CharField(source='get_absolute_picture_1_thumbnail')
    picture_2 = serializers.CharField(source='get_absolute_picture_2_img')
    picture_2_thumb = serializers.CharField(source='get_absolute_picture_2_thumbnail')
    picture_3 = serializers.CharField(source='get_absolute_picture_3_img')
    picture_3_thumb = serializers.CharField(source='get_absolute_picture_3_thumbnail')
    picture_4 = serializers.CharField(source='get_absolute_picture_4_img')
    picture_4_thumb = serializers.CharField(source='get_absolute_picture_4_thumbnail')
    description = serializers.CharField()
    for_whom = BaseOfferForWhomSerializer(many=True, read_only=True)
    # tags = BaseOfferTagsSerializer(many=True, read_only=True)
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
    product_name = serializers.CharField(source='*')
    price = serializers.FloatField()
    temp_solder_type = serializers.CharField(source='temp_offer_solder.temp_solder_type')
    temp_solder_value = serializers.FloatField(source='temp_offer_solder.temp_solder_value')
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
                  'service_longitude', 'service_latitude', 'service_address', 'service_km_radius']

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
