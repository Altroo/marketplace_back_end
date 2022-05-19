from rest_framework.views import APIView
from rest_framework import permissions
from .models import Version
from version.serializers import VersionSerializer
from rest_framework import status
from rest_framework.response import Response


class GetVersionView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        version = Version.objects.all().first()
        serializer = VersionSerializer(version)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
