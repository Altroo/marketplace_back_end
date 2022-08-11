from django.db import models
from django.db.models import Model
from account.models import CustomUser


class Ratings(Model):
    buyer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                              verbose_name='Buyer',
                              related_name='rating_buyer', null=True)
    seller = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                               verbose_name='Seller',
                               related_name='rating_seller', null=True)
    # Needs extra field seller_offer => foreign key to offer.
    # Or using offer in orderDetails model
    rating_note = models.PositiveIntegerField(verbose_name='Rating Note', default=1)
    rating_body = models.CharField(verbose_name='Rating Body', max_length=255,
                                   default=None, null=False, blank=False)
    # Dates
    created_date = models.DateTimeField(verbose_name='Created date',
                                        editable=False, auto_now_add=True,
                                        db_index=True)

    def __str__(self):
        try:
            seller = self.seller.email
        except AttributeError:
            seller = 'ACCOUNT DELETED'
        try:
            buyer = self.buyer.email
        except AttributeError:
            buyer = 'ACCOUNT DELETED'
        return 'Seller : {} - Buyer : {} - {}'.format(seller, buyer, self.rating_note)

    class Meta:
        # unique_together = (('user', 'offer'),)
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'
        ordering = ('-created_date',)
