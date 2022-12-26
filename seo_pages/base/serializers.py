from rest_framework import serializers
from seo_pages.models import DefaultSeoPage
from offers.models import Offers
from collections import Counter


class BaseDefaultSeoPageUrlsOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = DefaultSeoPage
        fields = ['page_url']


class BaseDefaultSeoPageSerializer(serializers.ModelSerializer):

    class Meta:
        model = DefaultSeoPage
        fields = ['pk', 'page_url', 'title', 'tags', 'header', 'paragraphe', 'page_meta_description']


class BaseCoupDeCoeurShopOffers(serializers.Serializer):
    offer_pk = serializers.IntegerField(source='pk')
    picture = serializers.CharField(source='get_absolute_picture_1_img')

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseCoupDeCoeurSerializer(serializers.Serializer):
    shop_pk = serializers.IntegerField(source='pk')
    shop_name = serializers.CharField()
    avatar = serializers.CharField(source='get_absolute_avatar_img')
    shop_link = serializers.CharField(source='qaryb_link')
    left_offers = serializers.SerializerMethodField()
    right_offers = serializers.SerializerMethodField()

    @staticmethod
    def get_left_offers(instance):
        offers_len = Offers.objects.filter(auth_shop=instance.pk).all()
        if offers_len.count() > 0:
            if offers_len.count() >= 4:
                shop_offers = offers_len[:2]
                offers = BaseCoupDeCoeurShopOffers(shop_offers, many=True)
                return offers.data
            elif offers_len >= 2:
                shop_offers = offers_len[:1]
                offers = BaseCoupDeCoeurShopOffers(shop_offers, many=True)
                return offers.data
            else:
                shop_offers = offers_len[0]
                offers = BaseCoupDeCoeurShopOffers(shop_offers, many=True)
                return offers.data
        else:
            return {}

    @staticmethod
    def get_right_offers(instance):
        offers_len = Offers.objects.filter(auth_shop=instance.pk).all()
        if offers_len.count() > 0:
            if offers_len.count() >= 4:
                shop_offers = offers_len[2:4]
                offers = BaseCoupDeCoeurShopOffers(shop_offers, many=True)
                return offers.data
            elif offers_len >= 2:
                shop_offers = offers_len[1:2]
                offers = BaseCoupDeCoeurShopOffers(shop_offers, many=True)
                return offers.data
            else:
                shop_offers = offers_len[0]
                offers = BaseCoupDeCoeurShopOffers(shop_offers, many=True)
                return offers.data
        else:
            return {}

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseNewShopsSerializer(serializers.Serializer):
    shop_pk = serializers.IntegerField(source='pk')
    shop_name = serializers.CharField()
    avatar = serializers.CharField(source='get_absolute_avatar_img')
    shop_link = serializers.CharField(source='qaryb_link')
    shop_category = serializers.SerializerMethodField()
    bg_color_code = serializers.CharField()

    @staticmethod
    def get_shop_category(instance):
        categories = Offers.objects.filter(auth_shop=instance.pk)\
            .prefetch_related('offer_categories').values_list('offer_categories__name_category',
                                                              flat=True)
        try:
            return Counter(categories).most_common()[0][0]
        except IndexError:
            return None

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseHomePageSerializer(serializers.Serializer):
    coup_de_coeur_bg = serializers.CharField()
    coup_de_coeur = BaseCoupDeCoeurSerializer()
    new_shops = BaseNewShopsSerializer(many=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
