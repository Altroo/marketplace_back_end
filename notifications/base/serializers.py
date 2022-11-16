from rest_framework import serializers
from notifications.models import Notifications


class BaseNotificationsSerializer(serializers.ModelSerializer):
    # fixes ws type conflict
    type_ = serializers.CharField(source='type')

    class Meta:
        model = Notifications
        fields = ['pk', 'user', 'body', 'type_', 'viewed', 'created_date']

        extra_kwargs = {
            'user': {'write_only': True},
            'pk': {'read_only': True},
        }


class BaseNotificationsPatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notifications
        fields = ['viewed']
