from rest_framework import serializers
from auth_shop.base.models import AuthShop, AuthShopDays, AskForCreatorLabel, ModeVacance, \
    DeletedAuthShops


class BaseShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthShop
        fields = [
            'user',
            'shop_name',
            'avatar', 'color_code', 'bg_color_code',
            'font_name',
            'qaryb_link', 'creator', 'unique_id']
        extra_kwargs = {
            'avatar': {'required': True},
        }

    def save(self):
        shop = AuthShop(
            user=self.validated_data['user'],
            shop_name=self.validated_data['shop_name'],
            avatar=self.validated_data['avatar'],
            color_code=self.validated_data['color_code'],
            bg_color_code=self.validated_data['bg_color_code'],
            font_name=self.validated_data['font_name'],
            qaryb_link=self.validated_data['qaryb_link'],
            # Read only default to False
            creator=self.validated_data['creator'],
            unique_id=self.validated_data['unique_id'],
        )
        shop.save()
        return shop


# class BaseShopOpeningDaysSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AuthShopDays
#         fields = ['code_day']


class BaseGETShopInfoSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(source='get_absolute_avatar_img')
    # opening_days = BaseShopOpeningDaysSerializer(many=True, read_only=True)
    opening_days = serializers.SerializerMethodField()
    morning_hour_from = serializers.TimeField(format='%H:%M')
    morning_hour_to = serializers.TimeField(format='%H:%M')
    afternoon_hour_from = serializers.TimeField(format='%H:%M')
    afternoon_hour_to = serializers.TimeField(format='%H:%M')

    @staticmethod
    def get_opening_days(instance):
        return instance.opening_days.values_list('code_day', flat=True)

    class Meta:
        model = AuthShop
        fields = ['shop_name', 'avatar', 'color_code', 'bg_color_code', 'font_name', 'bio',
                  'opening_days', 'morning_hour_from', 'morning_hour_to',
                  'afternoon_hour_from', 'afternoon_hour_to',
                  'phone', 'contact_email',
                  'website_link', 'facebook_link', 'twitter_link', 'instagram_link',
                  'whatsapp', 'zone_by', 'longitude', 'latitude',
                  'address_name', 'km_radius', 'creator']


class BaseShopAvatarPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthShop
        fields = ['avatar']
        extra_kwargs = {
            'avatar': {'required': True},
        }

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class BaseShopNamePutSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthShop
        fields = ['shop_name']
        extra_kwargs = {
            'shop_name': {'required': True},
        }

    def update(self, instance, validated_data):
        instance.shop_name = validated_data.get('shop_name', instance.shop_name)
        instance.save()
        return instance


class BaseShopBioPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthShop
        fields = ['bio']
        extra_kwargs = {
            'bio': {'required': True},
        }

    def update(self, instance, validated_data):
        instance.bio = validated_data.get('bio', instance.bio)
        instance.save()
        return instance


class BaseShopAvailabilityPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthShop
        fields = ['morning_hour_from', 'morning_hour_to',
                  'afternoon_hour_from', 'afternoon_hour_to']

    def update(self, instance, validated_data):
        instance.morning_hour_from = validated_data.get('morning_hour_from', instance.morning_hour_from)
        instance.morning_hour_to = validated_data.get('morning_hour_to', instance.morning_hour_to)
        instance.afternoon_hour_from = validated_data.get('afternoon_hour_from', instance.afternoon_hour_from)
        instance.afternoon_hour_to = validated_data.get('afternoon_hour_to', instance.afternoon_hour_to)
        instance.save()
        return instance


class BaseShopContactPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthShop
        fields = ['phone', 'contact_email',
                  'website_link',
                  'facebook_link', 'twitter_link', 'instagram_link', 'whatsapp']

    def update(self, instance, validated_data):
        instance.phone = validated_data.get('phone', instance.phone)
        instance.contact_email = validated_data.get('contact_email', instance.contact_email)
        instance.website_link = validated_data.get('website_link', instance.website_link)
        instance.facebook_link = validated_data.get('facebook_link', instance.facebook_link)
        instance.twitter_link = validated_data.get('twitter_link', instance.twitter_link)
        instance.instagram_link = validated_data.get('instagram_link', instance.instagram_link)
        instance.whatsapp = validated_data.get('whatsapp', instance.whatsapp)
        instance.save()
        return instance


class BaseShopTelPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthShop
        fields = ['phone']
        extra_kwargs = {
            'phone': {'required': True},
        }

    def update(self, instance, validated_data):
        instance.phone = validated_data.get('phone', instance.phone)
        instance.save()
        return instance


class BaseShopWtspPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthShop
        fields = ['whatsapp']
        extra_kwargs = {
            'whatsapp': {'required': True},
        }

    def update(self, instance, validated_data):
        instance.whatsapp = validated_data.get('whatsapp', instance.whatsapp)
        instance.save()
        return instance


class BaseShopAddressPutSerializer(serializers.ModelSerializer):
    def validate(self, data):
        """
        Check that start is before finish.
        """
        data_keys = data.keys()
        if data['zone_by'] == 'S' and 'km_radius' not in data_keys:
            raise serializers.ValidationError({'km_radius': ['km_radius is required when zone is by Sector.']})
        return data

    class Meta:
        model = AuthShop
        fields = ['zone_by', 'longitude', 'latitude', 'address_name', 'km_radius']
        extra_kwargs = {
            'zone_by': {'required': True},
            'longitude': {'required': True},
            'latitude': {'required': True},
            'address_name': {'required': True},
        }

    def update(self, instance, validated_data):
        instance.zone_by = validated_data.get('zone_by', instance.zone_by)
        instance.longitude = validated_data.get('longitude', instance.longitude)
        instance.latitude = validated_data.get('latitude', instance.latitude)
        instance.address_name = validated_data.get('address_name', instance.address_name)
        instance.km_radius = validated_data.get('km_radius', instance.km_radius)
        instance.save()
        return instance


class BaseShopColorPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthShop
        fields = ['color_code', 'bg_color_code']
        extra_kwargs = {
            'color_code': {'required': True},
            'bg_color_code': {'required': True},
        }

    def update(self, instance, validated_data):
        instance.color_code = validated_data.get('color_code', instance.color_code)
        instance.bg_color_code = validated_data.get('bg_color_code', instance.bg_color_code)
        instance.save()
        return instance


class BaseShopFontPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthShop
        fields = ['font_name']
        extra_kwargs = {
            'font_name': {'required': True},
        }

    def update(self, instance, validated_data):
        instance.font_name = validated_data.get('font_name', instance.font_name)
        instance.save()
        return instance


class BaseShopAskForCreatorLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AskForCreatorLabel
        fields = ['auth_shop']


class BaseShopModeVacanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeVacance
        fields = ['auth_shop', 'date_from', 'date_to']


class BaseShopModeVacancePUTSerializer(serializers.ModelSerializer):

    class Meta:
        model = ModeVacance
        fields = ['date_from', 'date_to']

    def update(self, instance, validated_data):
        instance.date_from = validated_data.get('date_from', instance.date_from)
        instance.date_to = validated_data.get('date_to', instance.date_to)
        instance.save()
        return instance


class BaseDeletedAuthShopsSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeletedAuthShops
        fields = ['user', 'reason_choice', 'typed_reason']
