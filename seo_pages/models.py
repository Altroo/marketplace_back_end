from colorfield.fields import ColorField
from django.db import models
from typing import Union
from django.db.models import Model, QuerySet
from django.contrib.postgres.fields import ArrayField
from subscription.models import IndexedArticles
from django.db.models.signals import m2m_changed
from shop.models import AuthShop


class DefaultSeoPage(Model):
    page_url = models.SlugField(verbose_name='Lien de la page (unique)', max_length=255, blank=True, null=True,
                                unique=True, default=None, help_text='ex : ma-seo-page')
    title = models.CharField(verbose_name='Titre de la page', max_length=255,
                             blank=True, null=True, default=None)
    h_one = models.CharField(verbose_name='H1', max_length=255,
                             blank=True, null=True, default=None)
    tags = ArrayField(models.CharField(verbose_name='Tags', max_length=100,
                                       blank=True, null=True, default=None),
                      default=None, blank=True, null=True, size=None,
                      help_text='ex : Divers,Beauté,Santé & Bien être... (Séparer par une virgule ",".')
    h_two = models.TextField(verbose_name='H2', default=None, blank=True, null=True)
    paragraphe = models.TextField(verbose_name='Paragraphe', default=None, blank=True, null=True)
    page_meta_description = models.TextField(verbose_name='Meta description', default=None, blank=True, null=True)
    indexed = models.BooleanField(verbose_name='Page publier ?', default=True)
    articles = models.ManyToManyField(IndexedArticles,
                                      verbose_name='Articles',
                                      related_name='default_seo_page_indexed_articles', blank=True)

    def __str__(self):
        return '{} - {}'.format(self.title, self.page_url)

    class Meta:
        verbose_name = 'Seo page'
        verbose_name_plural = 'Seo pages'
        ordering = ('-pk',)


class HomePage(Model):
    coup_de_coeur_bg = ColorField(verbose_name='Coup de coeur background color', default='#FFFFFF')
    coup_de_coeur = models.OneToOneField(AuthShop, on_delete=models.CASCADE,
                                         verbose_name='Boutique coup de coeur',
                                         related_name='authShop_coup_de_coeur')
    new_shops = models.ManyToManyField(AuthShop,
                                       verbose_name='New shops list',
                                       related_name='authShop_shops_joint',
                                       blank=True)

    def __str__(self):
        return '{}'.format(self.coup_de_coeur.shop_name)

    class Meta:
        verbose_name = 'Home page'
        verbose_name_plural = 'Home page'
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
