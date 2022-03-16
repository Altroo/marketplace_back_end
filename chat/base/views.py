from django.db.models import Q
from account.models import CustomUser, BlockedUsers
from rest_framework.viewsets import ModelViewSet
from chat.base.serializers import BaseMessageModelSerializer, BaseChatUserModelSerializer
from chat.base.models import MessageModel
from .pagination import BaseMessagePagination, BaseConversationPagination


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


class BaseChatUserModelViewSet(ModelViewSet):
    serializer_class = BaseChatUserModelSerializer
    allowed_methods = ('GET', 'HEAD', 'OPTIONS')
    pagination_class = BaseConversationPagination

    def get_queryset(self):
        my_set = set()
        result_msg_user = MessageModel.objects.filter(user=self.request.user)
        result_msg_recipient = MessageModel.objects.filter(recipient=self.request.user)
        for i in result_msg_user:
            if i != self.request.user.pk:
                my_set.add(i.recipient.pk)
        for i in result_msg_recipient:
            if i != self.request.user.pk:
                my_set.add(i.user.pk)

        def get_blocked_users():
            """
            Blocked users
            """
            blocked_user_sender = BlockedUsers.objects.filter(user=self.request.user).values('user_blocked')
            blocked_user_receiver = BlockedUsers.objects.filter(user_blocked=self.request.user).values('user')
            inactive_users = CustomUser.objects.filter(is_active=False).values('pk')
            my_blocked_list = set()
            for block in blocked_user_sender:
                my_blocked_list.add(block['user_blocked'])
            for block in blocked_user_receiver:
                my_blocked_list.add(block['user'])
            for inactive_user in inactive_users:
                my_blocked_list.add(inactive_user['pk'])
            return tuple(my_blocked_list)
        blocked_users = get_blocked_users()
        return CustomUser.objects.filter(id__in=my_set).exclude(pk__in=blocked_users)

    def list(self, request, *args, **kwargs):
        """
        Return all user data accept for the user
        who is making this request.
        """
        response = super(BaseChatUserModelViewSet, self).list(request, args, kwargs)
        # created_date from the serializer method field
        response.data['results'].sort(reverse=True, key=lambda key_needed: key_needed['created_date'])

        return response

