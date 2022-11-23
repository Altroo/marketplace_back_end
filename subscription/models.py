from datetime import timedelta
from typing import Union
from uuid import uuid4

from django.db import models
from django.db.models import Model, QuerySet
from fpdf import FPDF

from places.models import Country
from shop.models import AuthShop
from offers.models import Offers
from django.utils import timezone
from os import path
from Qaryb_API.settings import API_URL
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notifications


def get_facture_path():
    return path.join('media/files/')


class SubscriptionChoices:
    SUBSCRIPTION_STATUS = (
        ('A', 'Accepted'),
        ('R', 'Rejected'),
        ('P', 'Processing'),
    )

    PROMO_CODE_STATUS = (
        ('V', 'Valid'),
        ('E', 'Expired'),
    )

    PROMO_CODE_TYPES = (
        ('P', 'Price'),
        ('S', 'Slots'),
    )

    PAYMENT_TYPE = (
        ('', 'Unset'),
        ('C', 'Carte'),
        ('V', 'Virement'),
    )


class AvailableSubscription(Model):
    nbr_article = models.PositiveIntegerField(verbose_name="Nombre d'article", blank=True, null=True, default=None)
    prix_ht = models.PositiveIntegerField(verbose_name="Prix abonnement HT/ans", blank=True, null=True, default=None)
    prix_ttc = models.PositiveIntegerField(verbose_name="Prix abonnement TTC/ans", blank=True, null=True, default=None)
    prix_unitaire_ht = models.PositiveIntegerField(verbose_name="Prix d'article HT/article", blank=True, null=True,
                                                   default=None)
    prix_unitaire_ttc = models.PositiveIntegerField(verbose_name="Prix d'article TTC/article", blank=True, null=True,
                                                    default=None)
    pourcentage = models.IntegerField(verbose_name="Réduction pourcentage", blank=True, null=True, default=None)

    # illimite = models.BooleanField(verbose_name='Illimité', default=False)

    def __str__(self):
        return '{} - {}'.format(self.nbr_article, self.prix_ttc)

    class Meta:
        verbose_name = 'Available subscription'
        verbose_name_plural = 'Available subscriptions'
        ordering = ('-pk',)


class PromoCodes(Model):
    promo_code = models.CharField(verbose_name='Promo code', max_length=6, unique=True)
    type_promo_code = models.CharField(verbose_name='Type promo code', max_length=1,
                                       choices=SubscriptionChoices.PROMO_CODE_TYPES,
                                       default='P')
    usage_unique = models.BooleanField(verbose_name='Usage unique', default=False)
    value = models.PositiveIntegerField(verbose_name="% price or nbr (depend on type)",
                                        blank=True, null=True, default=None)
    promo_code_status = models.CharField(verbose_name='Promo code status', max_length=1,
                                         choices=SubscriptionChoices.PROMO_CODE_STATUS,
                                         default='V')
    expiration_date = models.DateTimeField(verbose_name='Expiration date', default=None,
                                           blank=True, null=True)

    def __str__(self):
        return '{} - {}'.format(self.promo_code, self.get_type_promo_code_display())

    class Meta:
        verbose_name = 'Promo code'
        verbose_name_plural = 'Promo codes'
        ordering = ('-pk',)


class RequestedSubscriptions(Model):
    auth_shop = models.ForeignKey(AuthShop, on_delete=models.CASCADE,
                                  verbose_name='Auth Shop',
                                  related_name='auth_shop_requested_subscription')
    subscription = models.ForeignKey(AvailableSubscription, on_delete=models.CASCADE,
                                     verbose_name="Subscription picked",
                                     related_name='subscription_requested_subscription')
    company = models.CharField(verbose_name='Company', max_length=30, null=True, blank=True, default=None)
    ice = models.CharField(verbose_name='ICE', max_length=15, null=True, blank=True, default=None)
    first_name = models.CharField(verbose_name='First name', max_length=30, blank=True, null=True, default=None)
    last_name = models.CharField(verbose_name='Last name', max_length=30, blank=True, null=True, default=None)
    adresse = models.CharField(verbose_name='Adresse', max_length=30, blank=True, null=True, default=None)
    city = models.CharField(verbose_name='City', max_length=30, blank=True, null=True, default=None)
    code_postal = models.CharField(verbose_name='Code postal', max_length=30, blank=True, null=True, default=None)
    country = models.ForeignKey(Country, verbose_name='Country',
                                on_delete=models.CASCADE, related_name='country_requested_subscription',
                                blank=True, null=True)
    promo_code = models.ForeignKey(PromoCodes, verbose_name='Applied Promo code',
                                   on_delete=models.SET_NULL,
                                   blank=True,
                                   null=True,
                                   related_name='promo_code_requested_subscription')
    payment_type = models.CharField(verbose_name='Payment type', max_length=1,
                                    choices=SubscriptionChoices.PAYMENT_TYPE, default='')
    reference_number = models.CharField(verbose_name='Reference number', max_length=255, unique=True)
    status = models.CharField(verbose_name='Status', max_length=1,
                              choices=SubscriptionChoices.SUBSCRIPTION_STATUS,
                              default='P')
    created_date = models.DateTimeField(verbose_name='Order date', editable=False,
                                        auto_now_add=True,
                                        db_index=True)
    updated_date = models.DateTimeField(verbose_name='Updated date', editable=False, auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.auth_shop.shop_name, self.subscription.nbr_article)

    @property
    def generate_pdf(self):
        parent_file_dir = path.abspath(path.join(path.dirname(__file__), ".."))
        # generate pdf
        pdf = FPDF()
        pdf.add_page()
        # pdf.add_font('sysfont', '', r"c:\WINDOWS\Fonts\arial.ttf", uni=True)
        # unicode_font = ImageFont.truetype(parent_file_dir + '/static/fonts/Changa-Regular.ttf', 20)
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(200, 10, txt='Nom boutique : ' + self.auth_shop.shop_name, ln=1, align='L')
        pdf.cell(200, 10, txt='Reference number : ' + self.reference_number, ln=2, align='L')
        base_path = get_facture_path()
        pdf_output_path = "{}{}.{}".format(base_path, uuid4(), 'pdf')
        pdf.output(pdf_output_path)
        return pdf_output_path

    class Meta:
        verbose_name = 'Requested subscription'
        verbose_name_plural = 'Requested subscriptions'
        ordering = ('-pk',)


@receiver(post_save, sender=RequestedSubscriptions)
def send_notification_ws(sender, instance: Union[QuerySet, RequestedSubscriptions], created, raw, using, update_fields,
                         **kwargs):
    if not created and instance.status == 'A':
        try:
            # TODO - missing upgreade case
            # Upgrade subscription case
            SubscribedUsers.objects.get(pk=instance.pk)
            Notifications.objects.create(user=instance.auth_shop.user, type='SA')
            print('SubscribedUsers try created via signal')
        except SubscribedUsers.DoesNotExist:
            print('SubscribedUsers catch created via signal')
            # Manual subscription case
            total_paid = instance.subscription.prix_ttc
            available_slots = instance.subscription.nbr_article
            promo_code_obj = instance.promo_code
            if promo_code_obj:
                if promo_code_obj.promo_code_status == 'E':
                    return
                elif promo_code_obj.type_promo_code == 'S' and promo_code_obj.value is not None:
                    total_paid = 0
                    available_slots = promo_code_obj.value
                elif promo_code_obj.type_promo_code == 'P' and promo_code_obj.value is not None:
                    total_paid = round(total_paid - promo_code_obj.value)
            pdf_output_path = instance.generate_pdf
            subscription_created = SubscribedUsers.objects.create(
                original_request=instance,
                available_slots=available_slots,
                total_paid=total_paid,
                facture=pdf_output_path,
            )
            if subscription_created:
                Notifications.objects.create(user=instance.auth_shop.user, type='SA')
                if promo_code_obj and not promo_code_obj.usage_unique and total_paid == 0:
                    promo_code_obj.promo_code_status = 'E'
                    promo_code_obj.save()


def get_expiration_date():
    return timezone.now() + timedelta(days=365)


class SubscribedUsers(Model):
    original_request = models.OneToOneField(RequestedSubscriptions, verbose_name='Original subscription',
                                            on_delete=models.CASCADE,
                                            related_name='original_request_subscribed_users', unique=True)
    available_slots = models.PositiveIntegerField(verbose_name="Available slots", blank=True, null=True, default=None)
    total_paid = models.PositiveIntegerField(verbose_name="Total paid TTC/ans", blank=True, null=True,
                                             default=None)
    facture = models.FilePathField(verbose_name='Facture', path=get_facture_path(), blank=True, null=True, default=None)
    # by default + 1 year from now
    expiration_date = models.DateTimeField(verbose_name='Expiration date',
                                           default=get_expiration_date)

    def __str__(self):
        return '{} - {}'.format(self.original_request.auth_shop.shop_name, self.expiration_date)

    @property
    def get_absolute_facture_path(self):
        if self.facture:
            return "{0}/{1}".format(API_URL, self.facture)
        return None

    class Meta:
        verbose_name = 'Subscribed user'
        verbose_name_plural = 'Subscribed users'
        ordering = ('-pk',)


class IndexedArticles(Model):
    subscription = models.ForeignKey(SubscribedUsers, on_delete=models.CASCADE,
                                     verbose_name='Subscription',
                                     related_name='subscription_indexed_articles')
    offer = models.OneToOneField(Offers, on_delete=models.CASCADE,
                                 verbose_name='Offer',
                                 related_name='subscription_offer')

    def __str__(self):
        return '{} - {}'.format(self.subscription.pk, self.offer.title)

    class Meta:
        verbose_name = 'Indexed article'
        verbose_name_plural = 'Indexed articles'
        ordering = ('-pk',)
