from rest_framework import serializers

from account.models import CustomUser
from auth_shop.base.models import AuthShop
from chat.base.models import MessageModel, Status
from rest_framework.serializers import (ModelSerializer,
                                        SerializerMethodField,
                                        CreateOnlyDefault, CurrentUserDefault)

# from chat.v2_0_0.tasks import NotifyMessageReceivedTaskV2


# Messages list
from Qaryb_API_new.settings import API_URL


class BaseMessageModelSerializer(ModelSerializer):
    initiator = SerializerMethodField()
    # attachment_link = serializers.CharField(source='get_absolute_attachment_img')
    # attachment_thumbnail_link = serializers.CharField(source='get_absolute_attachment_thumbnail')
    attachment_link = SerializerMethodField()
    attachment_thumbnail_link = SerializerMethodField()

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
        return instance.user.email

    # def save(self, **kwargs):
    #     assert hasattr(self, '_errors'), (
    #         'You must call `.is_valid()` before calling `.save()`.'
    #     )
    #
    #     assert not self.errors, (
    #         'You cannot call `.save()` on a serializer with invalid data.'
    #     )
    #
    #     # Guard against incorrect use of `serializer.save(commit=False)`
    #     assert 'commit' not in kwargs, (
    #         "'commit' is not a valid keyword argument to the 'save()' method. "
    #         "If you need to access data before committing to the database then "
    #         "inspect 'serializer.validated_data' instead. "
    #         "You can also pass additional keyword arguments to 'save()' if you "
    #         "need to set extra attributes on the saved model instance. "
    #         "For example: 'serializer.save(owner=request.user)'.'"
    #     )
    #
    #     assert not hasattr(self, '_data'), (
    #         "You cannot call `.save()` after accessing `serializer.data`."
    #         "If you need to access data before committing to the database then "
    #         "inspect 'serializer.validated_data' instead. "
    #     )
    #
    #     validated_data = {**self.validated_data, **kwargs}
    #
    #     if self.instance is not None:
    #         self.instance = self.update(self.instance, validated_data)
    #         assert self.instance is not None, (
    #             '`update()` did not return an object instance.'
    #         )
    #     else:
    #         self.instance = self.create(validated_data)
    #         assert self.instance is not None, (
    #             '`create()` did not return an object instance.'
    #         )
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

    class Meta:
        model = MessageModel
        fields = ('pk', 'user', 'initiator',
                  'recipient', 'created',
                  'body', 'attachment', 'attachment_thumbnail', 'attachment_link', 'attachment_thumbnail_link',
                  'viewed', 'viewed_timestamp')
        extra_kwargs = {
            'user': {
                'default': CreateOnlyDefault(
                    CurrentUserDefault()
                ),
            },
            'attachment': {'required': False, 'write_only': True},
            'attachment_thumbnail': {'required': False, 'write_only': True},
        }


# Conversations list
class BaseChatUserModelSerializer(ModelSerializer):
    last_message = SerializerMethodField()
    online = SerializerMethodField()
    user_pk = SerializerMethodField()
    user_avatar = SerializerMethodField()
    user_first_name = SerializerMethodField()
    user_last_name = SerializerMethodField()
    seen = SerializerMethodField()
    created_date = SerializerMethodField()
    shop_pk = SerializerMethodField()
    shop_name = SerializerMethodField()
    shop_avatar_thumbnail = SerializerMethodField()

    @staticmethod
    def get_user_pk(instance):
        return instance.pk

    @staticmethod
    def get_user_first_name(instance):
        user_receiver = CustomUser.objects.get(pk=instance.pk)
        return user_receiver.first_name

    @staticmethod
    def get_user_last_name(instance):
        user_receiver = CustomUser.objects.get(pk=instance.pk)
        return user_receiver.last_name

    @staticmethod
    def get_user_avatar(instance):
        user_receiver = CustomUser.objects.get(pk=instance.pk)
        return user_receiver.get_absolute_avatar_thumbnail

    def get_seen(self, instance):
        user = self.context.get('request').user
        result_msg_user = MessageModel.objects.filter(user=user, recipient=instance).order_by('created').last()
        result_msg_recipient = MessageModel.objects.filter(user=instance, recipient=user).order_by('created').last()
        if result_msg_user and result_msg_recipient:
            if result_msg_user.created > result_msg_recipient.created:
                return True
            else:
                return result_msg_recipient.viewed
        else:
            if result_msg_user:
                return True
            if result_msg_recipient:
                return result_msg_recipient.viewed

    def get_created_date(self, instance):
        user = self.context.get('request').user
        result_msg_user = MessageModel.objects.filter(user=user, recipient=instance).order_by('created').last()
        result_msg_recipient = MessageModel.objects.filter(user=instance, recipient=user).order_by('created').last()
        if result_msg_user and result_msg_recipient:
            if result_msg_user.created > result_msg_recipient.created:
                return result_msg_user.created
            else:
                return result_msg_recipient.created
        else:
            if result_msg_user:
                return result_msg_user.created
            if result_msg_recipient:
                return result_msg_recipient.created

    def get_last_message(self, instance):
        user = self.context.get('request').user
        result_msg_user = MessageModel.objects.filter(user=user, recipient=instance).order_by('created').last()
        result_msg_recipient = MessageModel.objects.filter(user=instance, recipient=user).order_by('created').last()
        if result_msg_user and result_msg_recipient:
            if result_msg_user.created > result_msg_recipient.created:
                if result_msg_user.attachment.name:
                    return 'Photo'
                return result_msg_user.body
            else:
                if result_msg_recipient.attachment.name:
                    return 'Photo'
                return result_msg_recipient.body
        else:
            if result_msg_user:
                if result_msg_user.attachment.name:
                    return 'Photo'
                return result_msg_user.body
            if result_msg_recipient:
                if result_msg_recipient.attachment.name:
                    return 'Photo'
                return result_msg_recipient.body

    @staticmethod
    def get_online(instance):
        try:
            if instance.status:
                return instance.status.online
            else:
                return False
        except Status.DoesNotExist:
            return False

    @staticmethod
    def get_shop_pk(instance):
        try:
            shop = AuthShop.objects.get(user=instance.pk).pk
        except AuthShop.DoesNotExist:
            shop = None
        return shop

    @staticmethod
    def get_shop_name(instance):
        try:
            shop = AuthShop.objects.get(user=instance.pk).shop_name
        except AuthShop.DoesNotExist:
            shop = None
        return shop

    @staticmethod
    def get_shop_avatar_thumbnail(instance):
        try:
            shop = AuthShop.objects.get(user=instance.pk).get_absolute_avatar_thumbnail
        except AuthShop.DoesNotExist:
            shop = None
        return shop

    class Meta:
        model = CustomUser
        fields = ['user_pk', 'user_avatar', 'user_first_name', 'user_last_name',
                  'last_message', 'seen', 'created_date', 'online',
                  'shop_pk', 'shop_name', 'shop_avatar_thumbnail']
