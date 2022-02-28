from rest_framework import serializers

from places.base.models import Country, City


class BasePlaceBaseSerializer(serializers.ModelSerializer):
    """
    Place Base serializer
    """
    name = serializers.CharField(source='language_name')

    class Meta:
        fields = (
            'pk',
            'name',
        )


class BaseCountrySerializer(BasePlaceBaseSerializer):
    """
    Country serializer
    """

    class Meta(BasePlaceBaseSerializer.Meta):
        model = Country
        fields = BasePlaceBaseSerializer.Meta.fields + ('code',)


class BaseCitySerializer(BasePlaceBaseSerializer):
    """
    City serializer
    """

    class Meta(BasePlaceBaseSerializer.Meta):
        model = City
