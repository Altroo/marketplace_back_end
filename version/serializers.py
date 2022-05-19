from rest_framework import serializers
from version.models import Version


class VersionSerializer(serializers.ModelSerializer):
    current_version = serializers.CharField()
    # android_version = serializers.CharField()
    # ios_version = serializers.CharField()
    # android_id = serializers.CharField(source='android_link')
    # ios_id = serializers.CharField(source='ios_link')
    maintenance = serializers.BooleanField()

    class Meta:
        model = Version
        fields = ['current_version', 'maintenance']
