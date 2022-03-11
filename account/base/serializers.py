from rest_framework import serializers
from account.models import CustomUser
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
