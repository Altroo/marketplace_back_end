from typing import Union
from decouple import config
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.db.models import QuerySet
from django.utils.html import format_html
from django.utils import timezone
from seo_pages.models import DefaultSeoPage, HomePage
from Qaryb_API.google_api.google_utils import GoogleUtils


@admin.action(description='Indéxé les pages selectionnez.')
def call_google_index(modeladmin, request, queryset: Union[QuerySet, DefaultSeoPage]):
    urls = [f"https://qaryb.com/collections/{i.page_url}" for i in queryset]
    urls_to_index = {}
    for url in urls:
        urls_to_index[url] = 'URL_UPDATED'

    google = GoogleUtils()
    google.index_pages(urls_to_index)
    if len(google.responses) > 0:
        for response in google.responses:
            url = response['urlNotificationMetadata']['url']
            now = timezone.now()
            page_url = url.split('/')[-1]
            queryset.filter(page_url=page_url).update(indexed_date=now)
            messages.info(request, f"Page : {page_url} à été indexé avec succès, dernière date : {now}")
    if len(google.errors) > 0:
        for error in google.errors:
            messages.error(request, error)


class DefaultSeoPagesAdmin(ModelAdmin):
    # show_default_seo_articles
    list_display = ('pk', 'get_page_url', 'title', 'indexed', 'indexed_date')
    search_fields = ('pk', 'page_url', 'title', 'tags', 'h_one', 'h_two', 'paragraphe',
                     'page_meta_description', 'articles__offer__title',
                     'articles__offer__auth_shop__shop_name')
    list_filter = ('indexed', 'indexed_date')
    readonly_fields = ('indexed_date',)
    ordering = ('-pk',)
    filter_horizontal = ('articles',)
    actions = [call_google_index]

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
