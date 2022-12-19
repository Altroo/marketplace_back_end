from django.db import models
from django.db.models import Model
from account.models import CustomUser
from offers.models import Offers


class Cart(Model):
    unique_id = models.CharField(verbose_name='Cart unique ID',
                                 default=None, null=True, blank=True,
                                 max_length=50)
    offer = models.ForeignKey(Offers, on_delete=models.CASCADE,
                              verbose_name='Offer', related_name='cart_offer')
    picked_color = models.CharField(verbose_name='Picked Color', max_length=255, default=None, null=True, blank=True)
    picked_size = models.CharField(verbose_name='Picked Size', max_length=255, default=None, null=True, blank=True)
    picked_quantity = models.PositiveIntegerField(verbose_name='Quantity', default=None, null=True, blank=True)
    # Service
    picked_date = models.DateField(verbose_name='Picked Date', default=None, null=True, blank=True)
    picked_hour = models.TimeField(verbose_name='Picked Hour', default=None, null=True, blank=True)
    # Added/Updated Dates
    created_date = models.DateTimeField(verbose_name='Created date', editable=False, auto_now_add=True, db_index=True)
    updated_date = models.DateTimeField(verbose_name='Updated date', editable=False, auto_now=True)

    def __str__(self):
        return '{} - {} - {}'.format(self.unique_id, self.offer.auth_shop.shop_name, self.offer.title)

    class Meta:
        unique_together = (('unique_id', 'offer'),)
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        ordering = ('-updated_date', '-created_date')
