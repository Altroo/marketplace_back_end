from rest_framework import serializers
from subscription.models import AvailableSubscription, RequestedSubscriptions, \
    SubscribedUsers, IndexedArticles
from django.utils import timezone


class BaseGETAvailableSubscriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableSubscription
        fields = ['pk', 'nbr_article', 'prix_ht',
                  'prix_ttc', 'prix_unitaire_ht',
                  'prix_unitaire_ttc',
                  'pourcentage']


class BasePOSTRequestSubscriptionSerializer(serializers.ModelSerializer):
    company = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ice = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    created_date = serializers.DateTimeField(format="%d/%m/%Y %H:%M:%S", read_only=True)

    class Meta:
        model = RequestedSubscriptions
        fields = ['pk', 'auth_shop', 'subscription',
                  'company', 'ice', 'first_name', 'last_name',
                  'adresse', 'city', 'code_postal', 'country',
                  'promo_code', 'payment_type', 'reference_number',
                  'facture_number', 'created_date', 'status', 'remaining_to_pay']
        extra_kwargs = {
            'pk': {'read_only': True},
            'created_date': {'read_only': True},
        }


class BasePOSTAsPutRequestSubscriptionSerializer(serializers.ModelSerializer):
    company = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ice = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    class Meta:
        model = RequestedSubscriptions
        fields = ['auth_shop', 'subscription',
                  'company', 'ice', 'first_name', 'last_name',
                  'adresse', 'city', 'code_postal', 'country',
                  'promo_code', 'payment_type', 'reference_number', 'facture_number', 'remaining_to_pay']
        extra_kwargs = {
            'pk': {'read_only': True},
            'created_date': {'read_only': True},
        }


class BasePUTRequestSubscriptionSerializer(serializers.ModelSerializer):
    company = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ice = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    class Meta:
        model = RequestedSubscriptions
        fields = ['subscription',
                  'company', 'ice', 'first_name', 'last_name',
                  'adresse', 'city', 'code_postal', 'country',
                  'promo_code', 'payment_type', 'reference_number', 'facture_number']
        extra_kwargs = {
            'pk': {'read_only': True},
        }


class BasePOSTSubscribedUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscribedUsers
        fields = ['pk', 'original_request', 'available_slots', 'total_paid']
        extra_kwargs = {
            'pk': {'read_only': True},
        }


class BasePUTSubscribedUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscribedUsers
        fields = ['available_slots', 'total_paid', 'expiration_date']


class BaseGETCurrentUserSubscription(serializers.Serializer):
    # nbr_article = serializers.IntegerField(source='original_request.subscription.nbr_article')
    nbr_article = serializers.IntegerField(source='available_slots')
    pourcentage = serializers.IntegerField(source='original_request.subscription.pourcentage')
    prix_unitaire_ttc = serializers.IntegerField(source='original_request.subscription.prix_unitaire_ttc')
    # prix_ttc = serializers.IntegerField(source='original_request.subscription.prix_ttc')
    prix_ttc = serializers.IntegerField(source='total_paid')
    prix_ht = serializers.IntegerField(source='original_request.subscription.prix_ht')
    prix_unitaire_ht = serializers.IntegerField(source='original_request.subscription.prix_unitaire_ht')
    company = serializers.CharField(source='original_request.company')
    ice = serializers.CharField(source='original_request.ice')
    first_name = serializers.CharField(source='original_request.first_name')
    last_name = serializers.CharField(source='original_request.last_name')
    adresse = serializers.CharField(source='original_request.adresse')
    city = serializers.CharField(source='original_request.city')
    code_postal = serializers.CharField(source='original_request.code_postal')
    country = serializers.CharField(source='original_request.country.name_fr')
    used_slots = serializers.SerializerMethodField()
    facture = serializers.CharField(source='get_absolute_facture_path')
    expiration_date = serializers.DateTimeField(format='%d/%m/%Y')
    remaining_days = serializers.SerializerMethodField()

    @staticmethod
    def get_used_slots(instance):
        indexed_articles = IndexedArticles.objects.filter(offer__auth_shop__user=
                                                          instance.original_request.auth_shop.user).count()
        return indexed_articles

    @staticmethod
    def get_remaining_days(instance):
        remaining_days = instance.expiration_date - timezone.now()
        return round(remaining_days.days)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseGETIndexedArticlesList(serializers.Serializer):
    pk = serializers.IntegerField()
    thumbnail = serializers.SerializerMethodField()
    title = serializers.CharField(source='offer.title')
    # price = serializers.CharField(source='offer.price')

    @staticmethod
    def get_thumbnail(instance):
        if instance.offer.picture_1_thumbnail:
            return instance.offer.get_absolute_picture_1_thumbnail
        elif instance.offer.picture_2_thumbnail:
            return instance.offer.get_absolute_picture_2_thumbnail
        elif instance.offer.picture_3_thumbnail:
            return instance.offer.get_absolute_picture_3_thumbnail
        elif instance.offer.picture_4_thumbnail:
            return instance.offer.get_absolute_picture_4_thumbnail
        else:
            return None

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseGETAvailableArticlesList(serializers.Serializer):
    pk = serializers.IntegerField()
    thumbnail = serializers.SerializerMethodField()
    title = serializers.CharField()

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


class BasePOSTIndexArticlesSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndexedArticles
        fields = ['subscription', 'offer']
