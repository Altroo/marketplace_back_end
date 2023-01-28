from typing import Union
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import QuerySet
from shop.models import AuthShop
from chat.models import MessageModel, Status, ArchivedConversations
from rest_framework import serializers
from shop.base.utils import Base64ImageField


# Messages list of a target
class BaseMessageModelSerializer(serializers.ModelSerializer):
    initiator = serializers.SerializerMethodField()
    attachment = Base64ImageField(
        max_length=None, use_url=True, required=False
    )

    attachment_link = serializers.SerializerMethodField()
    attachment_thumbnail_link = serializers.SerializerMethodField()

    @staticmethod
    def get_attachment_link(instance):
        if instance.attachment:
            return instance.get_absolute_attachment_img
        return None

    @staticmethod
    def get_attachment_thumbnail_link(instance):
        if instance.attachment_thumbnail:
            return instance.get_absolute_attachment_thumbnail
        return None

    @staticmethod
    def get_initiator(instance):
        try:
            shop = AuthShop.objects.get(user=instance.user.pk).shop_name
        except AuthShop.DoesNotExist:
            shop = instance.user.first_name + ' ' + instance.user.last_name
        return shop

    @staticmethod
    async def notify_message_received_async(instance):
        attachment_exist = instance.attachment.path if instance.attachment else None
        if attachment_exist is not None:
            body = 'Picture'
        else:
            body = instance.body
        event = {
            "type": "recieve_group_message",
            "message": {
                "type": "NEW_MESSAGE",
                "pk": instance.id,
                "initiator": instance.user.pk,
                "recipient": instance.recipient.pk,
                "body": body,
            }
        }
        channel_layer = get_channel_layer()
        await channel_layer.group_send("%s" % instance.recipient.id, event)

    @staticmethod
    def notify_message_received_sync(instance):
        attachment_exist = instance.attachment.path if instance.attachment else None
        if attachment_exist is not None:
            body = 'Picture'
        else:
            body = instance.body
        event = {
            "type": "recieve_group_message",
            "message": {
                "type": "NEW_MESSAGE",
                "pk": instance.id,
                "initiator": instance.user.pk,
                "recipient": instance.recipient.pk,
                "body": body,
            }
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("%s" % instance.recipient.pk, event)

    def save(self, **kwargs):
        assert hasattr(self, '_errors'), (
            'You must call `.is_valid()` before calling `.save()`.'
        )

        assert not self.errors, (
            'You cannot call `.save()` on a serializer with invalid data.'
        )

        # Guard against incorrect use of `serializer.save(commit=False)`
        assert 'commit' not in kwargs, (
            "'commit' is not a valid keyword argument to the 'save()' method. "
            "If you need to access data before committing to the database then "
            "inspect 'serializer.validated_data' instead. "
            "You can also pass additional keyword arguments to 'save()' if you "
            "need to set extra attributes on the saved model instance. "
            "For example: 'serializer.save(owner=request.user)'.'"
        )

        assert not hasattr(self, '_data'), (
            "You cannot call `.save()` after accessing `serializer.data`."
            "If you need to access data before committing to the database then "
            "inspect 'serializer.validated_data' instead. "
        )

        validated_data = {**self.validated_data, **kwargs}

        if self.instance is not None:
            self.instance = self.update(self.instance, validated_data)
            assert self.instance is not None, (
                '`update()` did not return an object instance.'
            )
        else:
            self.instance = self.create(validated_data)
            assert self.instance is not None, (
                '`create()` did not return an object instance.'
            )
            # Send WS message : added here to avoid sending duplicate sockets when attachment is added
            #         if self.instance.body != 'K8Fe6DoFgl9Xt0':
            #             attachment_exist = self.instance.attachment.path if self.instance.attachment else None
            #             notify_message_received = NotifyMessageReceivedTaskV2()
            #             notify_message_received.apply_async(args=(self.instance.id,
            #                                                       self.instance.user.pk,
            #                                                       self.instance.recipient.pk,
            #                                                       self.instance.body,
            #                                                       attachment_exist,
            #                                                       self.instance.user.first_name,
            #                                                       self.instance.user.last_name))
            #     return self.instance
            if self.instance.body or self.instance.attachment.name:
                try:
                    self.notify_message_received_sync(instance=self.instance)
                except RuntimeError:
                    self.notify_message_received_async(instance=self.instance)
                # Remove conversation from archives if exists
                try:
                    # instance.user.pk
                    # instance.recipient.pk
                    archived_conversations_sender = ArchivedConversations.objects.get(
                        user=self.instance.user.pk, recipient=self.instance.recipient.pk)
                    archived_conversations_sender.delete()
                except ArchivedConversations.DoesNotExist:
                    pass
                try:
                    archived_conversations_receiver = ArchivedConversations.objects.get(
                        user=self.instance.recipient.pk, recipient=self.instance.user.pk)
                    archived_conversations_receiver.delete()
                except ArchivedConversations.DoesNotExist:
                    pass
        return self.instance

    class Meta:
        model = MessageModel
        fields = ('pk', 'user', 'initiator',
                  'recipient', 'created',
                  'body', 'attachment', 'attachment_thumbnail', 'attachment_link', 'attachment_thumbnail_link',
                  'viewed')
        extra_kwargs = {
            'user': {
                'default': serializers.CreateOnlyDefault(
                    serializers.CurrentUserDefault()
                ),
            },
            'attachment': {'required': False, 'write_only': True},
            'attachment_thumbnail': {'required': False, 'write_only': True},
        }


class BaseConversationsSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    body = serializers.SerializerMethodField()
    viewed = serializers.SerializerMethodField()
    created = serializers.DateTimeField()

    user_pk = serializers.SerializerMethodField()
    user_first_name = serializers.SerializerMethodField()
    user_last_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()

    online = serializers.SerializerMethodField()
    shop_pk = serializers.SerializerMethodField()
    shop_name = serializers.SerializerMethodField()
    shop_avatar_thumbnail = serializers.SerializerMethodField()

    def get_user_pk(self, instance: Union[QuerySet, MessageModel]):
        user = self.context.get("user")
        if instance.user == user:
            return instance.recipient.pk
        else:
            return instance.user.pk

    def get_user_first_name(self, instance):
        user = self.context.get("user")
        if instance.user == user:
            return instance.recipient.first_name
        else:
            return instance.user.first_name

    def get_user_last_name(self, instance):
        user = self.context.get("user")
        if instance.user == user:
            return instance.recipient.last_name
        else:
            return instance.user.last_name

    def get_user_avatar(self, instance):
        user = self.context.get("user")
        if instance.user == user:
            return instance.recipient.get_absolute_avatar_thumbnail
        else:
            return instance.user.get_absolute_avatar_thumbnail

    def get_online(self, instance):
        user = self.context.get("user")
        if instance.user == user:
            try:
                if instance.recipient.status:
                    return instance.recipient.status.online
                else:
                    return False
            except Status.DoesNotExist:
                return False
        else:
            try:
                if instance.user.status:
                    return instance.user.status.online
                else:
                    return False
            except Status.DoesNotExist:
                return False

    def get_shop_pk(self, instance):
        user = self.context.get("user")
        if instance.user == user:
            try:
                shop = AuthShop.objects.get(user=instance.recipient.pk).pk
            except AuthShop.DoesNotExist:
                shop = None
            return shop
        else:
            try:
                shop = AuthShop.objects.get(user=instance.user.pk).pk
            except AuthShop.DoesNotExist:
                shop = None
            return shop

    def get_shop_name(self, instance):
        user = self.context.get("user")
        if instance.user == user:
            try:
                shop = AuthShop.objects.get(user=instance.recipient.pk).shop_name
            except AuthShop.DoesNotExist:
                shop = None
            return shop
        else:
            try:
                shop = AuthShop.objects.get(user=instance.user.pk).shop_name
            except AuthShop.DoesNotExist:
                shop = None
            return shop

    def get_shop_avatar_thumbnail(self, instance):
        user = self.context.get("user")
        if instance.user == user:
            try:
                shop = AuthShop.objects.get(user=instance.recipient.pk).get_absolute_avatar_thumbnail
            except AuthShop.DoesNotExist:
                shop = None
            return shop
        else:
            try:
                shop = AuthShop.objects.get(user=instance.user.pk).get_absolute_avatar_thumbnail
            except AuthShop.DoesNotExist:
                shop = None
            return shop

    def get_viewed(self, instance):
        user = self.context.get("user")
        if instance.user == user:
            return True
        else:
            return instance.viewed

    @staticmethod
    def get_body(instance):
        if instance.attachment.name:
            return 'Photo'
        if len(str(instance.body)) < 30:
            return instance.body
        else:
            return instance.body[0:30] + '...'

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# # Conversations list
# class BaseChatUserModelSerializer(serializers.ModelSerializer):
#     pk = serializers.SerializerMethodField()
#     body = serializers.SerializerMethodField()
#     online = serializers.SerializerMethodField()
#     user_pk = serializers.SerializerMethodField()
#     user_avatar = serializers.SerializerMethodField()
#     user_first_name = serializers.SerializerMethodField()
#     user_last_name = serializers.SerializerMethodField()
#     viewed = serializers.SerializerMethodField()
#     created = serializers.SerializerMethodField()
#     shop_pk = serializers.SerializerMethodField()
#     shop_name = serializers.SerializerMethodField()
#     shop_avatar_thumbnail = serializers.SerializerMethodField()
#
#     @staticmethod
#     def get_user_pk(instance):
#         return instance.pk
#
#     @staticmethod
#     def get_user_first_name(instance):
#         user_receiver = CustomUser.objects.get(pk=instance.pk)
#         return user_receiver.first_name
#
#     @staticmethod
#     def get_user_last_name(instance):
#         user_receiver = CustomUser.objects.get(pk=instance.pk)
#         return user_receiver.last_name
#
#     @staticmethod
#     def get_user_avatar(instance):
#         user_receiver = CustomUser.objects.get(pk=instance.pk)
#         return user_receiver.get_absolute_avatar_thumbnail
#
#     def get_viewed(self, instance):
#         user = self.context.get('request').user
#         result_msg_user = MessageModel.objects.filter(user=user, recipient=instance).order_by('-created').first()
#         result_msg_recipient = MessageModel.objects.filter(user=instance, recipient=user).order_by('-created').first()
#         if result_msg_user and result_msg_recipient:
#             if result_msg_user.created > result_msg_recipient.created:
#                 return True
#             else:
#                 return result_msg_recipient.viewed
#         else:
#             if result_msg_user:
#                 return True
#             if result_msg_recipient:
#                 return result_msg_recipient.viewed
#
#     def get_created(self, instance):
#         user = self.context.get('request').user
#         result_msg_user = MessageModel.objects.filter(user=user, recipient=instance).order_by('-created').first()
#         result_msg_recipient = MessageModel.objects.filter(user=instance, recipient=user).order_by('-created').first()
#         if result_msg_user and result_msg_recipient:
#             if result_msg_user.created > result_msg_recipient.created:
#                 return result_msg_user.created
#             else:
#                 return result_msg_recipient.created
#         else:
#             if result_msg_user:
#                 return result_msg_user.created
#             if result_msg_recipient:
#                 return result_msg_recipient.created
#
#     def get_body(self, instance):
#         user = self.context.get('request').user
#         result_msg_user = MessageModel.objects.filter(user=user, recipient=instance).order_by('-created').first()
#         result_msg_recipient = MessageModel.objects.filter(user=instance, recipient=user).order_by('-created').first()
#         if result_msg_user and result_msg_recipient:
#             if result_msg_user.created > result_msg_recipient.created:
#                 if result_msg_user.attachment.name:
#                     return 'Photo'
#                 if len(str(result_msg_user.body)) < 30:
#                     return result_msg_user.body
#                 else:
#                     return result_msg_user.body[0:30] + '...'
#             else:
#                 if result_msg_recipient.attachment.name:
#                     return 'Photo'
#                 if len(str(result_msg_recipient.body)) < 30:
#                     return result_msg_recipient.body
#                 else:
#                     return result_msg_recipient.body[0:30] + '...'
#         else:
#             if result_msg_user:
#                 if result_msg_user.attachment.name:
#                     return 'Photo'
#                 if len(str(result_msg_user.body)) < 30:
#                     return result_msg_user.body
#                 else:
#                     return result_msg_user.body[0:30] + '...'
#             if result_msg_recipient:
#                 if result_msg_recipient.attachment.name:
#                     return 'Photo'
#                 if len(str(result_msg_recipient.body)) < 30:
#                     return result_msg_recipient.body
#                 else:
#                     return result_msg_recipient.body[0:30] + '...'
#
#     @staticmethod
#     def get_online(instance):
#         try:
#             if instance.status:
#                 return instance.status.online
#             else:
#                 return False
#         except Status.DoesNotExist:
#             return False
#
#     @staticmethod
#     def get_shop_pk(instance):
#         try:
#             shop = AuthShop.objects.get(user=instance.pk).pk
#         except AuthShop.DoesNotExist:
#             shop = None
#         return shop
#
#     @staticmethod
#     def get_shop_name(instance):
#         try:
#             shop = AuthShop.objects.get(user=instance.pk).shop_name
#         except AuthShop.DoesNotExist:
#             shop = None
#         return shop
#
#     @staticmethod
#     def get_shop_avatar_thumbnail(instance):
#         try:
#             shop = AuthShop.objects.get(user=instance.pk).get_absolute_avatar_thumbnail
#         except AuthShop.DoesNotExist:
#             shop = None
#         return shop
#
#     def get_pk(self, instance):
#         user = self.context.get('request').user
#         result_msg_user = MessageModel.objects.filter(user=user, recipient=instance).order_by('-created').first()
#         result_msg_recipient = MessageModel.objects.filter(user=instance, recipient=user).order_by('-created').first()
#         if result_msg_user and result_msg_recipient:
#             if result_msg_user.created > result_msg_recipient.created:
#                 return result_msg_user.pk
#             else:
#                 return result_msg_recipient.pk
#         else:
#             if result_msg_user:
#                 return result_msg_user.pk
#             if result_msg_recipient:
#                 return result_msg_recipient.pk
#
#     class Meta:
#         model = CustomUser
#         fields = ['pk', 'user_pk', 'user_avatar', 'user_first_name', 'user_last_name',
#                   'body', 'viewed', 'created', 'online',
#                   'shop_pk', 'shop_name', 'shop_avatar_thumbnail']
#         extra_kwargs = {
#             'pk': {'read_only': True}
#         }


class BaseArchiveConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivedConversations
        fields = ['user', 'recipient']
