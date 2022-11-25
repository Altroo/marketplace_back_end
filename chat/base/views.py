from django.db.models import Q
from rest_framework.exceptions import ValidationError
from account.models import CustomUser, BlockedUsers
from rest_framework.viewsets import ModelViewSet
from chat.base.serializers import BaseMessageModelSerializer, BaseChatUserModelSerializer, \
    BaseArchiveConversationSerializer
from chat.models import MessageModel, ArchivedConversations
from .pagination import BaseMessagePagination, BaseConversationPagination
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


# Messages list of a target
class BaseMessageModelViewSet(ModelViewSet):
    serializer_class = BaseMessageModelSerializer
    allowed_methods = ('GET', 'HEAD', 'OPTIONS', 'POST' 'PATCH')
    pagination_class = BaseMessagePagination

    def get_queryset(self):
        pk = self.kwargs.get('pk', None)
        target = self.request.query_params.get('target', None)
        # Get messages of a target
        if target is not None:
            if pk is not None:
                return MessageModel.objects.filter(
                    Q(recipient=self.request.user, user__id=target) |
                    Q(recipient__id=target, user=self.request.user)) \
                    .filter(Q(recipient=self.request.user) |
                            Q(user=self.request.user),
                            Q(pk=pk))
            else:
                return MessageModel.objects.filter(
                    Q(recipient=self.request.user, user__id=target) |
                    Q(recipient__id=target, user=self.request.user))
        # Get a specific message by id
        else:
            if pk is not None:
                return MessageModel.objects.filter(Q(recipient=self.request.user) |
                                                   Q(user=self.request.user)) \
                    .filter(Q(recipient=self.request.user) |
                            Q(user=self.request.user),
                            Q(pk=pk))
            else:
                return MessageModel.objects.filter(Q(recipient=self.request.user) |
                                                   Q(user=self.request.user))
        # if target is not None:
        #     if pk is not None:
        #         return MessageModel.objects.filter(
        #             Q(recipient=self.request.user, user__id=target) |
        #             Q(recipient__id=target, user=self.request.user)).exclude(body='K8Fe6DoFgl9Xt0') \
        #             .filter(Q(recipient=self.request.user) |
        #                     Q(user=self.request.user),
        #                     Q(pk=pk)).exclude(body='K8Fe6DoFgl9Xt0')
        #     else:
        #         return MessageModel.objects.filter(
        #             Q(recipient=self.request.user, user__id=target) |
        #             Q(recipient__id=target, user=self.request.user)).exclude(body='K8Fe6DoFgl9Xt0')
        # # Get a specific message by id
        # else:
        #     if pk is not None:
        #         return MessageModel.objects.filter(Q(recipient=self.request.user) |
        #                                            Q(user=self.request.user)).exclude(body='K8Fe6DoFgl9Xt0') \
        #             .filter(Q(recipient=self.request.user) |
        #                     Q(user=self.request.user),
        #                     Q(pk=pk)).exclude(body='K8Fe6DoFgl9Xt0')
        #     else:
        #         return MessageModel.objects.filter(Q(recipient=self.request.user) |
        #                                            Q(user=self.request.user)).exclude(body='K8Fe6DoFgl9Xt0')


# Conversations list
class BaseChatUserModelViewSet(ModelViewSet):
    serializer_class = BaseChatUserModelSerializer
    allowed_methods = ('GET', 'HEAD', 'OPTIONS')
    pagination_class = BaseConversationPagination

    def get_queryset(self):
        my_set = set()
        result_msg_user = MessageModel.objects.filter(user=self.request.user)
        result_msg_recipient = MessageModel.objects.filter(recipient=self.request.user)
        for i in result_msg_user:
            if i.recipient is not None and i != self.request.user.pk:
                my_set.add(i.recipient.pk)
        for i in result_msg_recipient:
            if i.user is not None and i != self.request.user.pk:
                my_set.add(i.user.pk)

        def get_blocked_users():
            """
            Blocked users
            """
            blocked_user_sender = BlockedUsers.objects.filter(user=self.request.user).values('user_blocked')
            blocked_user_receiver = BlockedUsers.objects.filter(user_blocked=self.request.user).values('user')
            inactive_users = CustomUser.objects.filter(is_active=False).values('pk')
            blocked_list = set()
            for block in blocked_user_sender:
                blocked_list.add(block['user_blocked'])
            for block in blocked_user_receiver:
                blocked_list.add(block['user'])
            for inactive_user in inactive_users:
                blocked_list.add(inactive_user['pk'])
            return tuple(blocked_list)

        def get_archived_conversations():
            archived_conversations_users = ArchivedConversations.objects.filter(user=self.request.user)\
                .values('recipient')
            archived_conversations_list = set()
            for archived_conversation in archived_conversations_users:
                archived_conversations_list.add(archived_conversation['recipient'])
            return tuple(archived_conversations_list)

        blocked_users = get_blocked_users()
        archived_conversations = get_archived_conversations()
        return CustomUser.objects.filter(id__in=my_set).exclude(pk__in=blocked_users)\
            .exclude(pk__in=archived_conversations)

    def list(self, request, *args, **kwargs):
        """
        Return all user data accept for the user
        who is making this request.
        """
        response = super(BaseChatUserModelViewSet, self).list(request, args, kwargs)
        # created from the serializer method field
        response.data['results'].sort(reverse=True, key=lambda key_needed: key_needed['created'])
        return response


# Archive conversation
class BaseArchiveConversationView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        user_pk = request.user.pk
        receiver = request.data.get('recipient')
        # Check if conversation already archived.
        try:
            ArchivedConversations.objects.get(user=user_pk, recipient=receiver)
            errors = {"error": ["Conversation already archived."]}
            raise ValidationError(errors)
        # Else add to archive
        except ArchivedConversations.DoesNotExist:
            serializer = BaseArchiveConversationSerializer(data={
                "user": user_pk,
                "recipient": receiver,
            })
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise ValidationError(serializer.errors)
