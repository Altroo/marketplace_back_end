from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class RatingsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        pass
