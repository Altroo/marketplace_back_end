from rest_framework import serializers
from cart.models import Cart
from offers.models import Offers, Solder, Products, Services, \
    Categories, Colors, Sizes, ForWhom, ServiceDays, Delivery, OfferTags, OfferVue
from places.models import City, Country
from shop.base.utils import Base64ImageField
from uuid import uuid4

class BaseOfferCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['pk', 'code_category', 'name_category']


class BaseOfferTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferTags
        fields = ['name_tag']


# class BaseOfferTagsSerializer(serializers.Serializer):
#     name_tag = serializers.CharField()
#
#     def update(self, instance, validated_data):
#         pass
#
#     def create(self, validated_data):
#         pass


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
                  'picture_1_thumbnail', 'picture_2_thumbnail', 'picture_4_thumbnail',
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
    picture_1 = Base64ImageField(
        max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
    )
    picture_1_thumbnail = Base64ImageField(
        max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
    )
    picture_2 = Base64ImageField(
        max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
    )
    picture_2_thumbnail = Base64ImageField(
        max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
    )
    picture_3 = Base64ImageField(
        max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
    )
    picture_3_thumbnail = Base64ImageField(
        max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
    )
    picture_4 = Base64ImageField(
        max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
    )
    picture_4_thumbnail = Base64ImageField(
        max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
    )
    offer_categories = BaseOfferCategoriesSerializer(many=True, read_only=True)
    for_whom = BaseOfferForWhomSerializer(many=True, read_only=True)
    # tags = BaseOfferTagsSerializer(many=True, read_only=True)
    creator_label = serializers.BooleanField(required=False, allow_null=True, default=False)

    class Meta:
        model = Offers
        fields = ['auth_shop', 'offer_type', 'offer_categories', 'title',
                  'picture_1', 'picture_1_thumbnail', 'picture_2', 'picture_2_thumbnail', 'picture_3',
                  'picture_3_thumbnail', 'picture_4', 'picture_4_thumbnail',
                  'description', 'for_whom', 'creator_label', 'made_in_label',
                  'price']

    extra_kwargs = {
        'picture_1': {'required': False},
        'picture_1_thumbnail': {'required': False},
        'picture_2': {'required': False},
        'picture_2_thumbnail': {'required': False},
        'picture_3': {'required': False},
        'picture_3_thumbnail': {'required': False},
        'picture_4': {'required': False},
        'picture_4_thumbnail': {'required': False},
    }


# Global Product serializer
class BaseShopProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ['offer', 'product_quantity', 'product_price_by', 'product_longitude',
                  'product_latitude', 'product_address']


# Global Service serializer
class BaseShopServiceSerializer(serializers.ModelSerializer):
    service_availability_days = BaseServiceAvailabilityDaysSerializer(many=True, read_only=True)
    service_morning_hour_from = serializers.TimeField(format='%H:%M')
    service_morning_hour_to = serializers.TimeField(format='%H:%M')
    service_afternoon_hour_from = serializers.TimeField(format='%H:%M', allow_null=True, default=None, required=False)
    service_afternoon_hour_to = serializers.TimeField(format='%H:%M', allow_null=True, default=None, required=False)

    class Meta:
        model = Services
        fields = ['offer', 'service_availability_days',
                  'service_morning_hour_from', 'service_morning_hour_to',
                  'service_afternoon_hour_from', 'service_afternoon_hour_to',
                  'service_zone_by', 'service_price_by',
                  'service_longitude', 'service_latitude', 'service_address', 'service_km_radius']


class BaseShopCitySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_fr')

    class Meta:
        model = City
        # Keept for the views output key names
        fields = ['pk', 'name']


class BaseShopOriginalCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        # Keept for the views output key names
        fields = ['pk', 'name_en', 'name_fr', 'name_ar']


class BaseShopDeliverySerializer(serializers.ModelSerializer):
    # delivery_city = BaseShopCitySerializer(many=True, read_only=True)
    # pk = serializers.PrimaryKeyRelatedField(read_only=True)
    delivery_city = serializers.SerializerMethodField()

    @staticmethod
    def get_delivery_city(instance):
        return instance.delivery_city.values_list('name_fr', flat=True).all()

    class Meta:
        model = Delivery
        fields = ['offer', 'delivery_city', 'all_cities', 'delivery_price', 'delivery_days']
        extra_kwargs = {
            'offer': {'write_only': True},
            # 'pk': {'read_only': True},
        }


# Used in offer details view
class BaseShopOriginalDeliverySerializer(serializers.ModelSerializer):
    delivery_city = BaseShopOriginalCitySerializer(many=True, read_only=True)

    # delivery_city = serializers.SerializerMethodField()

    # @staticmethod
    # def get_delivery_city(instance):
    #     return instance.delivery_city.values_list('name_fr', flat=True).all()

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
    # product_colors = serializers.SerializerMethodField()
    # product_colors = BaseProductColorSerializer(many=True, read_only=True)
    product_colors = serializers.SerializerMethodField()
    # product_sizes = serializers.SerializerMethodField()

    # product_sizes = BaseProductSizeSerializer(many=True, read_only=True)
    product_sizes = serializers.SerializerMethodField()

    # offer_delivery = BaseShopOriginalDeliverySerializer(many=True)
    # offer_delivery = serializers.SerializerMethodField()

    @staticmethod
    def get_product_colors(instance):
        return instance.product_colors.values_list('code_color', flat=True).all()

    @staticmethod
    def get_product_sizes(instance):
        return instance.product_sizes.values_list('code_size', flat=True).all()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseDetailsServiceSerializer(serializers.Serializer):
    # Details Product
    service_availability_days = BaseServiceAvailabilityDaysSerializer(many=True, read_only=True)
    # service_availability_days = serializers.SerializerMethodField()
    service_morning_hour_from = serializers.TimeField()
    service_morning_hour_to = serializers.TimeField()
    service_afternoon_hour_from = serializers.TimeField()
    service_afternoon_hour_to = serializers.TimeField()
    service_zone_by = serializers.CharField()
    service_price_by = serializers.CharField()
    service_longitude = serializers.CharField()
    service_latitude = serializers.CharField()
    service_address = serializers.CharField()
    service_km_radius = serializers.FloatField()

    # @staticmethod
    # def get_service_availability_days(instance):
    #     return instance.service_availability_days.values_list('code_day', flat=True).all()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseCountriesSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_fr')

    class Meta:
        model = Country
        fields = (
            'name',
            'code'
        )


class BaseOfferDetailsSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    user_pk = serializers.IntegerField(source='auth_shop.user.pk')
    title = serializers.CharField()
    offer_type = serializers.CharField()
    # offer_categories = BaseOfferCategoriesSerializer(many=True, read_only=True)
    # offer_categories = BaseOfferCategoriesSerializer(many=True, read_only=True)
    offer_categories = serializers.SerializerMethodField()
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
    # for_whom = BaseOfferForWhomSerializer(many=True, read_only=True)
    for_whom = serializers.SerializerMethodField()
    price = serializers.FloatField()
    creator_label = serializers.BooleanField()
    made_in_label = BaseCountriesSerializer(read_only=True)
    # made_in_label = serializers.CharField()
    # details product or details service
    details_offer = serializers.SerializerMethodField()
    solder_type = serializers.CharField(source='offer_solder.solder_type')
    solder_value = serializers.FloatField(source='offer_solder.solder_value')
    deliveries = BaseShopDeliverySerializer(many=True, read_only=True, source='offer_delivery')
    exist_in_cart = serializers.SerializerMethodField()
    pinned = serializers.BooleanField()
    unique_id = serializers.SerializerMethodField()
    # tags = serializers.SerializerMethodField()

    # @staticmethod
    # def get_tags(instance):
    #     return instance.tags.values_list('name_tag', flat=True).all()
    # @staticmethod
    # def get_for_whom(instance):
    #     return instance.for_whom.values_list('code_for_whom', flat=True).all()
    #
    # @staticmethod
    # def get_offer_categories(instance):
    #     return instance.offer_categories.values_list('code_category', flat=True).all()

    @staticmethod
    def get_unique_id(instance):
        return uuid4()

    @staticmethod
    def get_for_whom(instance):
        return instance.for_whom.values_list('code_for_whom', flat=True).all()

    @staticmethod
    def get_offer_categories(instance):
        return instance.offer_categories.values_list('code_category', flat=True).all()

    def get_exist_in_cart(self, instance):
        unique_id = self.context.get("unique_id")
        if unique_id is not None:
            try:
                Cart.objects.get(unique_id=unique_id, offer=instance.pk)
                return True
            except Cart.DoesNotExist:
                return False
        return False

    @staticmethod
    def get_details_offer(instance):
        if instance.offer_type == 'V':
            details_product = BaseDetailsProductSerializer(instance.offer_products)
            return details_product.data
        if instance.offer_type == 'S':
            details_service = BaseDetailsServiceSerializer(instance.offer_services)
            return details_service.data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.offer_type == 'S':
            del data['deliveries']
        return data

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseOffersListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    thumbnail = serializers.SerializerMethodField()
    title = serializers.CharField()
    price = serializers.FloatField()
    solder_type = serializers.CharField(source='offer_solder.solder_type')
    solder_value = serializers.FloatField(source='offer_solder.solder_value')
    creator_label = serializers.BooleanField()
    # details_offer = serializers.SerializerMethodField()
    offer_type = serializers.CharField()
    pinned = serializers.BooleanField()
    shop_url = serializers.SlugField(source='auth_shop.qaryb_link')
    # TODO add ratings once available

    # @staticmethod
    # def get_details_offer(instance):
    #     if instance.offer_type == 'V':
    #         details_product = BaseDetailsProductSerializer(instance.offer_products)
    #         return details_product.data
    #     if instance.offer_type == 'S':
    #         details_service = BaseDetailsServiceSerializer(instance.offer_services)
    #         return details_service.data

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
        elif instance.picture_1:
            return instance.get_absolute_picture_1_img
        elif instance.picture_2:
            return instance.get_absolute_picture_2_img
        elif instance.picture_3:
            return instance.get_absolute_picture_3_img
        elif instance.picture_4:
            return instance.get_absolute_picture_4_img
        else:
            return None

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseOffersMiniProfilListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    thumbnail = serializers.CharField(source='get_absolute_picture_1_thumbnail')
    title = serializers.CharField()
    price = serializers.FloatField()
    solder_type = serializers.CharField(source='offer_solder.solder_type')
    solder_value = serializers.FloatField(source='offer_solder.solder_value')
    creator_label = serializers.BooleanField()
    offer_type = serializers.CharField()
    pinned = serializers.BooleanField()

    # @staticmethod
    # def get_thumbnail(instance):
    #     if instance.picture_1:
    #         return instance.get_absolute_picture_1_img
    #     elif instance.picture_2:
    #         return instance.get_absolute_picture_2_img
    #     elif instance.picture_3:
    #         return instance.get_absolute_picture_3_img
    #     elif instance.picture_4:
    #         return instance.get_absolute_picture_4_img
    #     else:
    #         return None

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseOfferPutSerializer(serializers.ModelSerializer):
    # picture_1 = Base64ImageField(max_length=None, use_url=True, required=False, allow_empty_file=True, default=None,
    #                              allow_null=True)
    # picture_2 = Base64ImageField(max_length=None, use_url=True, required=False, allow_empty_file=True, default=None,
    #                              allow_null=True)
    # picture_3 = Base64ImageField(max_length=None, use_url=True, required=False, allow_empty_file=True, default=None,
    #                              allow_null=True)
    # picture_4 = Base64ImageField(max_length=None, use_url=True, required=False, allow_empty_file=True, default=None,
    #                              allow_null=True)

    class Meta:
        model = Offers
        fields = ['title', 'description', 'creator_label', 'made_in_label', 'price']
        # extra_kwargs = {
        #     'picture_1': {'required': False},
        #     'picture_2': {'required': False},
        #     'picture_3': {'required': False},
        #     'picture_4': {'required': False},
        # }


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
    service_morning_hour_from = serializers.TimeField(format='%H:%M')
    service_morning_hour_to = serializers.TimeField(format='%H:%M')
    service_afternoon_hour_from = serializers.TimeField(format='%H:%M', allow_null=True, default=None, required=False)
    service_afternoon_hour_to = serializers.TimeField(format='%H:%M', allow_null=True, default=None, required=False)

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

    # def update(self, instance, validated_data):
    #     instance.solder_type = validated_data.get('solder_type', instance.solder_type)
    #     instance.solder_value = validated_data.get('solder_value', instance.solder_value)
    #     instance.save()
    #     return instance


class BaseOffersVuesListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    thumbnail = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    nbr_total_vue = serializers.SerializerMethodField()

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

    @staticmethod
    def get_nbr_total_vue(instance):
        try:
            if instance.offer_vues.nbr_total_vue is None:
                return 0
        except OfferVue.DoesNotExist:
            return 0
        return instance.offer_vues.nbr_total_vue

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# # Offer serializer for Duplicate
# class BaseTempShopOfferDuplicateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TempOffers
#         fields = ['auth_shop', 'offer_type', 'title',
#                   'picture_1', 'picture_2', 'picture_3', 'picture_4',
#                   'picture_1_thumbnail', 'picture_2_thumbnail', 'picture_3_thumbnail', 'picture_4_thumbnail',
#                   'description', 'price']
#
#     def save(self):
#         offer = TempOffers(
#             auth_shop=self.validated_data['auth_shop'],
#             offer_type=self.validated_data['offer_type'],
#             title=self.validated_data['title'],
#             picture_1=self.validated_data['picture_1'],
#             picture_2=self.validated_data['picture_2'],
#             picture_3=self.validated_data['picture_3'],
#             picture_4=self.validated_data['picture_4'],
#             picture_1_thumbnail=self.validated_data['picture_1_thumbnail'],
#             picture_2_thumbnail=self.validated_data['picture_2_thumbnail'],
#             picture_3_thumbnail=self.validated_data['picture_3_thumbnail'],
#             picture_4_thumbnail=self.validated_data['picture_4_thumbnail'],
#             description=self.validated_data['description'],
#             price=self.validated_data['price'],
#         )
#         offer.save()
#         return offer
#
#
# # Global Offer serializer
# class BaseTempShopOfferSerializer(serializers.ModelSerializer):
#     picture_1 = Base64ImageField(
#         max_length=None, use_url=True, required=True,
#     )
#     picture_2 = Base64ImageField(
#         max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
#     )
#     picture_3 = Base64ImageField(
#         max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
#     )
#     picture_4 = Base64ImageField(
#         max_length=None, use_url=True, required=False, allow_null=True, allow_empty_file=True,
#     )
#     offer_categories = BaseOfferCategoriesSerializer(many=True, read_only=True)
#     for_whom = BaseOfferForWhomSerializer(many=True, read_only=True)
#     tags = BaseOfferTagsSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = TempOffers
#         fields = ['auth_shop', 'offer_type', 'offer_categories', 'title',
#                   'picture_1', 'picture_2', 'picture_3', 'picture_4',
#                   'description', 'for_whom', 'tags', 'made_in_label', 'price']
#
#
# # Global Product serializer
# class BaseTempShopProductSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TempProducts
#         fields = ['offer', 'product_quantity', 'product_price_by', 'product_longitude',
#                   'product_latitude', 'product_address']
#
#
# # Global Service serializer
# class BaseTempShopServiceSerializer(serializers.ModelSerializer):
#     service_availability_days = BaseServiceAvailabilityDaysSerializer(many=True, read_only=True)
#     service_morning_hour_from = serializers.TimeField(format='%H:%M')
#     service_morning_hour_to = serializers.TimeField(format='%H:%M')
#     service_afternoon_hour_from = serializers.TimeField(format='%H:%M', allow_null=True, default=None, required=False)
#     service_afternoon_hour_to = serializers.TimeField(format='%H:%M', allow_null=True, default=None, required=False)
#
#     class Meta:
#         model = TempServices
#         fields = ['offer', 'service_availability_days',
#                   'service_morning_hour_from', 'service_morning_hour_to',
#                   'service_afternoon_hour_from', 'service_afternoon_hour_to',
#                   'service_zone_by', 'service_price_by',
#                   'service_longitude', 'service_latitude', 'service_address', 'service_km_radius']

#
# class BaseTempShopCitySerializer(serializers.ModelSerializer):
#     city = serializers.CharField(source='name_fr')
#
#     class Meta:
#         model = City
#         fields = ['pk', 'city']


# class BaseTempShopDeliverySerializer(serializers.ModelSerializer):
#     # pk = serializers.PrimaryKeyRelatedField(read_only=True)
#
#     delivery_city = serializers.SerializerMethodField()
#
#     @staticmethod
#     def get_delivery_city(instance):
#         return instance.delivery_city.values_list('name_fr', flat=True).all()
#
#     class Meta:
#         model = TempDelivery
#         fields = ['offer', 'delivery_city', 'all_cities', 'delivery_price', 'delivery_days']
#         extra_kwargs = {
#             'offer': {'write_only': True},
#             # 'pk': {'read_only': True},
#         }


# class BaseDetailsTempProductSerializer(serializers.Serializer):
#     # Details Product
#     product_quantity = serializers.IntegerField()
#     product_price_by = serializers.CharField()
#     product_longitude = serializers.CharField()
#     product_latitude = serializers.CharField()
#     product_address = serializers.CharField()
#     product_colors = serializers.SerializerMethodField()
#     # product_colors = BaseProductColorSerializer(many=True, read_only=True)
#     product_sizes = serializers.SerializerMethodField()
#     # product_sizes = BaseProductSizeSerializer(many=True, read_only=True)
#
#     @staticmethod
#     def get_product_colors(instance):
#         return instance.product_colors.values_list('code_color', flat=True).all()
#
#     @staticmethod
#     def get_product_sizes(instance):
#         return instance.product_sizes.values_list('code_size', flat=True).all()
#
#     def update(self, instance, validated_data):
#         pass
#
#     def create(self, validated_data):
#         pass


# class BaseDetailsTempServiceSerializer(serializers.Serializer):
#     # Details Product
#     service_availability_days = BaseServiceAvailabilityDaysSerializer(many=True, read_only=True)
#     # service_availability_days = serializers.SerializerMethodField()
#     service_morning_hour_from = serializers.TimeField()
#     service_morning_hour_to = serializers.TimeField()
#     service_afternoon_hour_from = serializers.TimeField()
#     service_afternoon_hour_to = serializers.TimeField()
#     service_zone_by = serializers.CharField()
#     service_price_by = serializers.CharField()
#     service_longitude = serializers.CharField()
#     service_latitude = serializers.CharField()
#     service_address = serializers.CharField()
#     service_km_radius = serializers.FloatField()
#
#     # @staticmethod
#     # def get_service_availability_days(instance):
#     #     return instance.service_availability_days.values_list('code_day', flat=True).all()
#
#     def update(self, instance, validated_data):
#         pass
#
#     def create(self, validated_data):
#         pass


# class BaseTempShopDeliveryFlatSerializer(serializers.ModelSerializer):
#     # pk = serializers.PrimaryKeyRelatedField(read_only=True)
#     delivery_city = serializers.SerializerMethodField()
#
#     @staticmethod
#     def get_delivery_city(instance):
#         return instance.delivery_city.values_list('name_fr', flat=True).all()
#
#     class Meta:
#         model = TempDelivery
#         fields = ['offer', 'delivery_city', 'all_cities', 'delivery_price', 'delivery_days']
#         extra_kwargs = {
#             'offer': {'write_only': True},
#             # 'pk': {'read_only': True},
#         }


# class BaseTempOfferDetailsSerializer(serializers.Serializer):
#     pk = serializers.IntegerField()
#     title = serializers.CharField()
#     offer_type = serializers.CharField()
#     # offer_categories = BaseOfferCategoriesSerializer(many=True, read_only=True)
#     # offer_categories = BaseOfferCategoriesSerializer(many=True, read_only=True)
#     offer_categories = serializers.SerializerMethodField()
#     # Shop_name
#     shop_name = serializers.CharField(source='auth_shop.shop_name')
#     picture_1 = serializers.CharField(source='get_absolute_picture_1_img_base64')
#     picture_1_thumb = serializers.CharField(source='get_absolute_picture_1_thumbnail_base64')
#     picture_2 = serializers.CharField(source='get_absolute_picture_2_img_base64')
#     picture_2_thumb = serializers.CharField(source='get_absolute_picture_2_thumbnail_base64')
#     picture_3 = serializers.CharField(source='get_absolute_picture_3_img_base64')
#     picture_3_thumb = serializers.CharField(source='get_absolute_picture_3_thumbnail_base64')
#     picture_4 = serializers.CharField(source='get_absolute_picture_4_img_base64')
#     picture_4_thumb = serializers.CharField(source='get_absolute_picture_4_thumbnail_base64')
#     description = serializers.CharField()
#     # for_whom = BaseOfferForWhomSerializer(many=True, read_only=True)
#     for_whom = serializers.SerializerMethodField()
#     price = serializers.FloatField()
#     made_in_label = BaseCountriesSerializer(read_only=True)
#     # details product or details service
#     details_offer = serializers.SerializerMethodField()
#     solder_type = serializers.CharField(source='temp_offer_solder.solder_type')
#     solder_value = serializers.FloatField(source='temp_offer_solder.solder_value')
#     deliveries = BaseTempShopDeliveryFlatSerializer(many=True, read_only=True, source='temp_offer_delivery')
#     pinned = serializers.BooleanField()
#     tags = serializers.SerializerMethodField()
#
#     @staticmethod
#     def get_tags(instance):
#         return instance.tags.values_list('name_tag', flat=True).all()
#
#     @staticmethod
#     def get_for_whom(instance):
#         return instance.for_whom.values_list('code_for_whom', flat=True).all()
#
#     @staticmethod
#     def get_offer_categories(instance):
#         return instance.offer_categories.values_list('code_category', flat=True).all()
#
#     @staticmethod
#     def get_details_offer(instance):
#         if instance.offer_type == 'V':
#             details_product = BaseDetailsTempProductSerializer(instance.temp_offer_products)
#             return details_product.data
#         if instance.offer_type == 'S':
#             details_service = BaseDetailsTempServiceSerializer(instance.temp_offer_services)
#             return details_service.data
#
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         if instance.offer_type == 'S':
#             del data['offer_delivery']
#         return data
#
#     def update(self, instance, validated_data):
#         pass
#
#     def create(self, validated_data):
#         pass


# class BaseTempOffersListSerializer(serializers.Serializer):
#     pk = serializers.IntegerField()
#     thumbnail = serializers.SerializerMethodField()
#     title = serializers.CharField()
#     price = serializers.FloatField()
#     solder_type = serializers.CharField(source='temp_offer_solder.solder_type')
#     solder_value = serializers.FloatField(source='temp_offer_solder.solder_value')
#     # details_offer = serializers.SerializerMethodField()
#     pinned = serializers.BooleanField()
#     # TODO add ratings once available
#
#     @staticmethod
#     def get_details_offer(instance):
#         if instance.offer_type == 'V':
#             details_product = BaseDetailsTempProductSerializer(instance.temp_offer_products)
#             return details_product.data
#         if instance.offer_type == 'S':
#             details_service = BaseDetailsTempServiceSerializer(instance.temp_offer_services)
#             return details_service.data
#
#     @staticmethod
#     def get_thumbnail(instance):
#         if instance.picture_1:
#             return instance.get_absolute_picture_1_img
#         elif instance.picture_2:
#             return instance.get_absolute_picture_2_img
#         elif instance.picture_3:
#             return instance.get_absolute_picture_3_img
#         elif instance.picture_4:
#             return instance.get_absolute_picture_4_img
#         else:
#             return None
#
#     def update(self, instance, validated_data):
#         pass
#
#     def create(self, validated_data):
#         pass


# class BaseTempOfferPutSerializer(serializers.ModelSerializer):
#     picture_1 = Base64ImageField(max_length=None, use_url=True, required=False, allow_empty_file=True, default=None,
#                                  allow_null=True)
#     picture_2 = Base64ImageField(max_length=None, use_url=True, required=False, allow_empty_file=True, default=None,
#                                  allow_null=True)
#     picture_3 = Base64ImageField(max_length=None, use_url=True, required=False, allow_empty_file=True, default=None,
#                                  allow_null=True)
#     picture_4 = Base64ImageField(max_length=None, use_url=True, required=False, allow_empty_file=True, default=None,
#                                  allow_null=True)
#
#     class Meta:
#         model = TempOffers
#         fields = ['title', 'picture_1', 'picture_2', 'picture_3', 'picture_4',
#                   'description', 'made_in_label', 'price']
#         extra_kwargs = {
#             'picture_1': {'required': False},
#             'picture_2': {'required': False},
#             'picture_3': {'required': False},
#             'picture_4': {'required': False},
#         }
#
#     def update(self, instance, validated_data):
#         instance.title = validated_data.get('title', instance.title)
#         instance.picture_1 = validated_data.get('picture_1', instance.picture_1)
#         instance.picture_2 = validated_data.get('picture_2', instance.picture_2)
#         instance.picture_3 = validated_data.get('picture_3', instance.picture_3)
#         instance.picture_4 = validated_data.get('picture_4', instance.picture_4)
#         instance.description = validated_data.get('description', instance.description)
#         instance.made_in_label = validated_data.get('made_in_label', instance.made_in_label)
#         instance.price = validated_data.get('price', instance.price)
#         instance.save()
#         return instance
#
#
# class BaseTempProductPutSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TempProducts
#         fields = ['product_quantity', 'product_price_by', 'product_longitude', 'product_latitude', 'product_address']
#
#     def update(self, instance, validated_data):
#         instance.product_quantity = validated_data.get('product_quantity', instance.product_quantity)
#         instance.product_price_by = validated_data.get('product_price_by', instance.product_price_by)
#         instance.product_longitude = validated_data.get('product_longitude', instance.product_longitude)
#         instance.product_latitude = validated_data.get('product_latitude', instance.product_latitude)
#         instance.product_address = validated_data.get('product_address', instance.product_address)
#         instance.save()
#         return instance
#
#
# class BaseTempServicePutSerializer(serializers.ModelSerializer):
#     service_morning_hour_from = serializers.TimeField(format='%H:%M')
#     service_morning_hour_to = serializers.TimeField(format='%H:%M')
#     service_afternoon_hour_from = serializers.TimeField(format='%H:%M', allow_null=True, default=None, required=False)
#     service_afternoon_hour_to = serializers.TimeField(format='%H:%M', allow_null=True, default=None, required=False)
#
#     class Meta:
#         model = TempServices
#         fields = ['service_morning_hour_from', 'service_morning_hour_to',
#                   'service_afternoon_hour_from', 'service_afternoon_hour_to',
#                   'service_zone_by', 'service_price_by',
#                   'service_longitude', 'service_latitude', 'service_address', 'service_km_radius']
#
#     def update(self, instance, validated_data):
#         instance.service_morning_hour_from = validated_data.get('service_morning_hour_from',
#                                                                 instance.service_morning_hour_from)
#         instance.service_morning_hour_to = validated_data.get('service_morning_hour_to',
#                                                               instance.service_morning_hour_to)
#         instance.service_afternoon_hour_from = validated_data.get('service_afternoon_hour_from',
#                                                                   instance.service_afternoon_hour_from)
#         instance.service_afternoon_hour_to = validated_data.get('service_afternoon_hour_to',
#                                                                 instance.service_afternoon_hour_to)
#         instance.service_zone_by = validated_data.get('service_zone_by', instance.service_zone_by)
#         instance.service_price_by = validated_data.get('service_price_by', instance.service_price_by)
#         instance.service_longitude = validated_data.get('service_longitude', instance.service_longitude)
#         instance.service_latitude = validated_data.get('service_latitude', instance.service_latitude)
#         instance.service_address = validated_data.get('service_address', instance.service_address)
#         instance.save()
#         return instance
#
#
# class BaseTempShopOfferSolderSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TempSolder
#         fields = ['offer', 'solder_type', 'solder_value']
#
#     def save(self):
#         solder = TempSolder(
#             offer=self.validated_data['offer'],
#             solder_type=self.validated_data['solder_type'],
#             solder_value=self.validated_data['solder_value'],
#         )
#         solder.save()
#         return solder
#
#
# class BaseTempShopOfferSolderPutSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TempSolder
#         fields = ['solder_type', 'solder_value']
