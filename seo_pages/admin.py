from django.contrib import admin
from django.contrib.admin import ModelAdmin
from seo_pages.models import DefaultSeoPage


class DefaultSeoPagesAdmin(ModelAdmin):
    filter_horizontal = ('articles',)
    list_display = ('page_url', 'title', 'tags', 'indexed', 'show_default_seo_articles')
    search_fields = ('pk', 'page_url', 'title', 'tags', 'header', 'paragraphe',
                     'page_meta_description', 'articles__offer__title',
                     'articles__offer__auth_shop__shop_name')
    list_filter = ('indexed', 'articles__status')
    list_editable = ('indexed',)
    ordering = ('-pk',)

    @admin.display(description='Default seo articles')
    def show_default_seo_articles(self, obj):
        return ", ".join([i.offer.title for i in obj.articles.all()])


admin.site.register(DefaultSeoPage, DefaultSeoPagesAdmin)
