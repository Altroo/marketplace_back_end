from rest_framework import serializers
from blog.models import Blog
from Qaryb_API.settings import API_URL, CKEDITOR_UPLOAD_PATH


class BaseBlogPagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ['page_url', 'title', 'created_date']


SEARCH_PATTERN = f'src="/media/{CKEDITOR_UPLOAD_PATH}'
REPLACE_WITH = f'src="{API_URL}/media/{CKEDITOR_UPLOAD_PATH}'


class FixAbsolutePathSerializer(serializers.Field):

    def to_internal_value(self, data):
        pass

    def to_representation(self, value):
        text = value.replace(SEARCH_PATTERN, REPLACE_WITH)
        return text


class BaseBlogPageSerializer(serializers.ModelSerializer):
    content = FixAbsolutePathSerializer()
    background_image = serializers.CharField(source='get_absolute_background_img')

    class Meta:
        model = Blog
        fields = ['pk', 'page_url', 'background_image', 'background_image_alt',
                  'title', 'tags', 'header', 'content',
                  'page_meta_description', 'created_date']



