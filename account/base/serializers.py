from rest_framework import serializers
from account.models import CustomUser, BlockedUsers, ReportedUsers
from django.contrib.auth.password_validation import validate_password


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


class BaseProfileAvatarPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['avatar']

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class BaseProfilePutSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'gender', 'birth_date', 'city', 'country']

    def update(self, instance, validated_data):
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
    city = serializers.CharField(source='city.name_en')
    country = serializers.CharField(source='country.name_en')

    class Meta:
        model = CustomUser
        fields = ['avatar_thumbnail', 'first_name', 'last_name', 'gender',
                  'birth_date', 'city', 'country']


class BaseMyBlockedUsersListSerializer(serializers.Serializer):
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


class BaseMyBlockUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedUsers
        fields = ['user', 'user_blocked']


class BaseMyReportPostsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportedUsers
        fields = ['user', 'user_reported', 'report_reason']
