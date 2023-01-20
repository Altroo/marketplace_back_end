from typing import Union
from decouple import config
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from blog.models import Blog
from Qaryb_API.google_api.google_utils import GoogleUtils
from django.db.models import QuerySet


@admin.action(description='Indéxé les pages selectionnez.')
def call_google_index(modeladmin, request, queryset: Union[QuerySet, Blog]):
    urls = [f"https://qaryb.com/blog/{i.page_url}" for i in queryset]
    urls_to_index = {}
    for url in urls:
        urls_to_index[url] = 'URL_UPDATED'

    google = GoogleUtils()
    google.index_pages(urls_to_index)
    if len(google.responses) > 0:
        for response in google.responses:
            url = response['urlNotificationMetadata']['url']
            indexed_date = response['urlNotificationMetadata']['latestUpdate']['notifyTime']
            page_url = url.split('/')[-1]
            queryset.filter(page_url=page_url).update(indexed_date=indexed_date)
            messages.info(request, f"Page : {page_url} à été indexé avec succès, dernière date : {indexed_date}")
    if len(google.errors) > 0:
        for error in google.errors:
            messages.error(request, error)


class BlogAdmin(ModelAdmin):
    list_display = ('pk', 'get_page_url', 'title', 'indexed', 'indexed_date')
    search_fields = ('pk', 'page_url', 'title', 'tags', 'h_one', 'content',
                     'page_meta_description',)
    list_filter = ('indexed', 'indexed_date')
    list_editable = ('indexed',)
    ordering = ('-pk',)
    date_hierarchy = 'created_date'
    actions = [call_google_index]

    @admin.display(description='Page url')
    def get_page_url(self, obj):
        page_url = obj.page_url
        html = f"<a href='{config('FRONT_DOMAIN')}/blog/{page_url}' target='_blank'>{page_url}</a>"
        return format_html(html)


admin.site.register(Blog, BlogAdmin)
