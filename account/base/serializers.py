from rest_framework import serializers
from account.models import CustomUser, BlockedUsers, ReportedUsers, UserAddress, EnclosedAccounts, DeletedAccounts
from django.contrib.auth.password_validation import validate_password
from allauth.account.models import EmailAddress
from offers.base.serializers import BaseShopCitySerializer
from places.base.serializers import BaseCountriesSerializer
from shop.base.utils import Base64ImageField


class BaseSocialAccountSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    provider = serializers.CharField()
    uid = serializers.CharField()
    last_login = serializers.DateTimeField()
    date_joined = serializers.DateTimeField()
    extra_data = serializers.JSONField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'password2',
                  'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    @staticmethod
    def validate_password(value):
        validate_password(value)
        return value

    @staticmethod
    def validate_password2(value):
        validate_password(value)
        return value

    def save(self):
        account = CustomUser(
            email=self.validated_data['email'],
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
        )
        password = self.validated_data['password']
        password2 = self.validated_data['password2']
        if password != password2:
            raise serializers.ValidationError(
                {'password2': ["Ces mot de passes ne correspond pas."]}
            )
        account.set_password(password)
        account.save()
        return account


class BaseRegistrationEmailAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAddress
        fields = ['user', 'email', 'primary']


class BasePasswordResetSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    new_password = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    @staticmethod
    def validate_new_password(value):
        validate_password(value)
        return value

    @staticmethod
    def validate_new_password2(value):
        validate_password(value)
        return value


class BaseUserEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        model = CustomUser
        fields = ['email']
        extra_kwargs = {
            'email': {'write_only': True},
        }


class BaseProfilePutSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(
        max_length=None, use_url=True,
    )

    class Meta:
        model = CustomUser
        fields = ['avatar', 'first_name', 'last_name', 'gender', 'birth_date', 'city', 'country']


class BaseProfileGETSerializer(serializers.ModelSerializer):
    avatar_thumbnail = serializers.CharField(source='get_absolute_avatar_thumbnail')
    city = BaseShopCitySerializer(read_only=True)
    country = BaseCountriesSerializer(read_only=True)
    gender = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(format='%Y-%m-%d')

    @staticmethod
    def get_gender(instance):
        if instance.gender != '':
            return instance.gender
        return None

    class Meta:
        model = CustomUser
        fields = ['pk', 'avatar', 'avatar_thumbnail', 'first_name', 'last_name', 'gender',
                  'birth_date', 'city', 'country', 'date_joined']


# class BaseBlockedUsersListSerializer(serializers.Serializer):
#     pk = serializers.IntegerField()
#     # Blocked user
#     blocked_user_pk = serializers.IntegerField(source='user_blocked.pk')
#     blocked_user_first_name = serializers.CharField(source='user_blocked.first_name')
#     blocked_user_last_name = serializers.CharField(source='user_blocked.last_name')
#     blocked_user_avatar = serializers.CharField(source='user_blocked.get_absolute_avatar_thumbnail')
#
#     def update(self, instance, validated_data):
#         pass
#
#     def create(self, validated_data):
#         pass


class BaseBlockedUsersListSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField()
    # Blocked user
    blocked_user_pk = serializers.IntegerField(source='user_blocked.pk')
    blocked_user_first_name = serializers.CharField(source='user_blocked.first_name')
    blocked_user_last_name = serializers.CharField(source='user_blocked.last_name')
    blocked_user_avatar = serializers.CharField(source='user_blocked.get_absolute_avatar_thumbnail')

    class Meta:
        model = BlockedUsers
        fields = ['pk', 'blocked_user_pk', 'blocked_user_first_name', 'blocked_user_last_name', 'blocked_user_avatar']


class BaseUserAddressesListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    title = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    address = serializers.CharField()
    # city = serializers.CharField(source='city.name_fr')
    city = BaseShopCitySerializer(read_only=True)
    zip_code = serializers.IntegerField()
    # country = serializers.CharField(source='country.name_fr')
    country = BaseCountriesSerializer(read_only=True)
    phone = serializers.CharField()
    email = serializers.EmailField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# For naming convention
class BaseUserAddresseDetailSerializer(BaseUserAddressesListSerializer):
    pass


class BaseUserAddressSerializer(serializers.ModelSerializer):
    # city = BaseShopCitySerializer(read_only=True)
    # country = BaseCountriesSerializer(read_only=True)

    class Meta:
        model = UserAddress
        fields = ['pk', 'user', 'title', 'first_name',
                  'last_name', 'address', 'city', 'zip_code',
                  'country', 'phone', 'email']
        extra_kwargs = {
            'user': {'write_only': True},
        }


class BaseUserAddressPutSerializer(serializers.ModelSerializer):
    city = BaseShopCitySerializer(read_only=True)
    country = BaseCountriesSerializer(read_only=True)

    class Meta:
        model = UserAddress
        fields = ['pk', 'title', 'first_name',
                  'last_name', 'address', 'city', 'zip_code',
                  'country', 'phone', 'email']


class BaseEmailPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email']

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance


class BaseBlockUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedUsers
        fields = ['user', 'user_blocked']


class BaseReportPostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportedUsers
        fields = ['user', 'user_reported', 'report_reason']


class BaseEnclosedAccountsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnclosedAccounts
        fields = ['user', 'reason_choice', 'typed_reason']


class BaseDeletedAccountsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeletedAccounts
        fields = ['email', 'reason_choice', 'typed_reason']
