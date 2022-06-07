from rest_framework import serializers
from models import Cities


class BaseCitiesListSerializer(serializers.ModelSerializer):
    # pk = serializers.IntegerField(source='city.pk')
    # city_en = serializers.CharField(source='city.name_en')
    # city_fr = serializers.CharField(source='city.name_fr')
    # city_ar = serializers.CharField(source='city.name_ar')

    class Meta:
        model = Cities
        # fields = ['pk', 'city_en', 'city_fr', 'city_ar']
        fields = ['pk', 'city_fr']
