from django.db import models
from django.db.models import Model
from account.models import CustomUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

NOTIFICATION_CHOICES = (
    ('', 'Unset'),
    ('SA', 'Subscription activated'),
    ('OR', 'Order received'),
    ('OA', 'Order accepted'),
    ('CS', 'Order cancelled by the seller'),
    ('CB', 'Order cancelled by the buyer'),
)


class Notifications(Model):
    user = models.ForeignKey(CustomUser,
                             verbose_name='User',
                             on_delete=models.CASCADE,
                             related_name='user_notifications')
    body = models.CharField(verbose_name='Notification Body', max_length=255,
                            default=None, null=True, blank=True)
    type = models.CharField(max_length=2, choices=NOTIFICATION_CHOICES, default='', blank=True, null=True)
    viewed = models.BooleanField(default=False, verbose_name='Vue')
    # Dates
    created_date = models.DateTimeField(verbose_name='Created date', editable=False, auto_now_add=True, db_index=True)

    def __str__(self):
        return '{} - {}'.format(self.user.first_name, self.user.last_name)

    @property
    def get_created_date(self):
        created_date = self.created_date.isoformat()
        return created_date[:-6] + 'Z'

    async def ws_notification_async(self):
        channel_layer = get_channel_layer()
        event = {
            "type": "recieve_group_message",
            "message": {
                "type": "NOTIFICATION",
                "pk": self.pk,
                "body": self.body,
                "type_": self.type,
                "viewed": self.viewed,
                "created_date": self.get_created_date,
            }
        }
        await channel_layer.group_send("%s" % self.user.id, event)

    def ws_notification_sync(self):
        channel_layer = get_channel_layer()
        event = {
            "type": "recieve_group_message",
            "message": {
                "type": "NOTIFICATION",
                "pk": self.pk,
                "body": self.body,
                "type_": self.type,
                "viewed": self.viewed,
                "created_date": self.get_created_date,
            }
        }
        async_to_sync(channel_layer.group_send)("%s" % self.user.id, event)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ('-created_date',)


@receiver(post_save, sender=Notifications)
def send_notification_ws(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        try:
            instance.ws_notification_sync()
        except RuntimeError:
            instance.ws_notification_async()
