from django.db.models import Model
from django.db import models
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver
from account.models import CustomUser
from chat.models import Status


class Version(Model):
    current_version = models.CharField(verbose_name='Global version', max_length=255, blank=True, null=True)
    # android_link = CharField(verbose_name='Android store link', max_length=255, blank=True, null=True)
    # ios_link = CharField(verbose_name='iOS store link', max_length=255, blank=True, null=True)
    # android_version = CharField(verbose_name='Android version', max_length=255, blank=True, null=True)
    # ios_version = CharField(verbose_name='iOS version', max_length=255, blank=True, null=True)
    maintenance = models.BooleanField(verbose_name='Maintenance', default=False)

    def __str__(self):
        return 'Current version : {}'.format(self.current_version)

    class Meta:
        verbose_name_plural = "Version"


@receiver(post_save, sender=Version)
def check_maintenance(sender, instance, created, raw, using, update_fields, **kwargs):
    channel_layer = get_channel_layer()
    online_users = Status.objects.filter(online=True)
    if instance.maintenance:
        for user in online_users:
            event = {
                "type": "recieve_group_message",
                "message": {
                    "type": "MAINTENANCE",
                    "recipient": user.user.pk,
                    "maintenance": True
                }
            }
            async_to_sync(channel_layer.group_send)("%s" % user.user.id, event)
    else:
        for user in online_users:
            event = {
                "type": "recieve_group_message",
                "message": {
                    "type": "MAINTENANCE",
                    "recipient": user.user.pk,
                    "maintenance": False
                }
            }
            async_to_sync(channel_layer.group_send)("%s" % user.user.id, event)


class VirementData(Model):
    email = models.EmailField(verbose_name='Email address', blank=False, null=False, max_length=255)
    domiciliation = models.CharField(verbose_name='Domiciliation', blank=False, null=False, max_length=255)
    numero_de_compte = models.CharField(verbose_name='N° de compte', blank=False, null=False, max_length=255)
    titulaire_du_compte = models.CharField(verbose_name='Titulaire du compte', blank=False, null=False, max_length=255)
    numero_rib = models.CharField(verbose_name='N° du RIB', blank=False, null=False, max_length=255)
    identifiant_swift = models.CharField(verbose_name='Identifiant SWIFT', blank=False, null=False, max_length=255)

    def __str__(self):
        return '{} - {}'.format(self.email, self.numero_de_compte)

    class Meta:
        verbose_name = 'Virement admin data'
        verbose_name_plural = 'Virement admin data'
        ordering = ('-pk',)
