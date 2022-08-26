from account.models import CustomUser
from django.db.models import (Model, TextField, DateTimeField, ForeignKey,
                              CASCADE, BooleanField, OneToOneField, ImageField, SET_NULL)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from os import path
from uuid import uuid4
from Qaryb_API.settings import API_URL
from io import BytesIO
from django.core.files.base import ContentFile
from shop.base.utils import ImageProcessor


def chat_img_directory_path(instance, filename):
    filename, file_extension = path.splitext(filename)
    return path.join('chat/', str(uuid4()) + file_extension)


# TODO change to just Message
class MessageModel(Model):
    user = ForeignKey(CustomUser, on_delete=SET_NULL, verbose_name='Sender', related_name='sent_messages',
                      db_index=True, null=True)
    recipient = ForeignKey(CustomUser, on_delete=SET_NULL, verbose_name='Receiver', related_name='recevied_messages',
                           db_index=True, null=True)
    created = DateTimeField('Created date', auto_now_add=True, editable=False, db_index=True)
    body = TextField('Body', null=True, blank=True)
    attachment = ImageField(null=True, blank=True, upload_to=chat_img_directory_path, default=None)
    attachment_thumbnail = ImageField(null=True, blank=True, upload_to=chat_img_directory_path, default=None)
    viewed = BooleanField(default=False)
    viewed_timestamp = DateTimeField('Viewed Timestamp', auto_now=True, editable=False)

    def __nonzero__(self):
        return bool(self.attachment)

    def __str__(self):
        try:
            email_sender = self.user.email
        except AttributeError:
            email_sender = 'ACCOUNT DELETED'
        try:
            email_receiver = self.recipient.email
        except AttributeError:
            email_receiver = 'ACCOUNT DELETED'
        return 'ID: {} - Sender : {} - Receiver : {}'.format(self.pk, email_sender, email_receiver)

    async def notify_seen_async(self):
        channel_layer = get_channel_layer()
        event = {
            "type": "recieve_group_message",
            "message": {
                "type": "MSG_SEEN",
                "pk": self.id,
                "initiator": self.user.id,
                "recipient": self.recipient.id,
            }
        }
        await channel_layer.group_send("%s" % self.user.id, event)

    def notify_seen_sync(self):
        channel_layer = get_channel_layer()
        event = {
            "type": "recieve_group_message",
            "message": {
                "type": "MSG_SEEN",
                "pk": self.id,
                "initiator": self.user.id,
                "recipient": self.recipient.id,
            }
        }
        async_to_sync(channel_layer.group_send)("%s" % self.user.id, event)

    def save_image(self, field_name, image):
        if not isinstance(image, BytesIO):
            return

        getattr(self, field_name).save(f'{str(uuid4())}.jpeg',
                                       ContentFile(image.getvalue()),
                                       save=True)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ('-created',)

    @property
    def get_absolute_attachment_img(self):
        if self.attachment:
            return "{0}/media{1}".format(API_URL, self.attachment.url)
        return None

    @property
    def get_absolute_attachment_thumbnail(self):
        if self.attachment_thumbnail:
            return "{0}/media{1}".format(API_URL, self.attachment_thumbnail.url)
        return None


@receiver(post_save, sender=MessageModel)
def create_thumbnail(sender, instance, created, raw, using, update_fields, **kwargs):
    if created and instance.attachment.name:
        image_processor = ImageProcessor()
        loaded_img = image_processor.load_image(instance.attachment.path)
        resized_thumb = image_processor.image_resize(loaded_img, width=300, height=300)
        img_thumbnail = image_processor.from_img_to_io(resized_thumb, 'JPEG')
        instance.save_image('attachment_thumbnail', img_thumbnail)


class ArchivedConversations(Model):
    user = ForeignKey(CustomUser, on_delete=SET_NULL, verbose_name='Sender',
                      related_name='user_archived_conversation', null=True)
    recipient = ForeignKey(CustomUser, on_delete=SET_NULL, verbose_name='Receiver',
                           related_name='receiver_archived_conversation', null=True)

    def __str__(self):
        try:
            user = self.user.email
        except AttributeError:
            user = 'ACCOUNT DELETED'
        try:
            recipient = self.recipient.email
        except AttributeError:
            recipient = 'ACCOUNT DELETED'
        return 'ID: {} - User : {} - Receiver : {}'.format(self.pk, user, recipient)

    class Meta:
        verbose_name = "Archived Conversation"
        verbose_name_plural = "Archived Conversations"


class Status(Model):
    user = OneToOneField(CustomUser, on_delete=CASCADE, verbose_name='user', related_name="status")
    last_update = DateTimeField(auto_now=True, null=False, blank=False)
    online = BooleanField(default=False)

    def __str__(self):
        return "{} - {}".format(self.pk, self.online)

    class Meta:
        verbose_name = "Status"
        verbose_name_plural = "Status"


@receiver(pre_save, sender=MessageModel)
def notify_message(sender, instance, raw, using, update_fields, **kwargs):
    if instance.pk is not None:
        old_instance = MessageModel.objects.get(id=instance.id)
        if old_instance.viewed is False and instance.viewed is True:
            try:
                instance.notify_seen_sync()
            except RuntimeError:
                instance.notify_seen_async()
            old_unseen_messages = MessageModel.objects.filter(user=instance.user,
                                                              recipient=instance.recipient,
                                                              viewed=False)
            for message in old_unseen_messages:
                try:
                    message.notify_seen_sync()
                except RuntimeError:
                    message.notify_seen_async()
            old_unseen_messages.update(viewed=True)
        else:
            pass
    else:
        pass
