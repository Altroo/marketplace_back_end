from rest_framework import serializers
from seo_pages.models import DefaultSeoPage


class BaseDefaultSeoPageUrlsOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = DefaultSeoPage
        fields = ['page_url']


class BaseDefaultSeoPageSerializer(serializers.ModelSerializer):

    class Meta:
        model = DefaultSeoPage
        fields = ['pk', 'page_url', 'title', 'tags', 'header', 'paragraphe', 'page_meta_description']

