from django.db.models import Q
from rest_framework.exceptions import ValidationError
from account.models import CustomUser, BlockedUsers
from rest_framework.viewsets import ModelViewSet
from chat.base.serializers import BaseMessageModelSerializer, BaseConversationsSerializer, \
    BaseArchiveConversationSerializer
from chat.models import MessageModel, ArchivedConversations
from .pagination import BaseMessagePagination
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Max


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
class BaseChatConversationView(APIView, PageNumberPagination):
    permission_classes = (permissions.IsAuthenticated,)
    page_size = 10

    def get_blocked_users(self):
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

    def get_archived_conversations(self):
        archived_conversations_users = ArchivedConversations.objects.filter(user=self.request.user).values('recipient')
        archived_conversations_list = set()
        for archived_conversation in archived_conversations_users:
            archived_conversations_list.add(archived_conversation['recipient'])
        return tuple(archived_conversations_list)

    def get(self, request, *args, **kwargs):
        user = request.user
        archived_conversations = self.get_archived_conversations()
        blocked_users = self.get_blocked_users()
        chat_logs_users = MessageModel.objects.filter(Q(user=user) | Q(recipient=user)) \
            .exclude(Q(recipient__in=blocked_users + archived_conversations) | Q(user__in=blocked_users))
        chat_logs = chat_logs_users.values('user', 'recipient').annotate(messages__id__max=Max('id'))\
            .order_by('-messages__id__max')
        chat_logs_final = chat_logs
        for i in range(len(chat_logs)):
            sender = chat_logs[i]['user']
            receiver = chat_logs[i]['recipient']
            for j in range(i + 1, len(chat_logs)):
                if chat_logs[j]['user'] == receiver and chat_logs[j]['recipient'] == sender:
                    chat_logs_final = chat_logs_final.exclude(user=receiver, recipient=sender)
                    break
        messages = MessageModel.objects.filter(pk__in=chat_logs_final.values_list('messages__id__max', flat=True))
        page = self.paginate_queryset(request=request, queryset=messages)
        if page is not None:
            serializer = BaseConversationsSerializer(page, many=True, context={'user': user})
            return self.get_paginated_response(serializer.data)


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
