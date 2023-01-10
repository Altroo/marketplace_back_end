from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from blog.base.serializers import BaseBlogPagesSerializer, BaseBlogPageSerializer
from blog.models import Blog


class GetAvailableBlogPageUrlsView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        blog_pages = Blog.objects.filter(indexed=True)
        serializer = BaseBlogPagesSerializer(blog_pages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetBlogPageContent(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        page_url = kwargs.get('page_url')
        try:
            blog_page = Blog.objects.get(page_url=page_url)
            serializer = BaseBlogPageSerializer(blog_page)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Blog.DoesNotExist:
            errors = {"error": ["Blog page not found."]}
            raise ValidationError(errors)
