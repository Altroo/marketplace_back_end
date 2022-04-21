from django.db import models
from django.db.models import Model
from account.models import CustomUser


class Ratings(Model):
    user_sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                    verbose_name='User sender', related_name='rating_user_sender')
    user_receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                      verbose_name='User receiver', related_name='rating_user_receiver')
    RATING_FOR_CHOICES = (
        ('B', 'Buyer'),
        ('S', 'Seller'),
    )
    rating_for = models.CharField(verbose_name='Rating for', max_length=1,
                                  choices=RATING_FOR_CHOICES)
    rating_note = models.PositiveIntegerField(verbose_name='Rating Note', default=1)
    rating_body = models.CharField(verbose_name='Rating Body', max_length=255, default=None, null=False, blank=False)
    # Dates
    created_date = models.DateTimeField(verbose_name='Created date', editable=False, auto_now_add=True, db_index=True)

    def __str__(self):
        return 'Sender : {} - Recevier : {} - {}'.format(self.user_sender.email, self.user_receiver.email,
                                                         self.rating_note)

    class Meta:
        # unique_together = (('user', 'offer'),)
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'
        ordering = ('-created_date',)
