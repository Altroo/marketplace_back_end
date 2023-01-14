from decouple import config
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html

from seo_pages.models import DefaultSeoPage, HomePage


class DefaultSeoPagesAdmin(ModelAdmin):
    filter_horizontal = ('articles',)
    # show_default_seo_articles
    list_display = ('pk', 'get_page_url', 'title', 'indexed')
    search_fields = ('pk', 'page_url', 'title', 'tags', 'h_one', 'h_two', 'paragraphe',
                     'page_meta_description', 'articles__offer__title',
                     'articles__offer__auth_shop__shop_name')
    # exclude = ('tags',)
    list_filter = ('indexed',)
    ordering = ('-pk',)

    # def save_model(self, request, obj, form, change):
    #     tags = []
    #     for article in obj.articles.all():
    #         for tag in article.offer.tags.all():
    #             if tag.name_tag not in tags:
    #                 tags.append(tag.name_tag)
    #     obj.tags = tags
    #     super(DefaultSeoPagesAdmin, self).save_model(request, obj, form, change)

    @admin.display(description='Page url')
    def get_page_url(self, obj):
        page_url = obj.page_url
        html = f"<a href='{config('FRONT_DOMAIN')}/collections/{page_url}' target='_blank'>{page_url}</a>"
        return format_html(html)


class HomePageAdmin(ModelAdmin):
    list_display = ('coup_de_coeur_bg', 'coup_de_coeur', 'show_new_shops')
    search_fields = ('coup_de_coeur__shop_name', 'coup_de_coeur__qaryb_link',
                     'new_shops__shop_name', 'new_shops__qaryb_link')
    ordering = ('-pk',)

    @admin.display(description='New Shops')
    def show_new_shops(self, obj):
        return ", ".join([i.shop_name for i in obj.new_shops.all()])

    def has_add_permission(self, request):
        return not HomePage.objects.exists()


admin.site.register(DefaultSeoPage, DefaultSeoPagesAdmin)
admin.site.register(HomePage, HomePageAdmin)
