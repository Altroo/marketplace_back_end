from rest_framework import serializers
from shop.models import AuthShop


class BaseGetRatingsListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    user_pk = serializers.SerializerMethodField()
    initiator_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    rating_note = serializers.IntegerField()
    rating_body = serializers.CharField()
    created_date = serializers.DateTimeField()

    def get_user_pk(self, instance):
        if self.context.get('order_type') == 'buy':
            return instance.buyer.pk
        else:
            return instance.seller.pk

    def get_initiator_name(self, instance):
        if self.context.get('order_type') == 'buy':
            return instance.buyer.first_name + ' ' + instance.buyer.last_name
        else:
            try:
                shop_name = AuthShop.objects.get(user=instance.seller).shop_name
                return shop_name
            except AuthShop.DoesNotExist:
                return instance.seller.first_name + ' ' + instance.seller.last_name

    def get_avatar(self, instance):
        if self.context.get('order_type') == 'buy':
            return instance.buyer.get_absolute_avatar_thumbnail
        else:
            try:
                avatar = AuthShop.objects.get(user=instance.seller).get_absolute_avatar_thumbnail
                return avatar
            except AuthShop.DoesNotExist:
                return instance.seller.get_absolute_avatar_thumbnail

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
