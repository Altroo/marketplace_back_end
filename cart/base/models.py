from django.db import models
from django.db.models import Model
from account.models import CustomUser
from offer.base.models import Offers, get_shop_products_path


class Cart(Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                             verbose_name='User', related_name='cart_user')
    offer = models.ForeignKey(Offers, on_delete=models.CASCADE,
                              verbose_name='Offer', related_name='cart_offer')
    # Global
    note = models.CharField(verbose_name='Note', max_length=300, default=None, null=True, blank=True)
    # Product
    picked_color = models.CharField(verbose_name='Picked Color', max_length=255, default=None, null=True, blank=True)
    picked_size = models.CharField(verbose_name='Picked Size', max_length=255, default=None, null=True, blank=True)
    picked_quantity = models.PositiveIntegerField(verbose_name='Quantity', default=1)
    picture_1_thumbnail = models.ImageField(verbose_name='Picture 1 thumbnail', blank=True, null=True,
                                            upload_to=get_shop_products_path, max_length=1000)
    # Service
    picked_date = models.DateField(verbose_name='Picked Date', default=None, null=True, blank=True)
    picked_hour = models.TimeField(verbose_name='Picked Hour', default=None, null=True, blank=True)
    # Added/Updated Dates
    created_date = models.DateTimeField(verbose_name='Created date', editable=False, auto_now_add=True, db_index=True)
    updated_date = models.DateTimeField(verbose_name='Updated date', editable=False, auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.user.email, self.offer.title)

    class Meta:
        unique_together = (('user', 'offer'),)
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        ordering = ('-created_date', '-updated_date')
