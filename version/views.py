from rest_framework.views import APIView
from rest_framework import permissions
from .models import Version, VirementData
from version.serializers import VersionSerializer, VirementDataSerializer, NewsLetterSerializer
# from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response


class GetVersionView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        version = Version.objects.all().first()
        serializer = VersionSerializer(version)
        # data = 'Error simulation'
        return Response(data=serializer.data, status=status.HTTP_200_OK)
        # raise ValidationError({'error': ['Error simulation testing state']})


class GetAdminVirementData(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request, *args, **kwargs):
        virement_data = VirementData.objects.all().first()
        serializer = VirementDataSerializer(virement_data)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class NewsLetterView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        email = request.data.get('email')
        serializer = NewsLetterSerializer(data={
            'email': email
        })
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_204_NO_CONTENT)
