from django.contrib import admin
from django.contrib.admin import ModelAdmin
from seo_pages.models import DefaultSeoPage, HomePage


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
