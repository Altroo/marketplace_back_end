from django.db import models
from django.db.models import Model


class Cities(Model):
    city_en = models.CharField(max_length=255, verbose_name='City EN', blank=True, null=True, default=None)
    city_fr = models.CharField(max_length=255, verbose_name='City FR', blank=True, null=True, default=None)
    city_ar = models.CharField(max_length=255, verbose_name='City AR', blank=True, null=True, default=None)

    def __str__(self):
        return '{} - {} - {}'.format(self.city_en, self.city_fr, self.city_ar)

    class Meta:
        verbose_name = 'City'
        verbose_name_plural = 'Cities'

