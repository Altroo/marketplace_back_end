from rest_framework import serializers
from account.models import CustomUser, BlockedUsers, ReportedUsers, UserAddress, EnclosedAccounts, DeletedAccounts
from django.contrib.auth.password_validation import validate_password
from allauth.account.models import EmailAddress


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
                {'password2': ['The passwords don\'t match.']}
            )
        elif len(password) < 8 or len(password2) < 8:
            raise serializers.ValidationError(
                {'password': ['The password must be at least 8 characters long.']}
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


class BaseUserEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        model = CustomUser
        fields = ['email']
        extra_kwargs = {
            'email': {'write_only': True},
        }


# class BaseProfileAvatarPutSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['avatar']
#         extra_kwargs = {
#             'avatar': {'required': True},
#         }
#
#     def update(self, instance, validated_data):
#         instance.avatar = validated_data.get('avatar', instance.avatar)
#         instance.save()
#         return instance


class BaseProfilePutSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['avatar', 'first_name', 'last_name', 'gender', 'birth_date', 'city', 'country']

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.birth_date = validated_data.get('birth_date', instance.birth_date)
        instance.city = validated_data.get('city', instance.city)
        instance.country = validated_data.get('country', instance.country)
        instance.save()
        return instance


class BaseProfileGETSerializer(serializers.ModelSerializer):
    avatar_thumbnail = serializers.CharField(source='get_absolute_avatar_thumbnail')
    city = serializers.CharField(source='city.name_fr')
    country = serializers.CharField(source='country.name_fr')

    class Meta:
        model = CustomUser
        fields = ['avatar_thumbnail', 'first_name', 'last_name', 'gender',
                  'birth_date', 'city', 'country']


class BaseBlockedUsersListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    # Blocked user
    blocked_user_pk = serializers.IntegerField(source='user_blocked.pk')
    blocked_user_first_name = serializers.CharField(source='user_blocked.first_name')
    blocked_user_last_name = serializers.CharField(source='user_blocked.last_name')
    blocked_user_avatar = serializers.CharField(source='user_blocked.get_absolute_avatar_thumbnail')

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseUserAddressesListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    title = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField(source='city.name_fr')
    zip_code = serializers.IntegerField()
    country = serializers.CharField(source='country.name_fr')
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
    class Meta:
        model = UserAddress
        fields = ['pk', 'user', 'title', 'first_name',
                  'last_name', 'address', 'city', 'zip_code',
                  'country', 'phone', 'email']


class BaseUserAddressPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['title', 'first_name',
                  'last_name', 'address', 'city', 'zip_code',
                  'country', 'phone', 'email']

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.address = validated_data.get('address', instance.address)
        instance.city = validated_data.get('city', instance.city)
        instance.zip_code = validated_data.get('zip_code', instance.zip_code)
        instance.country = validated_data.get('country', instance.country)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance


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
