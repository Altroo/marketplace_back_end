from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from notifications.models import Notifications
from .serializers import BaseNotificationsSerializer, BaseNotificationsPatchSerializer


class NotificationView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        user_notifs = Notifications.objects.filter(user=user).order_by('-created_date')
        serializer = BaseNotificationsSerializer(user_notifs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def patch(request, *args, **kwargs):
        user = request.user
        notif_pk = request.data.get('pk')
        try:
            user_notif = Notifications.objects.get(pk=notif_pk, user=user)
            serializer = BaseNotificationsPatchSerializer(data={
                'viewed': True,
            }, partial=True)
            if serializer.is_valid():
                serializer.update(user_notif, serializer.validated_data)
                return Response(status=status.HTTP_204_NO_CONTENT)
        except Notifications.DoesNotExist:
            errors = {"error": ["Notification Doesn't exist!"]}
            raise ValidationError(errors)
