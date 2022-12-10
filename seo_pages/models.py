from django.db import models
from typing import Union
from django.db.models import Model, QuerySet
from django.contrib.postgres.fields import ArrayField
from subscription.models import IndexedArticles
from django.db.models.signals import m2m_changed


class DefaultSeoPage(Model):
    page_url = models.SlugField(verbose_name='Page url (unique)', max_length=255, blank=True, null=True,
                                unique=True, default=None)
    title = models.CharField(verbose_name='Title (h1)', max_length=255,
                             blank=True, null=True, default=None)
    tags = ArrayField(models.CharField(verbose_name='Tags', max_length=100, blank=True, null=True, default=None),
                      default=None, size=None, help_text='Separated by comma ","')
    header = models.TextField(verbose_name='Bold Header', default=None, blank=True, null=True)
    paragraphe = models.TextField(verbose_name='Paragraphe', default=None, blank=True, null=True)
    page_meta_description = models.TextField(verbose_name='Meta description', default=None, blank=True, null=True)
    indexed = models.BooleanField(verbose_name='Page indexed ?', default=False)
    articles = models.ManyToManyField(IndexedArticles,
                                      verbose_name='Articles',
                                      related_name='default_seo_page_indexed_articles', blank=True)

    def __str__(self):
        return '{} - {}'.format(self.title, self.page_url)

    class Meta:
        verbose_name = 'Default seo page'
        verbose_name_plural = 'Default seo pages'
        ordering = ('-pk',)


def post_save_default_seo_page_articles(sender, instance: Union[QuerySet, DefaultSeoPage],
                                        action, reverse, *args, **kwargs):
    page_articles = IndexedArticles.objects.all()
    # P = Processing
    # I = Indexed
    # U = Updated
    pk_set: set = kwargs.get('pk_set')
    if action == 'post_add' and not reverse:
        page_articles.filter(pk__in=pk_set).update(status='I')
    elif action == 'post_remove' and not reverse:
        page_articles.filter(pk__in=pk_set).update(status='P')


m2m_changed.connect(post_save_default_seo_page_articles, sender=DefaultSeoPage.articles.through)
